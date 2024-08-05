from typing import List


class KeyGroupBind:
    def __init__(self, group_id:str, fields:List[str]):
        self.group_id = group_id
        self.fields = fields


class TagRule:
    def __init__(self, id):
        # self.root = root
        self.id = id


class TagNode:
    def __init__(self, tag_rule:TagRule, binders:List[KeyGroupBind], dense_gid:int=None):
        self.tag_rule:TagRule = tag_rule
        self.dense_gid:int = dense_gid
        self.binders:List[KeyGroupBind] = binders


class HolmesRule:
    def __init__(self, ruleid, shape, tag_nodes, max_span=-1):
        self.ruleid:str = ruleid
        self.shape:str = shape
        self.tag_nodes:List[TagNode] = tag_nodes
        self.max_span:int = max_span


def gen_tag_node(event_rule, common_binder, dense_gid=None) -> TagNode:
    tid = event_rule[1]
    tagrule = TagRule(tid)
    binders = [KeyGroupBind(gid, fields) for gid, fields in event_rule[2]] if len(event_rule) == 3 else []
    binders = common_binder + binders
    return TagNode(tag_rule=tagrule, binders=binders, dense_gid=dense_gid)


def load_rule(ast):
    _, head, seq = ast
    # parse head
    if len(head) == 4:
        _, rule_id, shape, _commonk = head
        commonk = _commonk[1]
        common_binder = [KeyGroupBind("*", commonk)]
    else:
        _, rule_id, shape = head
        common_binder = []
    # parse seq
    tag_nodes = []
    dense_gid = 0
    for block in seq:
        if isinstance(block[0], str):
            tag_nodes.append(gen_tag_node(event_rule=block, common_binder=common_binder))
        else:
            tag_nodes += [gen_tag_node(event_rule=event_rule, common_binder=common_binder, dense_gid=dense_gid) for event_rule in block]
            dense_gid += 1
    rule = HolmesRule(
        ruleid=rule_id,
        shape=shape,
        tag_nodes=tag_nodes,
        max_span=60
    )
    return rule


if __name__ == "__main__":
    pass
