from typing import List, Dict

from rule.rule import EQLRule
from .worker import Worker


class Engine:
    def __init__(self) -> None:
        # For results caching, fetch by application layer with Engine.fetch_results()
        self.results_cached_buffer = []
        # One worker is a engine instance correspondinng one rule
        self.workers:List[Worker] = []
        # Record some tag should be checked by which rules(workers). The int-item is worker_ind
        self.tag_index:Dict[str, set[int]] = {}

    def add_eql_rule(self, rule:EQLRule):
        # add worker
        worker = Worker(rule=rule, rulename=rule.ruleid)
        self.workers.append(worker)
        # add tag2worker index
        worker_ind = len(self.workers) - 1
        for tag_node in rule.tag_nodes:
            tag_id = tag_node.tag_rule.id
            if tag_id not in self.tag_index: self.tag_index[tag_id] = set()
            self.tag_index[tag_id].add(worker_ind)

    def fetch_results(self):
        # will clean the cached results
        results = self.results_cached_buffer
        self.results_cached_buffer = []
        return results

    def process_event(self, event):
        tag_id = event["x-eql-tag"]
        for worker_ind in self.tag_index[tag_id]:
            worker = self.workers[worker_ind]
            results = worker.process_event(event=event)
            worker.prune(event_time=event["time"])
            if results != []:
                if worker.rule.sparse:
                    for result in results:
                        self.results_cached_buffer.append({"rulename": worker.rulename, "output": result})
                else:
                    pass
