from pygame import Surface

from Elements.InfoBoxElement import InfoBoxElement
from Events import PybEvents
from GUIs.SequenceGUI import SequenceGUI
from Workstation.Workstation import Workstation


class TaskSequenceExampleGUI(SequenceGUI):
    def initialize(self):
        self.ec = InfoBoxElement(self, 200, 700, 100, 30, "SESSION TIME", 'BOTTOM', ['0'], f_size=28)
        return [self.ec]

    def handle_event(self, event: PybEvents.PybEvent):
        super().handle_event(event)
        self.ec.set_text(str(round(self.time_elapsed / 60, 2)))
