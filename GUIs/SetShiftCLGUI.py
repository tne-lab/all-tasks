from enum import Enum

from Elements.ButtonElement import ButtonElement
from Elements.InfoBoxElement import InfoBoxElement
from Events import PybEvents
from ..GUIs.SetShiftGUI import SetShiftGUI


class SetShiftCLGUI(SetShiftGUI):

    class EventsCL(Enum):
        GUI_ABORT = 1

    def initialize(self):
        elements = super().initialize()
        self.amp = InfoBoxElement(self, 200, 250, 100, 30, "AMP", 'BOTTOM', ['0'], f_size=28)
        self.pw = InfoBoxElement(self, 200, 330, 100, 30, "PW", 'BOTTOM', ['0'], f_size=28)
        self.abort_button = ButtonElement(self, 200, 610, 100, 40, "ABORT", f_size=28)
        self.abort_button.mouse_up = lambda _: self.abort()
        return elements + [self.amp, self.pw, self.abort_button]

    def abort(self):
        self.amp.set_text("0")
        self.log_gui_event(self.EventsCL.GUI_ABORT)

    def handle_event(self, event: PybEvents.PybEvent) -> None:
        super().handle_event(event)
        if isinstance(event, PybEvents.TimeoutEvent) and event.name == "init_timeout":
            self.amp.set_text("0")
        elif isinstance(event, PybEvents.InfoEvent):
            self.amp.set_text(str(round(event.metadata["amp"])))
            self.pw.set_text((str(round(event.metadata["pw"]))))
