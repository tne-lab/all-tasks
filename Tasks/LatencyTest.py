import time
import numpy as np
from enum import Enum
from collections import defaultdict
import matplotlib.pyplot as plt

from Events import PybEvents
from Tasks.Task import Task
from Components.Both import Both


class LatencyTest(Task):
    """@DynamicAttrs"""

    class States(Enum):
        SINGLE_COMPONENT = 0
        MANY_COMPONENTS = 1
        BURST = 2

    @staticmethod
    def get_components():
        return {
            "latency_comp": [Both, Both, Both, Both, Both]
        }

    # noinspection PyMethodMayBeStatic
    @staticmethod
    def get_constants():
        return {
            'single_duration': 10 / 60,
            'many_duration': 10 / 60,
            'burst_duration': 10 / 60
        }

    @staticmethod
    def get_variables():
        return {
            'single_latencies': [],
            'many_latencies': defaultdict(list),
            'burst_latencies': defaultdict(list)
        }

    def init_state(self):
        return self.States.SINGLE_COMPONENT

    def start(self):
        self.latency_comp[0].write({'state': 'single_component'})
        self.set_timeout("single_complete", self.single_duration * 60)

    def stop(self):
        print("Single component mean latency:", np.mean(self.single_latencies))
        print("Single component # events:", len(self.single_latencies))
        for comp, latencies in self.many_latencies.items():
            print(f"MANY: {comp} Mean latency:", np.mean(latencies))
            print("MANY: Number of events:", len(latencies))

        for comp, latencies in self.burst_latencies.items():
            print(f"BURST: {comp} Mean latency:", np.mean(latencies))
            print("BURST: Number of events:", len(latencies))

        self.plot()

    def all_states(self, event: PybEvents.PybEvent) -> bool:
        if isinstance(event, PybEvents.TimeoutEvent) and event.name == "task_complete":
            self.latency_comp[0].write({'state': 'done'})
            self.complete = True
            return True
        return False

    def SINGLE_COMPONENT(self, event):
        if isinstance(event, PybEvents.TimeoutEvent) and event.name == "single_complete":
            self.change_state(self.States.MANY_COMPONENTS)
            self.latency_comp[0].write({'state': 'many_components'})
        elif isinstance(event, PybEvents.ComponentChangedEvent) and event.comp in self.latency_comp:
            self.single_latencies.append(time.perf_counter() - event.metadata["t"])

    def MANY_COMPONENTS(self, event):
        if isinstance(event, PybEvents.StateEnterEvent):
            self.set_timeout("many_complete", self.many_duration * 60)
        elif isinstance(event, PybEvents.TimeoutEvent) and event.name == "many_complete":
            self.change_state(self.States.BURST)
            self.latency_comp[0].write({'state': 'burst'})
        elif isinstance(event, PybEvents.ComponentChangedEvent) and event.comp in self.latency_comp:
            self.many_latencies[event.comp.id].append(time.perf_counter() - event.metadata["t"])

    def BURST(self, event):
        if isinstance(event, PybEvents.StateEnterEvent):
            self.set_timeout("task_complete", self.burst_duration * 60)
        elif isinstance(event, PybEvents.ComponentChangedEvent) and event.comp in self.latency_comp:
            self.burst_latencies[event.comp.id].append(time.perf_counter() - event.metadata["t"])

    def plot(self):
        self.single_latencies = [x * 1000 for x in self.single_latencies]  # Convert to ms
        self.many_latencies = {k: [x * 1000 for x in v] for k, v in self.many_latencies.items()}
        self.burst_latencies = {k: [x * 1000 for x in v] for k, v in self.burst_latencies.items()}

        fig, axs = plt.subplots(3, 1, figsize=(10, 15))

        axs[0].hist(self.single_latencies, bins=20, color='blue')
        axs[0].set_title('Single Component Latencies')
        axs[0].set_xlabel('Latency (ms)')
        axs[0].set_ylabel('Frequency')

        # Function to plot for dictionary latencies
        def plot_latencies(ax, latencies, title):
            colors = plt.cm.viridis(np.linspace(0, 1, len(latencies)))
            for (comp_id, lat), color in zip(latencies.items(), colors):
                ax.hist(lat, bins=20, color=color, alpha=0.7, label=f'Component {comp_id}')
            ax.set_title(title)
            ax.set_xlabel('Latency (ms)')
            ax.set_ylabel('Frequency')
            ax.legend()

        plot_latencies(axs[1], self.many_latencies, 'Many Components Latencies')
        plot_latencies(axs[2], self.burst_latencies, 'Burst Latencies')
        plt.subplots_adjust(hspace=0.5)
        plt.show()
        