import time
from typing import Any, Dict
from collections import defaultdict
from Components.Component import Component
from Sources.ThreadSource import ThreadSource
import matplotlib.pyplot as plt
import numpy as np


class LatencyTestSource(ThreadSource):

    def __init__(self):
        super().__init__()
        self.comps = []
        self.inter_event_time = 0.1
        self.cur_state = None
        self.n_comps = 5
        self.burst_n_loops = 10

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
                for comp in self.comps[:self.n_comps]:
                    self.update_component(comp, b, {"t": time.perf_counter()})
                b = not b
            elif self.cur_state == "burst":
                for i in range(self.burst_n_loops):
                    for comp in self.comps[:self.n_comps]:
                        self.update_component(comp, b, {"t": time.perf_counter()})
                    b = not b
            elif self.cur_state == "done":
                self.plot()
                return
            time.sleep(self.inter_event_time)

    def register_component(self, component: Component, metadata: Dict) -> None:
        self.comps.append(component.id)

    def write_component(self, component_id: str, msg: Any) -> None:
        if 'state' in msg:
            self.cur_state = msg['state']
        else:
            if self.cur_state == "single_component":
                self.single_latencies.append(time.perf_counter() - msg["t"])
            elif self.cur_state == "many_components":
                self.many_latencies[component_id].append(time.perf_counter() - msg["t"])
            elif self.cur_state == "burst":
                self.burst_latencies[component_id].append(time.perf_counter() - msg["t"])

    def plot(self):
        self.single_latencies = [x * 1000 for x in self.single_latencies]  # Convert to ms
        self.many_latencies = {k: [x * 1000 for x in v] for k, v in self.many_latencies.items()}
        self.burst_latencies = {k: [x * 1000 for x in v] for k, v in self.burst_latencies.items()}

        fig, axs = plt.subplots(3, 1, figsize=(10, 15))

        def display_stats(ax, latencies):
            mean = np.mean(latencies)
            std_dev = np.std(latencies)
            stats_text = f'Mean: {mean:.2f} ms, Std Dev: {std_dev:.2f} ms'
            ax.text(0.6, 0.95, stats_text, transform=ax.transAxes, fontsize=10, verticalalignment='top')

        axs[0].hist(self.single_latencies, bins=50, color='blue')
        axs[0].set_title('Single Component Latencies')
        axs[0].set_xlabel('Latency (ms)')
        axs[0].set_ylabel('Frequency')
        display_stats(axs[0], self.single_latencies)

        # Function to plot for dictionary latencies
        def plot_latencies(ax, latencies, title):
            colors = plt.cm.viridis(np.linspace(0, 1, len(latencies)))
            for (comp_id, lat), color in zip(latencies.items(), colors):
                ax.hist(lat, bins=50, color=color, alpha=0.7, label=f'Component {comp_id}')
            ax.set_title(title)
            ax.set_xlabel('Latency (ms)')
            ax.set_ylabel('Frequency')
            ax.legend()

        plot_latencies(axs[1], self.many_latencies, 'Many Components Latencies')
        plot_latencies(axs[2], self.burst_latencies, 'Burst Latencies')
        plt.subplots_adjust(hspace=0.5)
        plt.show()
