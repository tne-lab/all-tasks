import math
from types import MethodType
from typing import List

from Elements.Element import Element
from Elements.FanElement import FanElement
from GUIs import Colors
from GUIs.GUI import GUI

from Elements.InfoBoxElement import InfoBoxElement
from Events import PybEvents

class RawGUI(GUI):
    """@DynamicAttrs"""

    def initialize(self) -> List[Element]:
        self.fan = FanElement(self, 210, 20, 40, comp=self.fan)
        self.ne = InfoBoxElement(self, 372, 125, 50, 15, "NEXT EVENT", 'BOTTOM', ['0'])
        return [self.fan, self.ne]

    def handle_event(self, event: PybEvents.PybEvent) -> None:
        super(RawGUI, self).handle_event(event)
        self.ne.set_text(str(round(60 * self.duration - self.time_elapsed, 2)))