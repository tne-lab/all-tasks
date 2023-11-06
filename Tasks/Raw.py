from enum import Enum

from Events import PybEvents
from Tasks.Task import Task
from Components.Toggle import Toggle


class Raw(Task):
    """@DynamicAttrs"""
    class States(Enum):
        ACTIVE = 0

    @staticmethod
    def get_components():
        return {
            "fan": [Toggle],
            "house_light": [Toggle]
        }

    # noinspection PyMethodMayBeStatic
    @staticmethod
    def get_constants():
        return {
            'duration': 10/60
        }

    def init_state(self):
        return self.States.ACTIVE
    
    def start(self):
        self.fan.toggle(True)
        self.set_timeout("task_complete", self.duration * 60, end_with_state=False)

    def stop(self):
        self.fan.toggle(False)

    def all_states(self, event: PybEvents.PybEvent) -> bool:
        if isinstance(event, PybEvents.TimeoutEvent) and event.name == "task_complete":
            self.complete = True
            return True
        return False
    
    def ACTIVE(self, event):
        pass
