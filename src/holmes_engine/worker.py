from typing import List, Dict, Tuple
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
        # init
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
        self.last_ts_cache = None
        self.tree_dead = []
        # Dynamic but temporary, only live during one event's processing
        # The stack top of `tid_dyn_stack` represents the current dynamic tid of the event being processed.
        # You must reset it after or before one event's processing!!
        self.tid_dyn = None
        # FIX
        self.default_expired = 3
        # dense/sparse mode only
        if not self.rule.sparse:
            # wait_area: TagId indexed array map
            self.wait_area:Dict[str, List] = {}
            # <!>ATTENTION: densed expired_span only for expire&clean! Please use rule.max_span for logic!
            self.expired_span = self.rule.max_span * 3 if self.rule.max_span is not None else self.default_expired
        else:
            self.expired_span = self.rule.max_span

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
            if len(root.children) == 0:
                self.tree_dead.append(root_ind)
        while self.tree_dead != []:
            dead_tree_ind = self.tree_dead.pop()
            del self.ENTRY_POOL[dead_tree_ind]

    def new_event_node(self, raw_event):
        event = Event(
            eid=str(uuid4()),
            raw_event=raw_event,
            tid_dyn=self.tid_dyn,
            kg_inc_map=self.TAG2INC[self.tid_dyn]
        )
        self.EID_MAP[event.eid] = event
        return KGTreeNode(event.eid)

    def new_entry(self, raw_event):
        entry_node = self.new_event_node(raw_event=raw_event)
        entry_node.set_last_ts(ts=raw_event["time"])
        entry_node.set_leaf(entry_node)
        self.ENTRY_POOL.append(entry_node)

    def check_time_order(self, inspector_node:KGTreeNode, inspected_event):
        inspector_event = self.EID_MAP[inspector_node.eid].raw_event
        return inspected_event["time"] >= inspector_event["time"] \
            and inspected_event["time"] - inspector_event["time"] <= self.rule.max_span

    def check_constraint(self, inspector_node:KGTreeNode, inspected_event):
        inspector_event = self.EID_MAP[inspector_node.eid]
        inspector_tid = inspector_event.tid_dyn
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
        ind_y = self.TAGID2IND[tid_y]
        for leaf in root.leaves:
            leaf_seq_ind = self.TAGID2IND[self.EID_MAP[leaf.eid].tid_dyn]
            if ind_y - leaf_seq_ind <= 1: return True
        return False

    def process_dfs(self, entry:KGTreeNode, inspected_event, root:KGTreeNode) -> List[List]:
        # results
        results:List[List] = []
        # checking
        tid_x = self.EID_MAP[entry.eid].tid_dyn
        tid_y = self.tid_dyn
        ind_x = self.TAGID2IND[tid_x]
        ind_y = self.TAGID2IND[tid_y]
        if ind_y - ind_x == 1:
            if self.check_time_order(inspector_node=entry, inspected_event=inspected_event) \
                and self.check_constraint(inspector_node=entry, inspected_event=inspected_event):
                # ALREADY IN POSITION, AND THIS IS THE END OF GAME
                node = self.new_event_node(raw_event=inspected_event)
                entry.add_child(node=node)
                root.set_leaf(leaf=node)
                # UPDATE TIMESTAMP
                self.last_ts_cache = inspected_event["time"]
                # CHECK FINISH
                if tid_y == self.FINAL_TID:
                    return [[self.EID_MAP[entry.eid].raw_event, inspected_event]]
        else:
            assert ind_y > ind_x
            if self.check_constraint(inspector_node=entry, inspected_event=inspected_event):
                for child in entry.children:
                    results_collected = self.process_dfs(entry=child, inspected_event=inspected_event, root=root)
                    if results_collected is not None:
                        for result in results_collected:
                            result.insert(0, self.EID_MAP[entry.eid].raw_event)
                    results += results_collected
        return results

    def process_event(self, event):
        results = []
        tid = event["holmes-tag"]
        if tid not in self.TAGID_SET: return
        for entry in self.ENTRY_POOL:
            for i in range(self.dup_nodes[tid] + 1):
                self.tid_dyn = tid + '@' + str(i) if i != 0 else tid
                if self.tid_dyn == self.ENTRY_TID: continue
                if not self.precheck_has_position(root=entry): continue
                results_collected = self.process_dfs(entry=entry, inspected_event=event, root=entry)
                results += results_collected
            if self.last_ts_cache is not None:
                entry.set_last_ts(ts=self.last_ts_cache)
                self.last_ts_cache = None
        if tid == self.ENTRY_TID:
            self.tid_dyn = tid
            self.new_entry(raw_event=event)
            # return []
        return results
