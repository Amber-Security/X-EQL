import json
from .syntax import gen_parser


class Parser:
    def __init__(self):
        self.parser = gen_parser()

    def parse(self, rule:str):
        ast = self.parser.parse(rule)
        return ast

    def dump(self, ast, filepath):
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(ast, file)


if __name__ == "__main__":
    pass
