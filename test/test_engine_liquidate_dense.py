import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from typing import List, Dict, Tuple, Set

from holmes_rule.rule import HolmesRule
from holmes_engine.event import Event
from holmes_engine.kgtree import KGTreeNode
from holmes_engine.worker import Worker

class TestWorker(unittest.TestCase):

    def setUp(self):
        self.mock_rule = MagicMock()
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid=None, binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid=None, binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")
        self.worker.CONJUGATE_MAP = {
            "tid1": {"tid2": ["gid1"]},
            "tid2": {"tid1": ["gid2"]}
        }
        self.worker.TAG2KG = {
            "tid1": {"gid1": ["field1"]},
            "tid2": {"gid2": ["field2"]}
        }
        self.worker.DENSE_CACHE = {
            MagicMock(eid="eid1"): {
                0: [MagicMock(raw_event={"time": 100})],
                1: [MagicMock(raw_event={"time": 101}, tid_dyn="tid2")],
            }
        }
        self.worker.SLOT_LEN_MAP = {"tid1": 2}
        self.worker.EID_MAP = {"eid1": MagicMock(tid_dyn="tid1")}
        self.worker.DENSE_LEAVES = set()
        self.worker.FIND_DENSE_PREV = {"tid1": "tid1", "tid2": "tid1"}  # 确保包含 'tid1' 和 'tid2'
        self.worker.DENSE_SHAPE_IND = {"tid1": 0, "tid2": 1}  # 确保包含 'tid1' 和 'tid2'
        self.worker.default_dense_expired = 10

    @patch('holmes_engine.worker.Worker.join_new_leaf')
    @patch('holmes_engine.worker.Worker.process_dfs')
    @patch('holmes_engine.worker.Worker.prune_algorithm')
    def test_liquidate_dense(self, mock_prune_algorithm, mock_process_dfs, mock_join_new_leaf):
        # 模拟输入
        time = 111
        root = MagicMock(spec=KGTreeNode)

        # 模拟 join_new_leaf 和 process_dfs 方法的返回值
        mock_join_new_leaf.side_effect = [MagicMock(spec=KGTreeNode, eid="eid1"), MagicMock(spec=KGTreeNode, eid="eid2")]
        mock_process_dfs.return_value = ["result1", "result2"]

        # 调用 liquidate_dense 方法
        results = self.worker.liquidate_dense(time=time, root=root)

        # 验证方法调用
        mock_join_new_leaf.assert_called()
        mock_process_dfs.assert_called()
        mock_prune_algorithm.assert_called_once_with(entry=root, dead_leaves=[])  # 确保 dead_leaves 为空列表
        self.assertEqual(results, ["result1", "result2"])

if __name__ == '__main__':
    unittest.main()
