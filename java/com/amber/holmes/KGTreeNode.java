package com.amber.holmes;

import java.util.HashSet;
import java.util.Set;

class KGTreeNode {
    public String eid;
    public Set<KGTreeNode> children;
    public KGTreeNode parent;
    public long lastTs;
    public Set<KGTreeNode> leaves;

    public KGTreeNode(String eid) {
        this.eid = eid;
        this.children = new HashSet<>();
        this.parent = null;
        this.lastTs = -1;
        this.leaves = new HashSet<>();
    }

    public void kill() {
        assert children.isEmpty();
        if (parent != null) {
            parent.children.remove(this);
            parent = null;
        }
    }

    public void setLastTs(long ts) {
        if (lastTs < ts) {
            lastTs = ts;
        }
    }

    public void setLeaf(KGTreeNode leaf) {
        leaves.add(leaf);
        if (leaves.contains(leaf.parent)) {
            leaves.remove(leaf.parent);
        }
    }

    public void addChild(KGTreeNode node) {
        children.add(node);
        node.setParent(this);
    }

    public void setParent(KGTreeNode node) {
        parent = node;
    }
}
