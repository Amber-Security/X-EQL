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
        # Mock HolmesRule and other dependencies
        self.mock_rule = MagicMock(spec=HolmesRule)
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid=None, binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid=None, binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.mock_rule.max_span = 10
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")
        self.worker.tid_dyn = "tid1"
        self.worker.CONJUGATE_MAP = {
            "tid1": {"tid2": ["gid1"]},
            "tid2": {"tid1": ["gid2"]}
        }
        self.worker.TAG2KG = {
            "tid1": {"gid1": ["field1"]},
            "tid2": {"gid2": ["field2"]}
        }

    def test_init(self):
        self.assertEqual(self.worker.rule, self.mock_rule)
        self.assertEqual(self.worker.rulename, "test_rule")
        self.assertEqual(self.worker.dup_nodes, {"tid1": 0, "tid2": 0})
        self.assertEqual(self.worker.ENTRY_TID, "tid1")
        self.assertEqual(self.worker.FINAL_TID, "tid2")
        self.assertEqual(self.worker.TAGID_SEQ, ["tid1", "tid2"])
        self.assertEqual(self.worker.TAGID_SET, {"tid1", "tid2"})
        self.assertEqual(self.worker.TAGID2IND, {"tid1": 0, "tid2": 1})
        self.assertEqual(self.worker.TAG2KG, {"tid1": {"gid1": ["field1"]}, "tid2": {"gid2": ["field2"]}})
        self.assertEqual(self.worker.TAG2INC, {"tid1": {"gid1": ["field1"]}, "tid2": {"gid2": ["field2"]}})
        self.assertEqual(self.worker.CONJUGATE_MAP, {"tid2": {"tid1": ["gid2"]}})

    def test_gen_tag2kg(self):
        self.worker.gen_tag2kg()
        self.assertEqual(self.worker.TAG2KG, {"tid1": {"gid1": ["field1"]}, "tid2": {"gid2": ["field2"]}})

    def test_gen_kg_inc(self):
        self.worker.gen_kg_inc()
        self.assertEqual(self.worker.TAG2INC, {"tid1": {"gid1": ["field1"]}, "tid2": {"gid2": ["field2"]}})

    def test_gen_kg_conjugate(self):
        self.worker.gen_kg_conjugate()
        self.assertEqual(self.worker.CONJUGATE_MAP, {"tid2": {"tid1": ["gid2"]}})

    def test_prune_algorithm(self):
        entry = MagicMock(spec=KGTreeNode)
        dead_leaves = [MagicMock(spec=KGTreeNode)]
        self.worker.prune_algorithm(entry, dead_leaves)
        entry.leaves.remove.assert_called_once_with(dead_leaves[0])

    def test_is_dead_leaf(self):
        leaf = MagicMock(spec=KGTreeNode)
        leaf.eid = "eid1"
        self.worker.EID_MAP["eid1"] = MagicMock(raw_event={"time": 0})
        self.assertTrue(self.worker.is_dead_leaf(leaf, 11))
        self.assertFalse(self.worker.is_dead_leaf(leaf, 5))

    def test_prune(self):
        self.worker.ENTRY_POOL = [MagicMock(spec=KGTreeNode)]
        self.worker.ENTRY_POOL[0].leaves = [MagicMock(spec=KGTreeNode)]
        self.worker.ENTRY_POOL[0].leaves[0].eid = "eid1"
        self.worker.EID_MAP["eid1"] = MagicMock(raw_event={"time": 0})
        self.worker.prune(11)
        self.worker.prune_algorithm.assert_called_once()

    def test_new_event(self):
        raw_event = {"time": 1}
        event = self.worker.new_event(raw_event)
        self.assertIsInstance(event, Event)
        self.assertEqual(event.raw_event, raw_event)

    def test_new_event_node(self):
        event = MagicMock(spec=Event)
        event.eid = "eid1"
        node = self.worker.new_event_node(event)
        self.assertIsInstance(node, KGTreeNode)
        self.assertEqual(self.worker.EID_MAP["eid1"], event)

    def test_new_entry(self):
        raw_event = {"time": 1}
        self.worker.new_entry(raw_event)
        self.assertEqual(len(self.worker.ENTRY_POOL), 1)

    def test_check_time_order(self):
        inspector_node = MagicMock(spec=KGTreeNode)
        inspector_node.eid = "eid1"
        self.worker.EID_MAP["eid1"] = MagicMock(raw_event={"time": 0})
        self.assertTrue(self.worker.check_time_order(inspector_node, {"time": 5}))
        self.assertFalse(self.worker.check_time_order(inspector_node, {"time": 15}))

    def test_check_constraint(self):
        inspector_node = MagicMock(spec=KGTreeNode)
        inspector_node.eid = "eid1"
        self.worker.EID_MAP["eid1"] = MagicMock(tid_dyn="tid1", kg_inc={"gid1": ("value1",)})
        self.worker.tid_dyn = "tid2"
        self.worker.CONJUGATE_MAP = {
            "tid2": {"tid1": ["gid1"]}
        }
        self.assertTrue(self.worker.check_constraint(inspector_node, {"field1": "value1"}))
        self.assertFalse(self.worker.check_constraint(inspector_node, {"field1": "value2"}))

    def test_precheck_has_position(self):
        root = MagicMock(spec=KGTreeNode)
        root.leaves = [MagicMock(spec=KGTreeNode)]
        root.leaves[0].eid = "eid1"
        self.worker.EID_MAP["eid1"] = MagicMock(tid_dyn="tid1")
        self.worker.tid_dyn = "tid2"
        self.assertTrue(self.worker.precheck_has_position(root))

    def test_join_new_leaf(self):
        entry = MagicMock(spec=KGTreeNode)
        root = MagicMock(spec=KGTreeNode)
        inspected_event = {"time": 1}
        node = self.worker.join_new_leaf(entry, inspected_event, root)
        self.assertIsInstance(node, KGTreeNode)
        entry.add_child.assert_called_once_with(node=node)
        root.set_leaf.assert_called_once_with(leaf=node)

    def test_liquidate_dense(self):
        self.worker.DENSE_CACHE = {MagicMock(spec=KGTreeNode): {0: [MagicMock(spec=Event)]}}
        results = self.worker.liquidate_dense(1, MagicMock(spec=KGTreeNode))
        self.assertEqual(results, [])

    def test_process_dfs(self):
        entry = MagicMock(spec=KGTreeNode)
        entry.eid = "eid1"
        self.worker.EID_MAP["eid1"] = MagicMock(tid_dyn="tid1")
        self.worker.tid_dyn = "tid2"
        results = self.worker.process_dfs(entry, {"time": 1}, MagicMock(spec=KGTreeNode))
        self.assertEqual(results, [])

    def test_fetch_results(self):
        leaf = MagicMock(spec=KGTreeNode)
        leaf.eid = "eid1"
        leaf.parent = None
        self.worker.EID_MAP["eid1"] = MagicMock(tid_dyn="tid1", raw_event={"time": 1})
        results = self.worker.fetch_results(leaf)
        self.assertEqual(results, [{"time": 1}])

    def test_is_start_event(self):
        self.assertTrue(self.worker.is_start_event("tid1"))
        self.assertFalse(self.worker.is_start_event("tid2"))

    def test_process_event(self):
        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

        event = {"holmes-tag": "tid2", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_dense(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid="dense1", binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

        event = {"holmes-tag": "tid2", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_duplicate_tids(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid=None, binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid=None, binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_invalid_tid(self):
        event = {"holmes-tag": "invalid_tid", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_final_tid(self):
        event = {"holmes-tag": "tid2", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_dense_boot(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid="dense1", binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

        event = {"holmes-tag": "tid2", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_dense_boot_and_final_tid(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid="dense1", binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

        event = {"holmes-tag": "tid2", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_dense_boot_and_invalid_tid(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid="dense1", binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "invalid_tid", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_dense_boot_and_duplicate_tids(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_dense_boot_and_final_tid_and_invalid_tid(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid="dense1", binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "invalid_tid", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])



    def test_process_event_with_multiple_dense_gids(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid="dense2", binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

        event = {"holmes-tag": "tid2", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_no_matching_dense_gid(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid="dense2", binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid3", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_multiple_binders_and_fields(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[
                MagicMock(group_id="gid1", fields=["field1"]),
                MagicMock(group_id="gid2", fields=["field2"]),
            ]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_no_binders(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_missing_holmes_tag(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_invalid_time(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": "invalid_time"}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_multiple_events(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid="dense2", binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        events = [
            {"holmes-tag": "tid1", "time": 1},
            {"holmes-tag": "tid2", "time": 2},
        ]
        results = [self.worker.process_event(event) for event in events]
        self.assertEqual(results, [[], []])

    def test_process_event_with_large_time_gap(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

        event = {"holmes-tag": "tid1", "time": 1000000}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_multiple_dense_gids_and_tids(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid="dense1", binders=[MagicMock(group_id="gid2", fields=["field2"])]),
            MagicMock(tag_rule=MagicMock(id="tid3"), dense_gid="dense2", binders=[MagicMock(group_id="gid3", fields=["field3"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

        event = {"holmes-tag": "tid2", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

        event = {"holmes-tag": "tid3", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_complex_event_structure(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {
            "holmes-tag": "tid1",
            "time": 1,
            "extra_field": "extra_value",
            "nested": {
                "nested_field": "nested_value"
            }
        }
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_complex_event_structure(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {
            "holmes-tag": "tid1",
            "time": 1,
            "extra_field": "extra_value",
            "nested": {
                "nested_field": "nested_value"
            }
        }
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_multiple_events_and_different_tids(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid="dense2", binders=[MagicMock(group_id="gid2", fields=["field2"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        events = [
            {"holmes-tag": "tid1", "time": 1},
            {"holmes-tag": "tid2", "time": 2},
            {"holmes-tag": "tid1", "time": 3},
        ]
        results = [self.worker.process_event(event) for event in events]
        self.assertEqual(results, [[], [], []])

    def test_process_event_with_large_number_of_events(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        events = [{"holmes-tag": "tid1", "time": i} for i in range(1000)]
        results = [self.worker.process_event(event) for event in events]
        self.assertEqual(results, [[] for _ in range(1000)])

    def test_process_event_with_different_dense_gids_and_tids(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
            MagicMock(tag_rule=MagicMock(id="tid2"), dense_gid="dense2", binders=[MagicMock(group_id="gid2", fields=["field2"])]),
            MagicMock(tag_rule=MagicMock(id="tid3"), dense_gid="dense3", binders=[MagicMock(group_id="gid3", fields=["field3"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        events = [
            {"holmes-tag": "tid1", "time": 1},
            {"holmes-tag": "tid2", "time": 2},
            {"holmes-tag": "tid3", "time": 3},
        ]
        results = [self.worker.process_event(event) for event in events]
        self.assertEqual(results, [[], [], []])

    def test_process_event_with_missing_fields_in_event(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1"}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_extra_fields_in_event(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1, "extra_field": "extra_value"}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_nested_fields_in_event(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[MagicMock(group_id="gid1", fields=["field1"])]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1, "nested": {"nested_field": "nested_value"}}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_multiple_binders_and_different_fields(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[
                MagicMock(group_id="gid1", fields=["field1"]),
                MagicMock(group_id="gid2", fields=["field2"]),
            ]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_multiple_binders_and_same_fields(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[
                MagicMock(group_id="gid1", fields=["field1"]),
                MagicMock(group_id="gid2", fields=["field1"]),
            ]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

    def test_process_event_with_multiple_binders_and_no_fields(self):
        self.mock_rule.tag_nodes = [
            MagicMock(tag_rule=MagicMock(id="tid1"), dense_gid="dense1", binders=[
                MagicMock(group_id="gid1", fields=[]),
                MagicMock(group_id="gid2", fields=[]),
            ]),
        ]
        self.worker = Worker(rule=self.mock_rule, rulename="test_rule")

        event = {"holmes-tag": "tid1", "time": 1}
        results = self.worker.process_event(event)
        self.assertEqual(results, [])

if __name__ == '__main__':
    unittest.main()