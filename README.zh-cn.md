# 福尔摩斯: 流式跨事件查询引擎
[![release](https://img.shields.io/badge/Latest_release-v1.2.0_alpha-red.svg)](https://github.com/Amber-Security/X-EQL/releases/tag/v1.2.0-alpha)
[![organization](https://img.shields.io/badge/Organization-Amber_Security-yellow.svg)](https://github.com/Amber-Security)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## 功能

从流式的事件输入中查询符合数据特征约束的一个事件序列

## 快速上手

> 引擎整体被封装为三个python的包：`holmes_engine`, `holmes_rule`和`holmes_copilot`.

### 规则开发

#### Holmes语法

```
RULE_NAME: MODE sequence by FIELD1, FIELD2, ...
    [EVENT_TAG1] by (f4, f5):g, (f1, f2):g1, (f3):g2
    [EVENT_TAG2] by (f1, f2):g, (f3):g2, (f5):g3
    [EVENT_TAG3] by (f2, f1):g, (f3, f4):g1, (f5):g3
```

* `RULE_NAME` - 规则名
* `MODE` - 值可选为 `sparse` or `dense`. 目前仅支持 `sparse`
* `by FIELD1, FIELD2, ...` - 全局字段约束，可以不指定
* `EVENT_TAG1` - 指定一个单事件的名字.
* `by (f4, f5):g` - 指定一组字段约束. 括号内指定这个group要约束该事件的哪些字段名.

#### 规则编译

```Python
from holmes_rule.parser import Parser

parser = Parser()
ast = parser.parse(rule="# content of the holmes rule")

parser.dump(ast, "rule_xxx.json")
```

#### 规则加载

```Python
import json
from holmes_rule.rule import load_rule

with open("rule_xxx.json", "r", encoding="utf-8") as file:
    ast = json.load(file)

rule = load_rule(ast)
```

### 引擎运行

#### 添加规则

```Python
# ...
# rule = load_rule(ast)

from holmes_engine.engine import Engine

engine = Engine()
engine.add_holmes_rule(rule=rule)
```

#### 事件输入

```Python
test_events_without_noise = [
    {"holmes-tag": "tag1", "pid": 111, "f1": "a", "f2": "b", "f3": "c", "f4": "d", "f5": "e", "time": 1},
    {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "x", "time": 10},
    {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "y", "time": 11},
    {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "x", "time": 12},
    {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "y", "time": 20},
    {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "x", "time": 21},
    {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "y", "time": 22},
]

for event in test_events_without_noise:
    engine.process_event(event=event)
```

#### 结果读取

```Python
engine.fetch_results()
```

### Copilot

为了使holmes规则的开发具备更好的自动化潜力，我们提供了一个Copilot: 输入预期的事件序列，Copilot自动生成用以检出该预期事件序列模式的holmes规则。

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
执行上述用例，将得到预期输出:
```
ssh_login_TO_read_knownhost_TO_ssh_login: sparse sequence 
    [ssh_login] by (sessionid):g1, (localip):g2, (remoteip):g3
    [read_knownhost] by (sessionid):g1, (localip):g2, (remoteip):g3
    [ssh_login] by (remoteip):g2
```

## 开发者手册

### 各模块理解

#### src目录结构

```
·-+-· holmes_rule
  |    +-· syntax.py  → 规则的YACC文法实现
  |    +-· rule.py    → 规则的class定义，引擎是根据这里的实现来理解规则的；提供api将输入的ast实例化为规则实例
  |    +-· parser.py  → 输入文本规则，调用syntax中的接口解析规则，输出为规则的ast
  +-- holmes_engine
  |    +-· engine.py  → 处理引擎，提供添加规则、输入事件、读取结果3个api
  |    +-· worker.py  → 一条规则一个worker，由worker承担全部的匹配计算
  |    +-· kgtree.py  → kgtree维护规则匹配的全部状态
  |    +-· event.py   → 输入单事件的数据抽象
  +-- holmes_copilot
       +-· copilot.py  → 输入一组预期事件序列，自动输出holmes规则
```

#### 各模块工作流

![workflow](./doc/workflow.png)

### 算法理解

#### 有序性模式

Holmes引擎是流式处理的，规则又是对顺序约束敏感的，因此对输入数据的有序性必然有特殊要求。

让我们思考几种情形：输入的单事件都有一个字段fieldx区分事件发生顺序
* 不会有两个事件具有相同的fieldx值：我们称之为满足“稀疏”
* 由于粒度限制（例如时间戳）可能会有两个事件具有相同的fieldx值：我们称之为满足“稠密”
* 全部事件的fieldx来自相同的物理空间（例如来自同一个观测终端的CPU串行采集的系统调用）：我们称之为“同步”
* 不同输入事件的fieldx可能来自不同的物理空间（例如由两个主机异步采集送来的事件），导致fieldx排出的序未必符合真实世界中事件发生的顺序：我们称之为“异步”

因此，从数据视角来看，我们面临四种情形：
* 稀疏同步
* 稠密同步
* 稀疏异步
* 稠密异步

此外，从引擎视角来看，还会面临两种情形：
* 前接消息队列保证了有序性
* 前接消息队列不保证有序性

应对上述情况，算法侧迭代的Roadmap：
* 先解决同步场景
* 再解决异步场景

截至目前版本，在前接消息队列保证了有序性的前提下，算法能够处理稀疏同步的数据，暂时称之为sparse模式

> 彩蛋：在遥远的未来，我们将支持Graph形态的事件组匹配，而非仅是序列

#### Sparse模式的算法设计

> **假设现在我们只有一条规则：把大象放进冰箱需要4步！**

**STEP0:** 当一个事件X到达，我们首先判断它在不在规则指定的事件列表里，如果压根不在，就可以抱歉下一位了

**STEP1:** 好，我们继续处理，接下来我们要判断X是否满足数据约束：也即规则指定的事件顺序中，X是否与其前面的每一个已命中事件都满足group指定的约束

**STEP2:** 很好，到这一步说明STEP1也满足了，看来事件X也加入了这个候选的事件组，此时再判断一次X是否是规则指定序列的最后一个事件。如果是，恭喜！你成功检测到了一组满足规则要求的事件序列！我们获取结果即可！

**STEP3:** 沉舟侧畔千帆过，病树前头万木春。不论X是否命中，我们都应该根据时间戳和预设的失效时长来检查一下整个匹配状态，以把那些已经失效但仍未到达规则指定序列重点的命中事件缓存清除掉。

> **你需要的只是一棵树：每个结点都是一个哨兵！**

好嘟，我们马上来到算法的精髓了，让我们打起精神。这一节将介绍STEP1 + STEP2的具体实现。

**树与DFS：**

任何满足匹配的输入事件，不管它有没有到达规则指定序列的终点，都会成为一个树结构的一个结点
> 注意：这棵树中，深度相同的（同一层的）每一个结点，都是对应规则序列中同一个位置的一个实际事件；也即树的深度的第几层即代表规则中指定序列的第几个位置

当一个新事件X到达且进入STEP1时：
> (1) 如果X就是规则序列中的第一个事件，则创建一棵新的树（root结点，或者叫entry结点）
> 
> (2) 匹配数据约束：DFS该规则下的每棵树
> > 👉 递归终点是DFS到等于X在规则中所在次序所对应的树深度（例如X对应的事件类型在规则中位于第3个，那么DFS到第三层即到达递归终点）
> > 
> > 👉 DFS递归的每一层中，检查同父节点的数据约束，以及满足顺序字段递增的约束（例如时间戳）**—— 接下来将介绍哨兵算法如何做约束检查**

**哨兵检查：**

前面提到，检查规则指定的数据约束，其实就是在每层DFS递归中都检查同父节点的数据约束，那每层中具体查什么呢？其实就是**查事件X与该层父节点事件所共有的group，也即规则中指定的`(...):g`.**

**若按照惯性思维**，DFS到某层时，我们自然是先取规则中定义的此时的父结点事件与X事件的group的交集，然后遍历交集中的每个group并从中分别获取父事件的对应字段值和X事件的对应字段值，并判断是否满足约束条件。例如：
```
...
[EVENT_TAGn] by (f1, f2):g, (f3):g2, (f5):g3
...
...
[EVENT_TAGX] by (f8, f9):g, (f3, f4):g1, (f5):g3
```
此例中，假设X是一个EVENT_TAGX事件，此时DFS到的父事件是一个EVENT_TAGn事件，则group交集是`{g, g3}`，那么先处理g：取EVENT_TAGn事件的`{f1, f2}`和X的`{f8, f9}`，这俩值判等以检查约束。然后同理再判g3。

这没问题，**但这是最好的方法吗？不！** 显然有两处优化点：
> 💡 交集运算不需要在DFS期间实时去计算，因为这个交集对于任意两个事件都是固定的，可以在规则加载时直接算好缓存起来，这并不会占用多少内存
> 
> 💡 请想想：上述例子中，如果`g`这个group在EVENT_TAGX之前，不止存在于EVENT_TAGn中，而是出现了更多次，我们真的需要在每次DFS到`g`时都要算一次吗？并不需要！只要和第一次出现`g`的事件算一次就够了！
> > 🔖 因为第一次出现`g`的事件后的每一个受`g`约束的事件如果都和第一次出现`g`的事件做过关于`g`的约束检查，那么自然就保证大家全部满足`g`的约束！
> > 
> > 🔖 因此后来的事件同样仅需和第一次出现`g`的事件做一次检查就可以确保同后续所有受`g`约束的其它事件都满足`g`约束！
> > 
> > 😀 **这就是哨兵检查算法！**

最终我们给出哨兵检查算法的实现，在规则加载阶段，我们将计算两组缓存：
* group增量表：记录规则序列中每个事件中第一次出现的groupid（这样就知道某个group第一次出现在哪个事件里），记作INC表.
* group共轭表：记录规则序列中任意两事件间仅需检查的groupid，不难想到，其值为`原始group交集 ∩ 增量表中的group`，记作CONJ表.
* 例如检查新到的y事件时DFS遍历到了x（`... → x → ... → y`），我们已在规则加载时算好了共轭表`conj[y][x] = groups_x ∩ groups_y ∩ inc[x]`，这样在该层DFS检查时，只需要查`conj[y][x]`中的groups相等就行了

总体上，我们确保了每个group只被查一遍，避免了大量冗余计算；这就好像每个结点都是一个哨兵，每个哨兵只检查新到事件中自己该检查的字段，各司其职。

**完整命中返回结果：**

如果新到事件通过了所有“哨兵”的检查，完成一条DFS路径到底后，我们将把该事件实例化成一个新结点，作为一个新的叶子加入树。

此时，如果我们发现该事件已经是规则指定序列中的最后一个事件，那么恭喜，我们命中了一组符合规则要求的事件序列，仅需递归返回结果就行了。这个操作很简单，不过多赘述，参照源码即可。

> **凋亡消消乐：落红不是无情物！**

怎么从树中清理缓存呢？我是说那些过期的结点。我们设计了一个很优雅的算法。

如果一个叶子过期了，而它的父结点又没有其它子结点，那么父节点自然也过期了，因为父结点的时间戳比叶子结点更老。

OK，理解了上面这点，我们就不难将这个过程比喻成如下的一个形象的过程：

你有一棵小树，它有很多枝杈，如果一个枝杈的末端（我们的叶子）被标记为dead（过期），那么你就可以把这根枝杈直接掰掉（此时掰断位置的那个结点没有被kill，就是因为它还有别的枝杈，也即别的子结点）**—— 这个过程其实就是从末端一路回溯并删除父结点，直到父结点有其它子结点**

然后，我们过期的结点不止一个，也即有一批枝杈的末端被标记为dead，物理世界中，我们只需要伸手把所有末端标了dead的枝杈一个个掰了这事就做完了 **—— 也即上述回溯逻辑重复执行N次，N就是过期叶子的数量，遍历每个过期叶子做一轮该操作**

你看，很简单吧？具体实现看源码

> **弯弯绕的难点：重复事件类型！**

这一部分在理解了前面的核心逻辑后，其实也不难了，但讲起来很绕，不如直接看源码。

唯一需要特别强调的一点是，由于要处理这个特性，那么新到事件如果可以创建一棵新的树（也即它就是规则指定序列的第一个事件），那这棵树的创建要放在匹配之后做。

> **独乐乐不如众乐乐：多规则并发！**

一个抽象的worker在加载任意规则后，将规则逻辑无差别地初始化前面提到的状态结构（例如增列表和共轭表），然后维护几棵树来做匹配。

多个worker显然互不影响，因为是不同的对象，成员变量天然隔离，所以天然地具有同步优势，可以直接并发的跑规则。

#### 数据结构

- Event
  - 增量查验表：<gid → fields>，含义见Worker
  - 增量查验表 - 口令表：是增量查验表的填值实例
- KGTreeNode
- Engine
  - 添加及初始化holmes规则
  - 输入event处理
    - 先判断这个event都有哪些适用的worker（rule）
    - 送入worker处理
    - 处理完后prune清理状态
  - 获取规则
- Worker
  - 一个holmes规则实例化一个worker
    - 静态结构
      - 记录起始、终止事件的tid
      - 记录事件序列的tid seq、set
      - 做事件位序表：tid → 位序，可以查看每个事件的位序
      - 做事件约束表kg：tid → <gid → fields>，可以查看每个事件的所有约束字段
      - 做增量查验表inc：tid → <gid → fields>，可以查看每个事件哨卡仅非免检的约束字段（非这些字段组已经是免检的了，因为前面已经查验过了）
      - 做哨卡查验表conj：tid → <tid → []gid>，代入一个待检event视角，它通过层层哨卡时，[仅]需要同该哨卡查验哪些暗号
    - 动态状态
      - EID_MAP：事件uuid → 事件数据结构的映射
      - ENTRY_POOL：是个森林，存一堆entrynode
  - 一个worker负责维护该rule的全量处理状态
  - sparse模式
    - 先判断是否是起点event，是的话创建一个新的entry node，然后返回，不再做进一步处理
      - 创建新entry node时：
        - 先创建一个event：uuid唯一标识，重点是填入了增量查验表的实值口令
        - 填动态状态中的EID_MAP，实例化一个treenode返回
      - 为treenode设置时间戳
      - 为treenode设置leaf是自身：没看懂
    - 如果事件压根都不在这个规则的tid set里直接pass：实际上做重复了，外层已经约束过了
    - 开始过每棵检测森林：
      - dfs一棵tree，以dfs的方式遍历逐个哨卡，在所有通关的分支上加上自己
        - 遍历到叶子后：
          - 实例化这个事件的node结点，处理加边
          - 更新root的叶子们
          - worker的最晚时戳更新
          - 如果已经是终止结点，则返回结果
      - dfs返回的结果（每个都是一个完整命中事件）收拢
      - 如果last ts cache不为空，说明这个事件通过了至少一个哨卡分支，此时更新树的last ts并清空last ts cache
      - 返回result给engine
  - prune算法：
    - 先找出森林中所有的死叶子：完整匹配的 + span过期的
    - 开始剪枝

#### 碎碎念

1. 重复tid的规则？不支持？
2. 过哨卡时好像忘了查时戳？sparse模式下，大概率时戳是对的，这样节省性能，由于层层把关，只看最后一个保证对