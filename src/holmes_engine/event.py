from typing import Dict, Tuple


class Event:
    def __init__(self, eid, raw_event, tid_dyn, kg_inc_map):
        self.eid:str = eid
        self.raw_event = raw_event
        self.tid_dyn:str = tid_dyn
        self.kg_inc_map:Dict[str, Tuple] = kg_inc_map
        self.kg_inc:Dict[str, Tuple] = {}
        self.gen_kg_inc()

    def gen_kg_inc(self):
        if self.kg_inc_map is None:
            assert self.tid_dyn == "DENSE_BOOT"
            return
        for group_id in self.kg_inc_map:
            fields = self.kg_inc_map[group_id]
            fields_values = tuple([self.raw_event[name] for name in fields])
            self.kg_inc[group_id] = fields_values
