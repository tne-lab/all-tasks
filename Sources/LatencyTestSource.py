import time
from typing import Any, Dict
from collections import defaultdict
from Components.Component import Component
from Sources.ThreadSource import ThreadSource


class LatencyTestSource(ThreadSource):

    def __init__(self):
        super().__init__()
        self.comps = []
        self.inter_event_time = 0.1
        self.cur_state = None

        self.single_latencies = []
        self.many_latencies = defaultdict(list)
        self.burst_latencies = defaultdict(list)

    def initialize(self):
        b = False
        while True:
            if self.cur_state == "single_component":
                self.update_component("latency_comp-0-0", b, {"t": time.perf_counter()})
                b = not b
            elif self.cur_state == "many_components":
                for comp in self.comps:
                    self.update_component(comp, b, {"t": time.perf_counter()})
                b = not b
            elif self.cur_state == "burst":
                for i in range(5):
                    for comp in self.comps:
                        self.update_component(comp, b, {"t": time.perf_counter()})
                    b = not b
            time.sleep(self.inter_event_time)

    def register_component(self, component: Component, metadata: Dict) -> None:
        self.comps.append(component.id)

    def write_component(self, component_id: str, msg: Any) -> None:
        if 'state' in msg:
            self.cur_state = msg['state']

