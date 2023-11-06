from enum import Enum

import random

from Components.BinaryInput import BinaryInput
from Components.Toggle import Toggle
from Components.TimedToggle import TimedToggle
from Components.Video import Video

from Events import PybEvents
from Tasks.Task import Task


class BarPress(Task):
    """@DynamicAttrs"""
    class States(Enum):
        REWARD_AVAILABLE = 0
        REWARD_UNAVAILABLE = 1

    @staticmethod
    def get_components():
        return {
            'food_lever': [BinaryInput],
            'cage_light': [Toggle],
            'food': [TimedToggle],
            'fan': [Toggle],
            'lever_out': [Toggle],
            'food_light': [Toggle],
            'cam': [Video]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'duration': 40,
            'reward_lockout': False,
            'reward_lockout_min': 25,
            'reward_lockout_max': 35,
            'dispense_time': 0.7
        }

    def init_state(self):
        return self.States.REWARD_AVAILABLE

    def start(self):
        self.set_timeout("task_complete", self.duration * 60, end_with_state=False)
        self.cage_light.toggle(True)
        self.cam.start()
        self.fan.toggle(True)
        self.lever_out.toggle(True)
        self.food_light.toggle(True)

    def stop(self):
        self.food_light.toggle(False)
        self.cage_light.toggle(False)
        self.fan.toggle(False)
        self.lever_out.toggle(False)
        self.cam.stop()

    def all_states(self, event: PybEvents.PybEvent) -> bool:
        if isinstance(event, PybEvents.TimeoutEvent) and event.name == "task_complete":
            self.complete = True
            return True
        elif isinstance(event, PybEvents.GUIEvent) and event.event == "GUI_PELLET":
            self.food.toggle(self.dispense_time)
            return True
        return False

    def REWARD_AVAILABLE(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.ComponentChangedEvent) and event.comp == self.food_lever and event.comp.state:
            self.food.toggle(self.dispense_time)
            if self.reward_lockout:
                self.change_state(self.States.REWARD_UNAVAILABLE)

    def REWARD_UNAVAILABLE(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):
            self.set_timeout("lockout", self.reward_lockout_min + random.random() * (self.reward_lockout_max - self.reward_lockout_min))
        elif isinstance(event, PybEvents.TimeoutEvent) and event.name == "lockout":
            self.change_state(self.States.REWARD_AVAILABLE)
