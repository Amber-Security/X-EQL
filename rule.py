
from typing import List
from xeql_yacc import gen_parser


class KeyGroupBind:
    def __init__(self, group_id:str, fields:List[str]):
        self.group_id = group_id
        self.fields = fields


class TagRule:
    def __init__(self, id):
        # self.root = root
        self.id = id


class TagNode:
    def __init__(self, tag_rule:TagRule, binders:List[KeyGroupBind]):
        self.tag_rule:TagRule = tag_rule
        self.binders:List[KeyGroupBind] = binders


class EQLRule:
    def __init__(self, ruleid, shape, tag_nodes, max_span=-1, sparse=True):
        self.ruleid:str = ruleid
        self.shape:str = shape
        self.tag_nodes:List[TagNode] = tag_nodes
        self.max_span:int = max_span
        self.sparse:bool = sparse


class Parser:
    def __init__(self):
        self.parser = gen_parser()

    def parse(self, xeql:str) -> EQLRule:
        ast = self.parser.parse(xeql)
        _, head, seq = ast
        # parse head
        _, rule_id, mode, shape, _commonk = head
        commonk = _commonk[1]
        common_binder = KeyGroupBind("*", commonk)
        # parse seq
        tag_nodes = []
        for event_rule in seq:
            tid = event_rule[1]
            tagrule = TagRule(tid)
            binders = [KeyGroupBind(gid, fields) for gid, fields in event_rule[2]] if len(event_rule) == 3 else []
            binders = [common_binder] + binders
            tagnode = TagNode(tag_rule=tagrule, binders=binders)
            tag_nodes.append(tagnode)
        rule = EQLRule(
            ruleid=rule_id,
            shape=shape,
            tag_nodes=tag_nodes,
            max_span=60,
            sparse=mode=="sparse"
        )
        return rule


if __name__ == "__main__":
    testcase = '''
        test_rule: sparse sequence by pid
            [tag1] by (f4, f5):*, (f1, f2):g1, (f3):g2
            [tag2] by (f1, f2):*, (f3):g2
            [tag3] by (f2, f1):*, (f3, f4):g1
    '''
    testcase_json_rule = {
        "rule_id": "test rule",
        "shape": "sequence",
        "sparse": True,
        "common_keys": ["", ""],
        "tag_nodes": [
            {
                "tag_rule": "",
                "binders": [
                    {
                        "group_id": "",
                        "fields": ["", ""]
                    },
                ],
            },
        ],
    }
