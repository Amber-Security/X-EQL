#

## 一个结点本质上就是一个增量的kg

sparse模式下，全部同级node的diff一定是相等的

## kgcheck 算法本质

1. DFS kgtree

## 数据结构

1. event：

    basic

    eid

    kg-inc

        {gid: value}

2. index2event:
    
    每个event算个uuid唯一标记，反向map得到该结构

2. kgtree:
    1. Node:
        - eid
        - children


