import math
import random
from typing import Any

import numpy as np

from Sources.Source import Source
from Tasks.TimeoutManager import TimeoutManager, Timeout


class SetShiftSimSource(Source):

    def __init__(self, lr: float, temp: float):
        super().__init__()
        self.values = [0.33, 0.33, 0.33]
        self.lr = float(lr)
        self.temp = float(temp)
        self.choice = []
        self.amp = 0
        self.pw = 10
        self.tm = None

    def initialize(self):
        self.tm = TimeoutManager()
        self.tm.start()

    def write_component(self, component_id: str, msg: Any) -> None:
        if component_id.startswith('stim'):
            # save current parameters
            if msg.startswith('F'):
                parts = msg.split(';')[1].split(',')
                self.amp = abs(int(parts[0]))
                self.pw = int(parts[2])
        elif component_id.startswith('nose_poke_lights-' + str(self.component_chambers[component_id]) + '-1') and msg:
            # initiation light turned on
            # generate delay time response
            if len(self.choice) > 0:
                for f in self.choice:
                    self.values[f] -= self.lr * self.values[f]
                self.choice = []
            pid = 'nose_pokes-' + str(self.component_chambers[component_id]) + '-1'
            self.tm.add_timeout(Timeout(pid, 0, math.exp(0.0215 + self.amp * self.pw / 20000 + 1.5182 * np.random.normal()), self.poke, [pid]))
        elif component_id.startswith('nose_poke_lights') and msg:
            # side light turned on
            # choose based on RL
            # Generate actual choice and RT based on stim model
            v_left = self.values[0]
            v_right = self.values[1]
            if component_id.startswith('nose_poke_lights-' + str(self.component_chambers[component_id]) + '-0'):
                v_left += self.values[2]
            else:
                v_right += self.values[2]
            p_correct = 0.7 + 0.3 * math.exp(-(((self.amp - 250) / 100) ** 2 + ((self.pw - 50) / 100) ** 2))
            p_left = math.exp(v_left / self.temp) / (math.exp(v_left / self.temp) + math.exp(v_right / self.temp))
            choose_s_max = random.random() < p_correct
            if (choose_s_max and random.random() < p_left) or (not choose_s_max and random.random() < 0.5):
                self.choice.append(0)
                if component_id.startswith('nose_poke_lights-' + str(self.component_chambers[component_id]) + '-0'):
                    self.choice.append(2)
                pid = 'nose_pokes-' + str(self.component_chambers[component_id]) + '-0'
            else:
                self.choice.append(1)
                if component_id.startswith('nose_poke_lights-' + str(self.component_chambers[component_id]) + '-2'):
                    self.choice.append(2)
                pid = 'nose_pokes-' + str(self.component_chambers[component_id]) + '-2'
            rt = 0.733 - 0.4 * math.exp(-(((self.amp - 300) / 100) ** 2 + ((self.pw - 100) / 100) ** 2) + 0.4231 * np.random.normal())
            if rt < 3:
                self.tm.add_timeout(Timeout(pid, 0, rt, self.poke, [pid]))
        elif component_id.startswith("food") and msg:
            # reward was received
            for f in self.choice:
                self.values[f] += self.lr * (1 - self.values[f])
            self.choice = []

    def poke(self, pid):
        self.update_component(pid, True)
        self.tm.add_timeout(Timeout(pid, 0, 0.2, self.update_component, (pid, False)))
