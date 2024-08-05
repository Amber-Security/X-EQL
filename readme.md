# Holmes: Streaming Cross Events Query Engine

[![release](https://img.shields.io/badge/Latest_release-v1.3.0_alpha-red.svg)](https://github.com/Amber-Security/X-EQL/releases/tag/v1.3.0-alpha)
[![zh-cn-document](https://img.shields.io/badge/Document-Chinese_version-green.svg)](./README.zh-cn.md)
[![organization](https://img.shields.io/badge/Organization-Amber_Security-yellow.svg)](https://github.com/Amber-Security)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## What is Holmes

Holmes is a streaming events query engine, which queries an event sequence from the streamed event input that fits the constraint of the data feature.

## Getting Started

### Install

> The whole engine is packaged into three python-package: `holmes_engine`, `holmes_rule` and `holmes_copilot`. <br>Directly install the `.whl` file in the newest release with `pip`.

```
pip install holmes-*.whl
```

### Rule development

#### Holmes syntax

```
RULE_NAME: MODE sequence by FIELD1, FIELD2, ...
    [EVENT_TAG1] by (f4, f5):g, (f1, f2):g1, (f3):g2
    [EVENT_TAG2] by (f1, f2):g, (f3):g2, (f5):g3
    [EVENT_TAG3] by (f2, f1):g, (f3, f4):g1, (f5):g3
```

* `RULE_NAME` - rule name
* `MODE` - Can be value of `sparse` or `dense`. Up to now, only `sparse` supported
* `by FIELD1, FIELD2, ...` - The global join keys. Can be empty.
* `EVENT_TAG1` - Specify a single event name.
* `by (f4, f5):g` - Specify a group of join keys. Join keys refers to the specified field names of the specified EVENT.


#### Rule compile

```Python
from holmes_rule.parser import Parser

parser = Parser()
ast = parser.parse(rule="# content of the Holmes rule")

parser.dump(ast, "rule_xxx.json")
```

#### Rule load

```Python
import json
from holmes_rule.rule import load_rule

with open("rule_xxx.json", "r", encoding="utf-8") as file:
    ast = json.load(file)

rule = load_rule(ast)
```

### Engine running

#### Add rules

```Python
# ...
# rule = load_rule(ast)

from holmes_engine.engine import Engine

engine = Engine()
engine.add_holmes_rule(rule=rule)
```

#### Feed events

```Python
test_events_without_noise = [
    {"Holmes-tag": "tag1", "pid": 111, "f1": "a", "f2": "b", "f3": "c", "f4": "d", "f5": "e", "time": 1},
    {"Holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "x", "time": 10},
    {"Holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "y", "time": 11},
    {"Holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "x", "time": 12},
    {"Holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "y", "time": 20},
    {"Holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "x", "time": 21},
    {"Holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "y", "time": 22},
]

for event in test_events_without_noise:
    engine.process_event(event=event)
```

#### Fetch results

```Python
engine.fetch_results()
```
### Copilot

We provide a Copilot for automatically developing holmes rules: Input an expected events sequence, and Copilot automatically generates the holmes rule.

```Python
from holmes_copilot.copilot import Copilot

test_events_without_noise = [
    {"holmes-tag": "ssh_login", "pid": 112, "sessionid": "9876", "localip": "10.2.3.4", "remoteip": "10.2.3.9", "f4": " ", "f5": "x", "time": 10},
    {"holmes-tag": "read_knownhost", "pid": 113, "sessionid": "9876", "localip": "10.2.3.4", "remoteip": "10.2.3.9", "f4": "-", "f5": "z", "time": 12},
    {"holmes-tag": "ssh_login", "pid": 111, "sessionid": "3398", "localip": "10.2.3.5", "remoteip": "10.2.3.4", "f4": "b", "f5": "y", "time": 22},
]
rule = Copilot.generate_rule(test_events_without_noise)
print(rule)
```
And you will get the output:
```
ssh_login_TO_read_knownhost_TO_ssh_login: sparse sequence 
    [ssh_login] by (sessionid):g1, (localip):g2, (remoteip):g3
    [read_knownhost] by (sessionid):g1, (localip):g2, (remoteip):g3
    [ssh_login] by (remoteip):g2
```

## For developer

### Understand each module

#### src directory

```
·-+-· holmes_rule
  |    +-· syntax.py  → YACC grammar implementation of rules
  |    +-· rule.py    → The class definition of the rule, based on which the engine understands rules; Provides an api transforming the input AST to a rule instance.
  |    +-· parser.py  → Input the Holmes rule text, invoke the parsing-api in `syntax.py`, and return the ast of the rules
  +-- holmes_engine
  |    +-· engine.py  → The processing engine. Three apis provided: add rule, input events and fetch results.
  |    +-· worker.py  → Each rule has one worker. The worker undertakes all computing.
  |    +-· kgtree.py  → A kgtree maintains all state of one rule's matching
  |    +-· event.py   → Data abstraction of a single input event.
  +-- holmes_copilot
       +-· copilot.py  → Input an expected events sequence, and Copilot automatically generates the holmes rule.
```

#### Workflow by modules

![workflow](./doc/workflow.png)

### Algorithm

[📑Here but up to now only available in Chinese doc](https://github.com/Amber-Security/X-EQL/blob/main/README.zh-cn.md#%E7%AE%97%E6%B3%95%E7%90%86%E8%A7%A3)
