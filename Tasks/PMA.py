import random
from enum import Enum

from Components.BinaryInput import BinaryInput
from Components.Toggle import Toggle
from Components.TimedToggle import TimedToggle
from Components.Video import Video

from Events import PybEvents
from Tasks.Task import Task


class PMA(Task):
    """@DynamicAttrs"""
    class States(Enum):
        INTER_TONE_INTERVAL = 0
        TONE = 1
        SHOCK = 2
        POST_SESSION = 3

    @staticmethod
    def get_components():
        return {
            'food_lever': [BinaryInput],
            'cage_light': [Toggle],
            'food': [TimedToggle],
            'fan': [Toggle],
            'lever_out': [Toggle],
            'food_light': [Toggle],
            'shocker': [Toggle],
            'tone': [Toggle],
            'cam': [Video]
        }

    @staticmethod
    def get_constants():
        return {
            'ephys': False,
            'type': 'low',
            'random': True,
            'ntone': 20,
            'iti_min': 50,
            'iti_max': 150,
            'tone_duration': 30,
            'time_sequence': [96, 75, 79, 90, 80, 97, 88, 104, 77, 99, 102, 88, 101, 100, 96, 87, 78, 93, 89, 98],
            'shock_duration': 2,
            'post_session_time': 45,
            'dispense_time': 0.7
        }

    @staticmethod
    def get_variables():
        return {
            "cur_trial": 0,
            "presses": 0
        }

    def init_state(self):
        return self.States.INTER_TONE_INTERVAL, {"iti": self.iti_min + (self.iti_max - self.iti_min) * random.random() if self.random else self.time_sequence[self.cur_trial]}

    def start(self):
        self.cage_light.toggle(True)
        self.cam.start()
        self.fan.toggle(True)
        if self.type == 'low':
            self.lever_out.toggle(True)
            self.food_light.toggle(True)

    def stop(self):
        self.food_light.toggle(False)
        self.cage_light.toggle(False)
        self.fan.toggle(False)
        self.lever_out.toggle(False)
        self.shocker.toggle(False)
        self.tone.toggle(False)
        self.cam.stop()

    def all_states(self, event: PybEvents.PybEvent) -> bool:
        if isinstance(event, PybEvents.ComponentChangedEvent) and event.comp is self.food_lever and event.comp.state:
            self.food.toggle(self.dispense_time)
            self.presses += 1
            return True
        elif isinstance(event, PybEvents.GUIEvent) and event.name == "GUI_PELLET":
            self.food.toggle(self.dispense_time)
            return True
        return False

    def INTER_TONE_INTERVAL(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):
            self.set_timeout("iti", event.metadata["iti"])
        elif isinstance(event, PybEvents.TimeoutEvent) and event.name == "iti":
            self.change_state(self.States.TONE)

    def TONE(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):
            self.reward_available = True
            if not self.type == 'light':
                self.tone.toggle(True)
            if not self.type == 'low':
                self.lever_out.toggle(True)
                self.food_light.toggle(True)
            self.set_timeout("tone", self.tone_duration - self.shock_duration)
        elif isinstance(event, PybEvents.TimeoutEvent) and event.name == "tone":
            self.change_state(self.States.SHOCK)

    def SHOCK(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):
            if not self.type == 'light':
                self.shocker.toggle(True)
            self.set_timeout("shock", self.shock_duration)
        elif isinstance(event, PybEvents.TimeoutEvent) and event.name == "shock":
            self.cur_trial += 1
            if (self.random and self.cur_trial < self.ntone) or (not self.random and self.cur_trial < len(self.time_sequence)):
                self.change_state(self.States.INTER_TONE_INTERVAL, {"iti": self.iti_min + (self.iti_max - self.iti_min) * random.random() if self.random else self.time_sequence[self.cur_trial]})
            else:
                self.change_state(self.States.POST_SESSION)
        elif isinstance(event, PybEvents.StateExitEvent):
            self.shocker.toggle(False)
            self.tone.toggle(False)
            if not self.type == 'low':
                self.lever_out.toggle(False)
                self.food_light.toggle(False)

    def POST_SESSION(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):
            self.set_timeout("post", self.post_session_time)
        elif isinstance(event, PybEvents.TimeoutEvent) and event.name == "post":
            self.complete = True
