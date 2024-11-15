package com.amber.holmes;

import java.util.*;

class Worker {
    public HolmesRule rule;
    public String rulename;
    private Map<String, Integer> dup_nodes; // repeated counts for every tid
    private Map<String, Integer> DENSE_SHAPE_IND; // tid_sync → int
    private Map<String, Integer> SLOT_LEN_MAP;
    private Map<String, String> FIND_DENSE_PREV; // tid_sync → prev_tid_sync
    private String ENTRY_TID;
    private String FINAL_TID;
    private List<String> TAGID_SEQ;
    private Set<String> TAGID_SET;
    private Map<String, Integer> TAGID2IND;
    private Map<String, Map<String, List<String>>> TAG2KG;
    private Map<String, Map<String, List<String>>> TAG2INC;
    private Map<String, Map<String, List<String>>> CONJUGATE_MAP;
    private Map<String, Event> EID_MAP; // Dynamic but persistent
    private List<KGTreeNode> ENTRY_POOL; // Dynamic but persistent
    private Long last_ts_cache;
    private List<Integer> tree_dead; // for trash clean
    private Map<KGTreeNode, Map<Integer, List<Event>>> DENSE_CACHE; // {prev: {1: [], 2: [], 3: []}}
    private Set<KGTreeNode> DENSE_LEAVES; // for dense
    private String tidDyn; // Dynamic but temporary
    private int default_expired = 3;
    private int expired_span;
    private int default_dense_expired = 1;

    public Worker(HolmesRule rule, String rulename) {
        this.rule = rule;
        this.rulename = rulename;
        this.dup_nodes = new HashMap<>(); // repeated counts for every tid
        for (TagNode tag_node : rule.tagNodes) {
            if (!dup_nodes.containsKey(tag_node.tagRule.id)) {
                dup_nodes.put(tag_node.tagRule.id, 0);
            } else {
                dup_nodes.put(tag_node.tagRule.id, dup_nodes.get(tag_node.tagRule.id) + 1);
                tag_node.tagRule.id += "@" + dup_nodes.get(tag_node.tagRule.id);
            }
        }
        // init DENSE MAP
        // gen dense_gid → prev_tid_sync firstly
        Integer last_dgid = null;
        String last_tidDyn = null;
        Map<Integer, String> dgid2prev = new HashMap<>();
        this.DENSE_SHAPE_IND = new HashMap<>(); // tid_sync → int
        this.SLOT_LEN_MAP = new HashMap<>();
        int ind = 0;
        if (rule.tagNodes.get(0).denseGid != null) {
            last_dgid = null;
            last_tidDyn = "DENSE_BOOT";
        }
        Integer dense_gid = null;
        for (TagNode tag_node : rule.tagNodes) {
            String tidDyn = tag_node.tagRule.id;
            dense_gid = tag_node.denseGid;
            if (dense_gid != last_dgid) {
                // meet a new block, or out a block
                if (last_dgid != null) {
                    // out a block
                    SLOT_LEN_MAP.put(dgid2prev.get(last_dgid), ind + 1);
                }
                if (dense_gid != null) {
                    // into a new block
                    dgid2prev.put(dense_gid, last_tidDyn);
                    ind = 0;
                    DENSE_SHAPE_IND.put(tidDyn, ind);
                }
                last_dgid = dense_gid;
            } else {
                last_tidDyn = tidDyn;
                if (dense_gid != null) {
                    ind += 1;
                    DENSE_SHAPE_IND.put(tidDyn, ind);
                }
            }
        }
        if (dense_gid != null) {
            SLOT_LEN_MAP.put(dgid2prev.get(dense_gid), ind + 1);
        }
        this.FIND_DENSE_PREV = new HashMap<>(); // tid_sync → prev_tid_sync
        for (TagNode tag_node : rule.tagNodes) {
            if (tag_node.denseGid == null)
                continue;
            FIND_DENSE_PREV.put(tag_node.tagRule.id, dgid2prev.get(tag_node.denseGid));
        }
        // init INC, CONJ and others
        this.ENTRY_TID = this.rule.tagNodes.get(0).tagRule.id;
        this.FINAL_TID = this.rule.tagNodes.get(this.rule.tagNodes.size() - 1).tagRule.id;
        this.TAGID_SEQ = new ArrayList<>();
        for (TagNode tag_node : rule.tagNodes) {
            TAGID_SEQ.add(tag_node.tagRule.id);
        }
        this.TAGID_SET = new HashSet<>(TAGID_SEQ);
        this.TAGID2IND = new HashMap<>();
        for (ind = 0; ind < TAGID_SEQ.size(); ind++) {
            TAGID2IND.put(TAGID_SEQ.get(ind), ind);
        }
        this.TAG2KG = new HashMap<>();
        gen_tag2kg();
        this.TAG2INC = new HashMap<>();
        gen_kg_inc();
        this.CONJUGATE_MAP = new HashMap<>();
        gen_kg_conjugate();
        // Dynamic but persistent
        this.EID_MAP = new HashMap<>();
        this.ENTRY_POOL = new ArrayList<>();
        // for trash clean
        this.last_ts_cache = null;
        this.tree_dead = new ArrayList<>();
        // for dense
        this.DENSE_CACHE = new HashMap<>(); // {prev: {1: [], 2: [], 3: []}}
        this.DENSE_LEAVES = new HashSet<>();
        // Dynamic but temporary, only live during one event's processing
        // The stack top of `tidDyn_stack` represents the current dynamic tid of the
        // event being processed.
        // You must reset it after or before one event's processing!!
        this.tidDyn = null;
        // FIX
        this.default_expired = 3;
        this.expired_span = this.rule.maxSpan;
        this.default_dense_expired = 1;
        // check and init dense boot node
        if (rule.tagNodes.get(0).denseGid != null) {
            this.tidDyn = "DENSE_BOOT";
            new_entry(Collections.singletonMap("time", -1));
        }
    }

    private void gen_tag2kg() {
        for (TagNode tag_node : this.rule.tagNodes) {
            String tag_id = tag_node.tagRule.id;
            this.TAG2KG.put(tag_id, new HashMap<>());
            for (KeyGroupBind kg_bind : tag_node.binders) {
                this.TAG2KG.get(tag_id).put(kg_bind.groupId, kg_bind.fields);
            }
        }
    }

    private void gen_kg_inc() {
        Set<String> cache = new HashSet<>();
        for (String tid : this.TAGID_SEQ) {
            Set<String> gids = new HashSet<>(this.TAG2KG.get(tid).keySet());
            Set<String> new_gids = new HashSet<>(gids);
            new_gids.removeAll(cache);
            cache.addAll(gids);
            Map<String, List<String>> kg_inc = new HashMap<>();
            for (String gid : new_gids) {
                kg_inc.put(gid, this.TAG2KG.get(tid).get(gid));
            }
            this.TAG2INC.put(tid, kg_inc);
        }
    }

    private void gen_kg_conjugate() {
        for (int ind = 0; ind < TAGID_SEQ.size(); ind++) {
            String tid_y = TAGID_SEQ.get(ind);
            this.CONJUGATE_MAP.put(tid_y, new HashMap<>());
            for (String tid_x : TAGID_SEQ.subList(0, ind)) {
                HashSet<String> intersection = new HashSet<>(this.TAG2KG.get(tid_y).keySet());
                intersection.retainAll(this.TAG2INC.get(tid_x).keySet());
                this.CONJUGATE_MAP.get(tid_y).put(tid_x, new ArrayList<String>(intersection));
            }
        }
    }

    private void prune_algorithm(KGTreeNode entry, List<KGTreeNode> dead_leaves) {
        for (KGTreeNode dead_leaf : dead_leaves) {
            entry.leaves.remove(dead_leaf);
            KGTreeNode dead_node = dead_leaf;
            while (dead_node.children.isEmpty()) {
                if (dead_node.parent == null) {
                    if (!this.EID_MAP.get(dead_node.eid).tidDyn.equals("DENSE_BOOT")) {
                        this.EID_MAP.remove(dead_node.eid);
                    }
                    break;
                }
                KGTreeNode p = dead_node.parent;
                dead_node.kill();
                this.EID_MAP.remove(dead_node.eid);
                dead_node = p;
            }
        }
    }

    private boolean is_dead_leaf(KGTreeNode leaf, long event_time) {
        if (event_time - (long) (Integer) this.EID_MAP.get(leaf.eid).rawEvent.get("time") > this.expired_span) {
            return true;
        }
        return false;
    }

    public void prune(long event_time) {
        for (int root_ind = 0; root_ind < this.ENTRY_POOL.size(); root_ind++) {
            KGTreeNode root = this.ENTRY_POOL.get(root_ind);
            List<KGTreeNode> dead_leaves = new ArrayList<>();
            for (KGTreeNode leaf : root.leaves) {
                if (is_dead_leaf(leaf, event_time)) {
                    dead_leaves.add(leaf);
                }
            }
            if (dead_leaves.isEmpty()) {
                continue;
            }
            prune_algorithm(root, dead_leaves);
            if (root.children.isEmpty() && this.EID_MAP.containsKey(root.eid)) {
                assert this.EID_MAP.get(root.eid).tidDyn.equals("DENSE_BOOT");
            }
            if (root.children.isEmpty() && !this.EID_MAP.containsKey(root.eid)) {
                this.tree_dead.add(root_ind);
            }
        }
        while (!this.tree_dead.isEmpty()) {
            int dead_tree_ind = this.tree_dead.remove(this.tree_dead.size() - 1);
            this.ENTRY_POOL.remove(dead_tree_ind);
        }
    }

    private Event new_event(Map<String, Object> raw_event) {
        return new Event(
                UUID.randomUUID().toString(),
                raw_event,
                this.tidDyn,
                this.tidDyn.equals("DENSE_BOOT") ? null : this.TAG2INC.get(this.tidDyn));
    }

    private KGTreeNode new_event_node(Event event) {
        this.EID_MAP.put(event.eid, event);
        return new KGTreeNode(event.eid);
    }

    private void new_entry(Map<String, Object> raw_event) {
        KGTreeNode entry_node = new_event_node(new_event(raw_event));
        entry_node.setLastTs((long) (Integer) raw_event.get("time"));
        entry_node.setLeaf(entry_node);
        this.ENTRY_POOL.add(entry_node);
    }

    private boolean check_time_order(KGTreeNode inspector_node, Map<String, Object> inspected_event) {
        if (this.EID_MAP.get(inspector_node.eid).tidDyn.equals("DENSE_BOOT"))
            return true;
        Map<String, Object> inspector_event = this.EID_MAP.get(inspector_node.eid).rawEvent;
        return (long) (Integer) inspected_event.get("time") >= (long) (Integer) inspector_event.get("time") &&
                (long) (Integer) inspected_event.get("time")
                        - (long) (Integer) inspector_event.get("time") <= this.rule.maxSpan;
    }

    private boolean check_constraint(KGTreeNode inspector_node, Map<String, Object> inspected_event) {
        Event inspector_event = this.EID_MAP.get(inspector_node.eid);
        String inspector_tid = inspector_event.tidDyn;
        if (inspector_tid.equals("DENSE_BOOT"))
            return true;
        String inspected_tid = this.tidDyn;
        for (String constraint_group_id : this.CONJUGATE_MAP.get(inspected_tid).get(inspector_tid)) {
            assert this.TAG2KG.get(inspected_tid).containsKey(constraint_group_id);
            Object[] _prev_constraint = (Object[]) inspector_event.kgInc.get(constraint_group_id);
            String[] prev_constraint = Arrays.stream(_prev_constraint).map(v -> v.toString()).toArray(String[]::new);
            String[] fields = Arrays
                    .stream((Object[]) this.TAG2KG.get(inspected_tid).get(constraint_group_id).toArray())
                    .map(v -> v.toString()).toArray(String[]::new);
            String[] fields_values = Arrays.stream(fields).map(name -> inspected_event.get(name).toString())
                    .toArray(String[]::new);
            if (!Arrays.equals(prev_constraint, fields_values))
                return false;
        }
        return true;
    }

    private boolean precheck_has_position(KGTreeNode root) {
        String tid_y = this.tidDyn;
        // skip dense node
        if (this.FIND_DENSE_PREV.containsKey(tid_y))
            return true;
        // checking
        int ind_y = this.TAGID2IND.get(tid_y);
        for (KGTreeNode leaf : root.leaves) {
            if (this.EID_MAP.get(leaf.eid).tidDyn.equals("DENSE_BOOT"))
                continue;
            int leaf_seq_ind = this.TAGID2IND.get(this.EID_MAP.get(leaf.eid).tidDyn);
            if (ind_y - leaf_seq_ind <= 1)
                return true;
        }
        return false;
    }

    private KGTreeNode join_new_leaf(KGTreeNode entry, Object inspected_event, KGTreeNode root) {
        KGTreeNode node;
        if (!(inspected_event instanceof Event)) {
            node = new_event_node(new_event((Map<String, Object>) inspected_event));
        } else {
            node = new_event_node((Event) inspected_event);
        }
        entry.addChild(node);
        root.setLeaf(node);
        // UPDATE TIMESTAMP
        this.last_ts_cache = (inspected_event instanceof Event)
                ? (long) (Integer) ((Event) inspected_event).rawEvent.get("time")
                : (long) (Integer) ((Map<String, Object>) inspected_event).get("time");
        return node;
    }

    private List<KGTreeNode> liquidate_dense(long time, KGTreeNode root) {
        List<KGTreeNode> done = new ArrayList<>();
        List<KGTreeNode> results = new ArrayList<>();
        // processing
        for (Map.Entry<KGTreeNode, Map<Integer, List<Event>>> entry : DENSE_CACHE.entrySet()) {
            KGTreeNode prev = entry.getKey();
            for (Map.Entry<Integer, List<Event>> slotEntry : entry.getValue().entrySet()) {
                for (Event event : slotEntry.getValue()) {
                    if (time - (long) event.rawEvent.get("time") >= default_dense_expired) { // if need to handle a slot
                        boolean is_all_here = true;
                        for (int i = 0; i < SLOT_LEN_MAP.get(this.EID_MAP.get(prev.eid).tidDyn); i++) {
                            if (!entry.getValue().containsKey(i)) {
                                is_all_here = false;
                                break;
                            }
                        }
                        done.add(prev);
                        if (!is_all_here)
                            continue;
                        List<KGTreeNode> head_nodes = new ArrayList<>();
                        for (Event head_event : DENSE_CACHE.get(prev).get(0)) {
                            head_nodes.add(join_new_leaf(prev, head_event, root));
                        }
                        String tidDyn_save = this.tidDyn;
                        for (KGTreeNode head_n : head_nodes) {
                            this.DENSE_LEAVES.add(head_n);
                            for (int slot_ind = 1; slot_ind < SLOT_LEN_MAP
                                    .get(this.EID_MAP.get(prev.eid).tidDyn); slot_ind++) {
                                for (Event eventInSlot : DENSE_CACHE.get(prev).get(slot_ind)) {
                                    this.tidDyn = eventInSlot.tidDyn;
                                    List<KGTreeNode> results_collected = process_dfs(head_n, eventInSlot.rawEvent, root,
                                            true);
                                    results.addAll(results_collected);
                                }
                            }
                        }
                        this.tidDyn = tidDyn_save;
                    }
                    break;
                }
                break;
            }
        }
        // clean dyn cache
        for (KGTreeNode prev : done) {
            DENSE_CACHE.remove(prev);
        }
        // clean useless nodes
        List<KGTreeNode> dead_leaves = new ArrayList<>();
        for (KGTreeNode leaf : DENSE_LEAVES) {
            String leaf_tidDyn = this.EID_MAP.get(leaf.eid).tidDyn;
            String leaf_prev_tidDyn = this.FIND_DENSE_PREV.get(leaf_tidDyn);
            if (this.DENSE_SHAPE_IND.get(leaf_tidDyn) != this.SLOT_LEN_MAP.get(leaf_prev_tidDyn) - 1) {
                dead_leaves.add(leaf);
            }
        }
        prune_algorithm(root, dead_leaves);
        this.DENSE_LEAVES.clear();
        return results;
    }

    private List<KGTreeNode> process_dfs(KGTreeNode entry, Map<String, Object> inspected_event, KGTreeNode root,
            boolean liquidate) {
        List<KGTreeNode> results = new ArrayList<>();
        // checking
        String tid_x = this.EID_MAP.get(entry.eid).tidDyn;
        String tid_y = this.tidDyn;
        int ind_x = tid_x.equals("DENSE_BOOT") ? -1 : this.TAGID2IND.get(tid_x);
        int ind_y = this.TAGID2IND.get(tid_y);
        if (ind_y - ind_x == 1 && (!this.FIND_DENSE_PREV.containsKey(tid_y) || liquidate)) {
            if (check_time_order(entry, inspected_event) && check_constraint(entry, inspected_event)) {
                // ALREADY IN POSITION, AND THIS IS THE END OF GAME
                KGTreeNode node = join_new_leaf(entry, inspected_event, root);
                if (liquidate) {
                    if (node.parent != null && this.DENSE_LEAVES.contains(node.parent)) {
                        this.DENSE_LEAVES.remove(node.parent);
                    }
                    this.DENSE_LEAVES.add(node);
                }
                // CHECK FINISH
                if (tid_y.equals(this.FINAL_TID)) {
                    results.add(node);
                }
            }
        } else {
            assert ind_y > ind_x;
            if (check_constraint(entry, inspected_event)) {
                // check if meets the dense terminal condition
                if (!liquidate && this.FIND_DENSE_PREV.containsKey(this.tidDyn) &&
                        this.FIND_DENSE_PREV.get(this.tidDyn).equals(tid_x) &&
                        check_time_order(entry, inspected_event)) {
                    if (!DENSE_CACHE.containsKey(entry)) {
                        DENSE_CACHE.put(entry, new HashMap<>());
                    }
                    if (!DENSE_CACHE.get(entry).containsKey(this.DENSE_SHAPE_IND.get(this.tidDyn))) {
                        DENSE_CACHE.get(entry).put(this.DENSE_SHAPE_IND.get(this.tidDyn), new ArrayList<>());
                    }
                    DENSE_CACHE.get(entry).get(this.DENSE_SHAPE_IND.get(this.tidDyn)).add(new_event(inspected_event));
                    return results;
                }
                // continue checking
                for (KGTreeNode child : entry.children) {
                    List<KGTreeNode> results_collected = process_dfs(child, inspected_event, root, false);
                    results.addAll(results_collected);
                }
            }
        }
        return results;
    }

    private List<Object> fetch_results(KGTreeNode leaf) {
        KGTreeNode ptr = leaf;
        List<Object> chain = new ArrayList<>();
        while (ptr != null) {
            if (this.EID_MAP.get(ptr.eid).tidDyn.equals("DENSE_BOOT"))
                break;
            chain.add(0, this.EID_MAP.get(ptr.eid).rawEvent);
            ptr = ptr.parent;
        }
        return chain;
    }

    private boolean is_start_event(String tid) {
        return tid.equals(this.ENTRY_TID) && !this.FIND_DENSE_PREV.containsKey(tid);
    }

    public List<List<Object>> processEvent(Map<String, Object> event) {
        List<List<Object>> results = new ArrayList<>();
        String tid = (String) event.get("holmes-tag");
        if (!this.TAGID_SET.contains(tid))
            return results;
        for (KGTreeNode entry : this.ENTRY_POOL) {
            for (int i = 0; i <= this.dup_nodes.get(tid); i++) {
                this.tidDyn = (i != 0) ? tid + "@" + i : tid;
                if (is_start_event(this.tidDyn))
                    continue;
                if (!precheck_has_position(entry))
                    continue;
                List<KGTreeNode> terminal_leaves = new ArrayList<>();
                terminal_leaves.addAll(liquidate_dense((long) (Integer) event.get("time"), entry));
                terminal_leaves.addAll(process_dfs(entry, event, entry, false));
                for (KGTreeNode leaf : terminal_leaves) {
                    List<Object> results_collected = fetch_results(leaf);
                    results.add(results_collected);
                }
            }
            if (this.last_ts_cache != null) {
                entry.setLastTs(this.last_ts_cache);
                this.last_ts_cache = null;
            }
        }
        if (is_start_event(tid)) {
            this.tidDyn = tid;
            new_entry(event);
        }
        return results;
    }
}
