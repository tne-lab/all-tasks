from enum import Enum

from Elements.BarPressElement import BarPressElement
from Elements.IndicatorElement import IndicatorElement
from Elements.SoundElement import SoundElement
from Elements.ShockElement import ShockElement
from Elements.ButtonElement import ButtonElement
from Elements.InfoBoxElement import InfoBoxElement
from Events import PybEvents
from GUIs.GUI import GUI


# noinspection PyAttributeOutsideInit
class PMAGUI(GUI):
    """@DynamicAttrs"""
    class Events(Enum):
        GUI_PELLET = 0

    def initialize(self):
        self.iti = 0
        self.lever = BarPressElement(self, 77, 25, 100, 90, comp=self.food_lever)
        self.feed_button = ButtonElement(self, 129, 170, 50, 20, "FEED")
        self.feed_button.mouse_up = lambda _: self.log_gui_event(self.Events.GUI_PELLET)
        self.presses_elem = InfoBoxElement(self, 69, 125, 50, 15, "PRESSES", 'BOTTOM', ['0'])
        self.pellets = InfoBoxElement(self, 129, 125, 50, 15, "PELLETS", 'BOTTOM', ['0'])
        self.ntone = InfoBoxElement(self, 242, 125, 50, 15, "NTONE", 'BOTTOM', ['0'])
        self.next_event = InfoBoxElement(self, 372, 125, 50, 15, "NEXT EVENT", 'BOTTOM', ['0'])
        self.time_in_task = InfoBoxElement(self, 372, 170, 50, 15, "TIME", 'BOTTOM', ['0'])
        self.reward_indicator = IndicatorElement(self, 74, 163, 15)
        self.reward_indicator.on = False
        self.tone_elem = SoundElement(self, 227, 25, 40, comp=self.tone)
        self.shocker_elem = ShockElement(self, 357, 25, 40, comp=self.shocker)

        return [self.feed_button, self.time_in_task, self.next_event, self.ntone, self.pellets, self.presses_elem, self.lever, self.reward_indicator, self.tone_elem, self.shocker_elem]

    def handle_event(self, event: PybEvents.PybEvent) -> None:
        super(PMAGUI, self).handle_event(event)
        self.time_in_task.set_text(str(round(self.time_elapsed / 60, 2)))
        if isinstance(event, PybEvents.StartEvent):
            if self.type != 'low':
                self.reward_indicator.on = False
            else:
                self.reward_indicator.on = True
            self.food.count = 0
            self.presses = 0
            self.cur_trial = 0
            self.pellets.set_text(str(self.food.count))
            self.presses_elem.set_text(str(self.presses))
            self.ntone.set_text(str(self.cur_trial))
        elif isinstance(event, PybEvents.ComponentUpdateEvent) and event.comp_id == self.food.id and event.value:
            self.food.count += 1
            self.pellets.set_text(str(self.food.count))
        elif isinstance(event, PybEvents.ComponentUpdateEvent) and event.comp_id == self.food_lever.id and event.value:
            self.presses += 1
            self.presses_elem.set_text(str(self.presses))
        elif isinstance(event, PybEvents.StateEnterEvent) and event.name == "TONE":
            self.iti = self.tone_duration - self.shock_duration
            self.reward_indicator.on = True
        elif isinstance(event, PybEvents.StateEnterEvent) and event.name == "SHOCK":
            self.iti = self.shock_duration
        elif isinstance(event, PybEvents.StateExitEvent) and event.name == "SHOCK":
            if self.type != 'low':
                self.reward_indicator.on = False
            self.cur_trial += 1
            self.ntone.set_text(str(self.cur_trial))
        elif isinstance(event, PybEvents.StateEnterEvent) and event.name == "INTER_TONE_INTERVAL":
            self.iti = event.metadata["iti"]
            self.next_event.set_text(str(round(self.iti)))

        self.next_event.set_text(str(max(0, round(self.iti-self.time_in_state))))
