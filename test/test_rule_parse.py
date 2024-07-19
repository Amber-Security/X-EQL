
from holmes_rule.syntax import gen_parser
from holmes_rule.rule import load_rule, HolmesRule


def test_yacc_to_ast():
    ast_root = gen_parser().parse('''
        test_rule: sequence by pid
            [tag1] by (f4, f5):g, (f1, f2):g1, (f3):g2
            [tag2] 
            [
                [tag5] by (f2, f1):g, (f3, f4):g1      
                [tag6] by (f2, f1):g, (f3, f4):g1      
            ]
            [
                [tag5] by (f2, f1):g, (f3, f4):g1      
                [tag6] by (f2, f1):g, (f3, f4):g1      
            ]
            [tag3] by (f2, f1):g, (f3, f4):g1      
    ''')

    import json
    print(json.dumps(ast_root, indent=4))
    rule:HolmesRule = load_rule(ast_root)
    print(rule)
    print([tag.dense_gid for tag in rule.tag_nodes])


if __name__ == '__main__':
    test_yacc_to_ast()
