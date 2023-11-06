from enum import Enum

from Events import PybEvents
from Tasks.TaskSequence import TaskSequence
from .SetShift import SetShift
from .Raw import Raw


class TaskSequenceExample(TaskSequence):
    """@DynamicAttrs"""
    class States(Enum):
        PRE_RAW = 0
        SET_SHIFT = 1
        POST_RAW = 2

    @staticmethod
    def get_sequence_components():
        return {}

    @staticmethod
    def get_tasks():
        return [SetShift, Raw]

    # noinspection PyMethodMayBeStatic
    @staticmethod
    def get_constants():
        return {
            'set_shift_protocol': None,
            'pre_raw_protocol': None,
            'post_raw_protocol': None
        }
    
    def init_state(self):
        return self.States.PRE_RAW

    def init_sequence(self):
        return Raw, self.pre_raw_protocol

    def all_states(self, event):
        return False

    def PRE_RAW(self, event):
        if isinstance(event, PybEvents.TaskCompleteEvent):
            self.switch_task(SetShift, self.States.SET_SHIFT, self.set_shift_protocol, event.metadata)
            return True
        return False

    def SET_SHIFT(self, event):
        if isinstance(event, PybEvents.TaskCompleteEvent):
            self.switch_task(Raw, self.States.POST_RAW, self.post_raw_protocol, event.metadata)
            return True
        return False

    def POST_RAW(self, event):
        if isinstance(event, PybEvents.TaskCompleteEvent):
            self.complete = True
            return True
        return False
