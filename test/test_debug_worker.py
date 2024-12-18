import unittest
from unittest.mock import patch, MagicMock
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

    @patch('holmes_engine.worker.Worker.new_event_node')
    @patch('holmes_engine.worker.Worker.new_event')
    def test_join_new_leaf_with_dict(self, mock_new_event, mock_new_event_node):
        # 模拟输入
        inspected_event = {"time": "2023-10-01T12:00:00"}
        entry = MagicMock(spec=KGTreeNode)
        root = MagicMock(spec=KGTreeNode)

        # 模拟 new_event 和 new_event_node 方法的返回值
        mock_event = MagicMock(spec=Event)
        mock_event.raw_event = inspected_event
        mock_new_event.return_value = mock_event

        mock_node = MagicMock(spec=KGTreeNode)
        mock_new_event_node.return_value = mock_node

        # 调用 join_new_leaf 方法
        result_node = self.worker.join_new_leaf(entry, inspected_event, root)

        # 验证方法调用
        mock_new_event.assert_called_once_with(inspected_event)
        mock_new_event_node.assert_called_once_with(event=mock_event)
        entry.add_child.assert_called_once_with(node=mock_node)
        root.set_leaf.assert_called_once_with(leaf=mock_node)
        self.assertEqual(self.worker.last_ts_cache, inspected_event["time"])
        self.assertEqual(result_node, mock_node)

    @patch('holmes_engine.worker.Worker.new_event_node')
    def test_join_new_leaf_with_event(self, mock_new_event_node):
        # 模拟输入
        inspected_event = MagicMock(spec=Event)
        inspected_event.raw_event = {"time": "2023-10-01T12:00:00"}
        entry = MagicMock(spec=KGTreeNode)
        root = MagicMock(spec=KGTreeNode)

        # 模拟 new_event_node 方法的返回值
        mock_node = MagicMock(spec=KGTreeNode)
        mock_new_event_node.return_value = mock_node

        # 调用 join_new_leaf 方法
        result_node = self.worker.join_new_leaf(entry, inspected_event, root)

        # 验证方法调用
        mock_new_event_node.assert_called_once_with(event=inspected_event)
        entry.add_child.assert_called_once_with(node=mock_node)
        root.set_leaf.assert_called_once_with(leaf=mock_node)
        self.assertEqual(self.worker.last_ts_cache, inspected_event.raw_event["time"])
        self.assertEqual(result_node, mock_node)

if __name__ == '__main__':
    unittest.main()
