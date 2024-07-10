from typing import Set


class KGTreeNode:
    def __init__(self, eid):
        self.eid = eid
        self.children:Set[KGTreeNode] = set()
        self.parent:KGTreeNode = None
        self.last_ts = -1
        self.leaves:Set[KGTreeNode] = set()
    
    def kill(self):
        assert len(self.children) == 0
        if self.parent is not None:
            self.parent.children.remove(self)
            self.parent = None

    def set_last_ts(self, ts):
        if self.last_ts < ts:
            self.last_ts = ts

    def set_leaf(self, leaf):
        leaf:KGTreeNode = leaf
        self.leaves.add(leaf)
        if leaf.parent in self.leaves:
            self.leaves.remove(leaf.parent)

    def add_child(self, node):
        self.children.add(node)
        node.set_parent(node=self)

    def set_parent(self, node):
        self.parent= node
