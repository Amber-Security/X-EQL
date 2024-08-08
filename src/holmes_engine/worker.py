from typing import List, Dict, Tuple, Set
from uuid import uuid4

from holmes_rule.rule import HolmesRule
from .event import Event
from .kgtree import KGTreeNode


class Worker:
    def __init__(self, rule:HolmesRule, rulename:str) -> None:
        self.rule:HolmesRule = rule
        self.rulename:str = rulename
        # handle tid repeated situation before initing
        self.dup_nodes = {}  # repeated counts for every tid
        for tag_node in rule.tag_nodes:
            if tag_node.tag_rule.id not in self.dup_nodes:
                self.dup_nodes[tag_node.tag_rule.id] = 0
            else:
                self.dup_nodes[tag_node.tag_rule.id] += 1
                tag_node.tag_rule.id += '@' + str(self.dup_nodes[tag_node.tag_rule.id])
        # init DENSE MAP
        # gen dense_gid → prev_tid_sync firstly
        last_dgid = None
        last_tid_dyn = None
        dgid2prev = {}
        self.DENSE_SHAPE_IND = {}  # tid_sync → int
        self.SLOT_LEN_MAP = {}
        ind = 0
        if rule.tag_nodes[0].dense_gid is not None:
            last_dgid = None
            last_tid_dyn = "DENSE_BOOT"
        for tag_node in rule.tag_nodes:
            tid_dyn = tag_node.tag_rule.id
            dense_gid = tag_node.dense_gid
            if dense_gid != last_dgid:
                # meet a new block, or out a block
                if last_dgid is not None:
                    # out a block
                    self.SLOT_LEN_MAP[dgid2prev[last_dgid]] = ind + 1
                if dense_gid is not None:
                    # into a new block
                    dgid2prev[dense_gid] = last_tid_dyn
                    ind = 0
                    self.DENSE_SHAPE_IND[tid_dyn] = ind
                last_dgid = dense_gid
            else:
                last_tid_dyn = tid_dyn
                if dense_gid is not None:
                    ind += 1
                    self.DENSE_SHAPE_IND[tid_dyn] = ind
        if dense_gid is not None:
            self.SLOT_LEN_MAP[dgid2prev[dense_gid]] = ind + 1
        self.FIND_DENSE_PREV = {}  # tid_sync → prev_tid_sync
        for tag_node in rule.tag_nodes:
            if tag_node.dense_gid is None: continue
            self.FIND_DENSE_PREV[tag_node.tag_rule.id] = dgid2prev[tag_node.dense_gid]
        # init INC, CONJ and others
        self.ENTRY_TID = self.rule.tag_nodes[0].tag_rule.id
        self.FINAL_TID = self.rule.tag_nodes[-1].tag_rule.id
        self.TAGID_SEQ = [tag_node.tag_rule.id for tag_node in rule.tag_nodes]
        self.TAGID_SET = set(self.TAGID_SEQ)
        self.TAGID2IND = {}
        for ind, tid in enumerate(self.TAGID_SEQ):
            self.TAGID2IND[tid] = ind
        self.TAG2KG:Dict[str, Dict[str, Tuple[str]]] = {}
        self.gen_tag2kg()
        self.TAG2INC:Dict[str, Dict[str, Tuple[str]]] = {}
        self.gen_kg_inc()
        self.CONJUGATE_MAP = {}
        self.gen_kg_conjugate()
        # Dynamic but persistent
        self.EID_MAP:Dict[str, Event] = {}
        self.ENTRY_POOL:List[KGTreeNode] = []
        #   for trash clean
        self.last_ts_cache = None
        self.tree_dead = []
        #   for dense
        self.DENSE_CACHE:Dict[KGTreeNode, Dict[int, List[Event]]] = {} # {prev: {1: [], 2: [], 3: []}}
        self.DENSE_LEAVES:Set[KGTreeNode] = set()
        # Dynamic but temporary, only live during one event's processing
        #   The stack top of `tid_dyn_stack` represents the current dynamic tid of the event being processed.
        #   You must reset it after or before one event's processing!!
        self.tid_dyn = None
        # FIX
        self.default_expired = 3
        self.expired_span = self.rule.max_span
        self.default_dense_expired = 1
        # check and init dense boot node
        if rule.tag_nodes[0].dense_gid is not None:
            self.tid_dyn = "DENSE_BOOT"
            self.new_entry(raw_event={"time": -1})

    def gen_tag2kg(self):
        for tag_node in self.rule.tag_nodes:
            tag_id = tag_node.tag_rule.id
            self.TAG2KG[tag_id] = {}
            for kg_bind in tag_node.binders:
                self.TAG2KG[tag_id][kg_bind.group_id] = kg_bind.fields

    def gen_kg_inc(self):
        cache = set()
        for tid in self.TAGID_SEQ:
            gids = set(self.TAG2KG[tid].keys())
            new_gids = gids - cache
            cache |= gids
            kg_inc = {}
            for gid in new_gids:
                kg_inc[gid] = self.TAG2KG[tid][gid]
            self.TAG2INC[tid] = kg_inc

    def gen_kg_conjugate(self):
        for ind, tid_y in enumerate(self.TAGID_SEQ):
            self.CONJUGATE_MAP[tid_y] = {}
            for tid_x in self.TAGID_SEQ[:ind]:
                self.CONJUGATE_MAP[tid_y][tid_x] = list(
                    set(self.TAG2KG[tid_y].keys()) & set(self.TAG2INC[tid_x].keys())
                )

    def prune_algorithm(self, entry:KGTreeNode, dead_leaves:List[KGTreeNode]):
        for dead_leaf in dead_leaves:
            entry.leaves.remove(dead_leaf)
            dead_node = dead_leaf
            while len(dead_node.children) == 0:
                if dead_node.parent is None:
                    del self.EID_MAP[dead_node.eid]
                    break
                p = dead_node.parent
                dead_node.kill()
                del self.EID_MAP[dead_node.eid]
                dead_node = p

    def is_dead_leaf(self, leaf:KGTreeNode, event_time):
        # the first situation only get itself death, be carefull when we reconstruct it next time.
        # if self.EID_MAP[leaf.eid].raw_event["holmes-tag"] == self.FINAL_TID:
        #     return True
        if event_time - self.EID_MAP[leaf.eid].raw_event["time"] > self.expired_span:
            return True
        return False

    def prune(self, event_time):
        for root_ind, root in enumerate(self.ENTRY_POOL):
            dead_leaves = [leaf for leaf in root.leaves if self.is_dead_leaf(leaf=leaf, event_time=event_time)]
            if dead_leaves == []:
                continue
            self.prune_algorithm(entry=root, dead_leaves=dead_leaves)
            if root.eid in self.EID_MAP: assert self.EID_MAP[root.eid].tid_dyn == "DENSE_BOOT"
            if len(root.children) == 0 and root.eid not in self.EID_MAP:
                self.tree_dead.append(root_ind)
        while self.tree_dead != []:
            dead_tree_ind = self.tree_dead.pop()
            del self.ENTRY_POOL[dead_tree_ind]

    def new_event(self, raw_event):
        # reference to raw event
        return Event(
            eid=str(uuid4()),
            raw_event=raw_event,
            tid_dyn=self.tid_dyn,
            kg_inc_map=self.TAG2INC[self.tid_dyn] if self.tid_dyn != "DENSE_BOOT" else None
        )

    def new_event_node(self, event:Event):
        self.EID_MAP[event.eid] = event
        return KGTreeNode(event.eid)

    def new_entry(self, raw_event):
        entry_node = self.new_event_node(event=self.new_event(raw_event))
        entry_node.set_last_ts(ts=raw_event["time"])
        entry_node.set_leaf(entry_node)
        self.ENTRY_POOL.append(entry_node)

    def check_time_order(self, inspector_node:KGTreeNode, inspected_event):
        if self.EID_MAP[inspector_node.eid].tid_dyn == "DENSE_BOOT": return True
        inspector_event = self.EID_MAP[inspector_node.eid].raw_event
        return inspected_event["time"] >= inspector_event["time"] \
            and inspected_event["time"] - inspector_event["time"] <= self.rule.max_span

    def check_constraint(self, inspector_node:KGTreeNode, inspected_event):
        inspector_event = self.EID_MAP[inspector_node.eid]
        inspector_tid = inspector_event.tid_dyn
        if inspector_tid == "DENSE_BOOT": return True
        inspected_tid = self.tid_dyn
        for constraint_group_id in self.CONJUGATE_MAP[inspected_tid][inspector_tid]:
            assert constraint_group_id in self.TAG2KG[inspected_tid]
            prev_constraint = inspector_event.kg_inc[constraint_group_id]
            fields = self.TAG2KG[inspected_tid][constraint_group_id]
            fields_values = tuple([inspected_event[name] for name in fields])
            if prev_constraint != fields_values: return False
        return True

    def precheck_has_position(self, root:KGTreeNode):
        tid_y = self.tid_dyn
        # skip dense node
        if tid_y in self.FIND_DENSE_PREV: return True
        # checking
        ind_y = self.TAGID2IND[tid_y]
        for leaf in root.leaves:
            if self.EID_MAP[leaf.eid].tid_dyn == "DENSE_BOOT": continue
            leaf_seq_ind = self.TAGID2IND[self.EID_MAP[leaf.eid].tid_dyn]
            if ind_y - leaf_seq_ind <= 1: return True
        return False

    def join_new_leaf(self, entry:KGTreeNode, inspected_event:Dict|Event, root:KGTreeNode) -> KGTreeNode:
        if not isinstance(inspected_event, Event):
            node = self.new_event_node(event=self.new_event(inspected_event))
        else:
            node = self.new_event_node(event=inspected_event)
        entry.add_child(node=node)
        root.set_leaf(leaf=node)
        # UPDATE TIMESTAMP
        self.last_ts_cache = inspected_event.raw_event["time"] if isinstance(inspected_event, Event) else inspected_event["time"]
        return node

    def liquidate_dense(self, time, root:KGTreeNode):
        def checkout(time):
            # easy, easy...don't be shocked by the loops here.
            # it's just a easy checkout. look at the `break` :)
            for prev in self.DENSE_CACHE:
                for slot_ind in self.DENSE_CACHE[prev]:
                    for event in self.DENSE_CACHE[prev][slot_ind]:
                        if time - event.raw_event["time"] >= self.default_dense_expired:  # if need to handler a slot
                            is_all_here = True
                            for i in range(self.SLOT_LEN_MAP[self.EID_MAP[prev.eid].tid_dyn]):
                                if i not in self.DENSE_CACHE[prev]:
                                    is_all_here = False
                                    break
                            yield prev, is_all_here
                        break
                    break
        done = []
        results = []
        # processing
        for prev, is_all_here in checkout(time=time):
            done.append(prev)
            if not is_all_here: continue
            head_nodes = [self.join_new_leaf(entry=prev, inspected_event=head_event, root=root) for head_event in self.DENSE_CACHE[prev][0]]
            tid_dyn_save = self.tid_dyn
            for head_n in head_nodes:
                self.DENSE_LEAVES.add(head_n)
                for slot_ind in range(1, self.SLOT_LEN_MAP[self.EID_MAP[prev.eid].tid_dyn]):
                    for event in self.DENSE_CACHE[prev][slot_ind]:
                        self.tid_dyn = event.tid_dyn
                        results_collected = self.process_dfs(entry=head_n, inspected_event=event.raw_event, root=root, liquidate=True)
                        results += results_collected
            self.tid_dyn = tid_dyn_save
        # clean dyn cache
        for prev in done: del self.DENSE_CACHE[prev]
        # clean useless nodes
        dead_leaves = []
        for leaf in self.DENSE_LEAVES:
            leaf_tid_dyn = self.EID_MAP[leaf.eid].tid_dyn
            leaf_prev_tid_dyn = self.FIND_DENSE_PREV[leaf_tid_dyn]
            if self.DENSE_SHAPE_IND[leaf_tid_dyn] != self.SLOT_LEN_MAP[leaf_prev_tid_dyn] - 1:
                dead_leaves.append(leaf)
        self.prune_algorithm(entry=root, dead_leaves=dead_leaves)
        self.DENSE_LEAVES = set()
        return results

    def process_dfs(self, entry:KGTreeNode, inspected_event, root:KGTreeNode, liquidate=False) -> List[KGTreeNode]:
        # results
        results:List[KGTreeNode] = []
        # checking
        tid_x = self.EID_MAP[entry.eid].tid_dyn
        tid_y = self.tid_dyn
        ind_x = self.TAGID2IND[tid_x] if tid_x != "DENSE_BOOT" else -1
        ind_y = self.TAGID2IND[tid_y]
        if ind_y - ind_x == 1 and (tid_y not in self.FIND_DENSE_PREV or liquidate):
            if self.check_time_order(inspector_node=entry, inspected_event=inspected_event) \
                and self.check_constraint(inspector_node=entry, inspected_event=inspected_event):
                # ALREADY IN POSITION, AND THIS IS THE END OF GAME
                node = self.join_new_leaf(entry=entry, inspected_event=inspected_event, root=root)
                if liquidate:
                    if node.parent in self.DENSE_LEAVES: self.DENSE_LEAVES.remove(node.parent)
                    self.DENSE_LEAVES.add(node)
                # CHECK FINISH
                if tid_y == self.FINAL_TID:
                    return [node]
        else:
            assert ind_y > ind_x
            if self.check_constraint(inspector_node=entry, inspected_event=inspected_event):
                # check if meets the dense termial condition
                if not liquidate and self.tid_dyn in self.FIND_DENSE_PREV \
                      and self.FIND_DENSE_PREV[self.tid_dyn] == tid_x \
                         and self.check_time_order(inspector_node=entry, inspected_event=inspected_event):
                    if entry not in self.DENSE_CACHE: self.DENSE_CACHE[entry] = {}
                    if self.DENSE_SHAPE_IND[self.tid_dyn] not in self.DENSE_CACHE[entry]:
                        self.DENSE_CACHE[entry][self.DENSE_SHAPE_IND[self.tid_dyn]] = []
                    self.DENSE_CACHE[entry][self.DENSE_SHAPE_IND[self.tid_dyn]].append(self.new_event(inspected_event))
                    return results
                # continue checking
                for child in entry.children:
                    results_collected = self.process_dfs(entry=child, inspected_event=inspected_event, root=root)
                    results += results_collected
        return results

    def fetch_results(self, leaf:KGTreeNode):
        ptr = leaf
        chain = []
        while ptr is not None:
            if self.EID_MAP[ptr.eid].tid_dyn == "DENSE_BOOT": break
            chain.insert(0, self.EID_MAP[ptr.eid].raw_event)
            ptr = ptr.parent
        return chain

    def is_start_event(self, tid):
        return tid == self.ENTRY_TID and tid not in self.FIND_DENSE_PREV

    def process_event(self, event):
        results = []
        tid = event["holmes-tag"]
        if tid not in self.TAGID_SET: return
        for entry in self.ENTRY_POOL:
            for i in range(self.dup_nodes[tid] + 1):
                self.tid_dyn = tid + '@' + str(i) if i != 0 else tid
                if self.is_start_event(tid=self.tid_dyn): continue
                if not self.precheck_has_position(root=entry): continue
                terminal_leaves = []
                terminal_leaves += self.liquidate_dense(event["time"], root=entry)
                terminal_leaves += self.process_dfs(entry=entry, inspected_event=event, root=entry)
                for leaf in terminal_leaves:
                    results_collected = self.fetch_results(leaf=leaf)
                    results.append(results_collected)
            if self.last_ts_cache is not None:
                entry.set_last_ts(ts=self.last_ts_cache)
                self.last_ts_cache = None
        if self.is_start_event(tid=tid):
            self.tid_dyn = tid
            self.new_entry(raw_event=event)
            # return []
        return results
