from enum import Enum

from Elements.CircleLightElement import CircleLightElement
from Elements.NosePokeElement import NosePokeElement
from Elements.ButtonElement import ButtonElement
from Elements.InfoBoxElement import InfoBoxElement
from Events import PybEvents
from GUIs.GUI import GUI


# noinspection PyAttributeOutsideInit
class SetShiftGUI(GUI):
    """@DynamicAttrs"""

    class Events(Enum):
        GUI_PELLET = 0

    def initialize(self):
        self.np_lights = []
        self.np_inputs = []

        for i in range(3):
            npl = CircleLightElement(self, 50 + (i + 1) * (25 + 60), 60, 30, comp=self.nose_poke_lights[i])
            self.np_lights.append(npl)
            npi = NosePokeElement(self, 50 + (i + 1) * (25 + 60), 150, 30, comp=self.nose_pokes[i])
            self.np_inputs.append(npi)

        self.feed_button = ButtonElement(self, 200, 530, 100, 40, "FEED", f_size=28)
        self.feed_button.mouse_up = lambda _: self.log_gui_event(self.Events.GUI_PELLET)
        self.pellets = InfoBoxElement(self, 200, 440, 100, 30, "PELLETS", 'BOTTOM', ['0'], f_size=28)
        self.rule = InfoBoxElement(self, 375, 440, 100, 30, "RULE", 'BOTTOM', ['RANDOM'], f_size=24)
        self.time_in_trial = InfoBoxElement(self, 375, 600, 100, 30, "TIME", 'BOTTOM', ['0'], f_size=28)
        self.trial_count = InfoBoxElement(self, 375, 520, 100, 30, "TRIAL", 'BOTTOM', ['1'], f_size=28)

        return [*self.np_lights, *self.np_inputs, self.feed_button, self.pellets, self.time_in_trial, self.trial_count,
                self.rule]

    def handle_event(self, event: PybEvents.PybEvent) -> None:
        super(SetShiftGUI, self).handle_event(event)
        self.time_in_trial.set_text(str(round(self.time_elapsed / 60, 2)))
        if isinstance(event, PybEvents.StartEvent):
            self.food.count = 0
            self.pellets.set_text(str(self.food.count))
            self.rule.set_text("RANDOM")
            self.trial_count.set_text("1")
        elif isinstance(event, PybEvents.ComponentUpdateEvent) and event.comp_id == self.food.id and event.value:
            self.food.count += 1
            self.pellets.set_text(str(self.food.count))
        elif isinstance(event, PybEvents.StateExitEvent) and event.name == "RESPONSE":
            rules = ["LIGHT", "FRONT", "REAR", "RANDOM"]
            if self.cur_trial < self.n_random_start or self.cur_trial >= self.n_random_start + self.correct_to_switch * len(
                    self.rule_sequence):
                self.cur_trial += 1
            else:
                if event.metadata["accuracy"] == "correct":
                    if self.cur_block + 1 == self.correct_to_switch:
                        self.cur_rule += 1
                        self.cur_block = 0
                    else:
                        self.cur_block += 1
                    self.cur_trial += 1
                else:
                    self.cur_trial -= self.cur_block
                    self.cur_block = 0
            self.trial_count.set_text(str(self.cur_trial + 1))
            if self.cur_trial < self.n_random_start or self.cur_trial >= self.n_random_start + self.correct_to_switch * len(
                    self.rule_sequence):
                self.rule.set_text("RANDOM")
            else:
                self.rule.set_text(rules[self.rule_sequence[self.cur_rule]])
