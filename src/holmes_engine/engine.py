from typing import List, Dict

from holmes_rule.rule import HolmesRule
from .worker import Worker


class Engine:
    def __init__(self) -> None:
        # For results caching, fetch by application layer with Engine.fetch_results()
        self.results_cached_buffer = []
        # One worker is a engine instance correspondinng one rule
        self.workers:Dict[str, Worker] = {}
        # Record some tag should be checked by which rules(workers). The int-item is worker_ind
        self.tag_index:Dict[str, set[str]] = {}

    def add_holmes_rule(self, rule:HolmesRule):
        # check exist
        if rule.ruleid in self.workers:
            return "exist"
        # add worker
        worker = Worker(rule=rule, rulename=rule.ruleid)
        self.workers[rule.ruleid] = worker
        # add tag2worker index
        for tag_node in rule.tag_nodes:
            tag_id = tag_node.tag_rule.id
            if tag_id not in self.tag_index: self.tag_index[tag_id] = set()
            self.tag_index[tag_id].add(rule.ruleid)
        return "success"

    def del_holmes_rule(self, ruleid):
        # check exist
        if ruleid not in self.workers:
            return "not exist"
        # del worker
        del self.workers[ruleid]
        return "success"

    def update_holmes_rule(self, rule:HolmesRule):
        r = self.del_holmes_rule(ruleid=rule.ruleid)
        if r == "not exist": return r
        self.add_holmes_rule(rule=rule)
        return "success"

    def fetch_results(self):
        # will clean the cached results
        results = self.results_cached_buffer
        self.results_cached_buffer = []
        return results

    def process_event(self, event):
        tag_id = event["holmes-tag"]
        if tag_id not in self.tag_index: return
        for holmes_rule_id in self.tag_index[tag_id]:
            worker = self.workers[holmes_rule_id]
            results = worker.process_event(event=event)
            worker.prune(event_time=event["time"])
            if results != []:
                for result in results:
                    self.results_cached_buffer.append({"rulename": worker.rulename, "output": result})
