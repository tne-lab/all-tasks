from Elements.IndicatorElement import IndicatorElement
from Events import PybEvents
from Local.GUIs.SetShiftGUI import SetShiftGUI


# noinspection PyAttributeOutsideInit
class SetShiftPRGUI(SetShiftGUI):
    """@DynamicAttrs"""

    def initialize(self):
        elements = super(SetShiftPRGUI, self).initialize()
        self.stim_indicator = IndicatorElement(self, 50, 465, 25)
        self.stim_indicator.on = False
        return [self.stim_indicator, *elements]

    def handle_event(self, event: PybEvents.PybEvent) -> None:
        super(SetShiftPRGUI, self).handle_event(event)
        if isinstance(event, PybEvents.InfoEvent):
            self.stim_indicator.on = event.value
