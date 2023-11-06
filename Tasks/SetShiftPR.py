import itertools
import random

import numpy as np

from Events import PybEvents
from Local.Tasks.SetShift import SetShift


class SetShiftPR(SetShift):

    @staticmethod
    def get_constants():
        constants = super(SetShiftPR, SetShiftPR).get_constants()
        constants["n_random_start"] = 0
        constants["n_random_end"] = 0
        constants["run_lengths"] = [1, 3, 5, 7, 9]
        constants["n_run"] = 3
        constants['delay'] = 3.5
        return constants

    @staticmethod
    def get_variables():
        variables = super(SetShiftPR, SetShiftPR).get_variables()
        variables["trial_sequence"] = []
        variables["stimming"] = False
        variables["trial_index"] = 0
        return variables

    def start(self):
        all_on = self.run_lengths * self.n_run
        all_off = self.run_lengths * self.n_run
        random.shuffle(all_on)
        random.shuffle(all_off)
        all_settings = [None] * (len(all_on) * 2)
        all_settings[::2] = all_off
        all_settings[1::2] = all_on
        self.trial_sequence = list(itertools.chain.from_iterable([[i % 2] * x for i, x in enumerate(all_settings)]))
        self.cam.start()
        self.set_timeout("task_complete", self.max_duration * 60, end_with_state=False)
        self.chamber_light.toggle(False)
        self.stim.parametrize(0, [1, 1], round(self.params['period']), 100000000000,
                              0 * np.array([[-1, 1], [-1, 1]]),
                              0 * np.array([1, 1]))
        self.stim.start(0)

    def INTER_TRIAL_INTERVAL(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):
            if self.stimming != self.trial_sequence[self.trial_index]:
                self.set_timeout("stim_change", self.delay)
        elif isinstance(event, PybEvents.TimeoutEvent) and event.name == "stim_change":
            if self.trial_sequence[self.trial_index]:
                self.stim.update_parameters(round(self.params['period']), round(self.params['amp']) * np.array([[-1, 1], [-1, 1]]),
                                            [round(self.params['pw'])] * 2)
            else:
                self.stim.update_parameters(round(self.params['period']),
                                            0 * np.array([[-1, 1], [-1, 1]]),
                                            [0] * 2)
            self.stimming = self.trial_sequence[self.trial_index]
            self.log_event(PybEvents.InfoEvent(self.metadata["chamber"], "STIM_CHANGE", self.stimming))
        super(SetShiftPR, self).INTER_TRIAL_INTERVAL(event)

    def INITIATION(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):
            self.nose_poke_lights[1].toggle(True)
        elif isinstance(event, PybEvents.ComponentChangedEvent) and event.comp is self.nose_pokes[1] and event.comp:
            self.change_state(self.States.RESPONSE, {"light_location": self.light_sequence[self.cur_trial % (len(self.light_sequence))]})
        elif isinstance(event, PybEvents.StateExitEvent):
            self.nose_poke_lights[1].toggle(False)

    def RESPONSE(self, event: PybEvents.PybEvent):
        metadata = {}
        if isinstance(event, PybEvents.StateEnterEvent):
            self.nose_poke_lights[2 * self.light_sequence[self.cur_trial % len(self.light_sequence)]].toggle(True)
            self.set_timeout("response_timeout", self.response_duration)
        elif isinstance(event, PybEvents.ComponentChangedEvent) and (event.comp is self.nose_pokes[0] or event.comp is self.nose_pokes[2]) and event.comp:
            metadata["rule"] = self.rule_sequence[self.cur_rule % len(self.rule_sequence)]
            metadata["cur_block"] = self.cur_block
            metadata["rule_index"] = self.cur_rule
            if self.rule_sequence[self.cur_rule % len(self.rule_sequence)] == 0:
                if (event.comp is self.nose_pokes[0] and not self.light_sequence[self.cur_trial % len(self.light_sequence)]) or (
                        event.comp is self.nose_pokes[2] and self.light_sequence[self.cur_trial % len(self.light_sequence)]):
                    self.correct()
                    metadata["accuracy"] = "correct"
                else:
                    self.cur_trial -= self.cur_block
                    self.cur_block = 0
                    metadata["accuracy"] = "incorrect"
            elif self.rule_sequence[self.cur_rule % len(self.rule_sequence)] == 1:
                if event.comp is self.nose_pokes[0]:
                    self.correct()
                    metadata["accuracy"] = "correct"
                else:
                    self.cur_trial -= self.cur_block
                    self.cur_block = 0
                    metadata["accuracy"] = "incorrect"
            elif self.rule_sequence[self.cur_rule % len(self.rule_sequence)] == 2:
                if event.comp is self.nose_pokes[2]:
                    self.correct()
                    metadata["accuracy"] = "correct"
                else:
                    self.cur_trial -= self.cur_block
                    self.cur_block = 0
                    metadata["accuracy"] = "incorrect"
            self.trial_index += 1
            self.change_state(self.States.INTER_TRIAL_INTERVAL, metadata)
        elif isinstance(event, PybEvents.TimeoutEvent) and event.name == "response_timeout":
            self.cur_trial -= self.cur_block
            self.cur_block = 0
            metadata["rule"] = self.rule_sequence[self.cur_rule % len(self.rule_sequence)]
            metadata["cur_block"] = self.cur_block
            metadata["rule_index"] = self.cur_rule
            metadata["accuracy"] = "incorrect"
            metadata["response"] = "none"
            self.trial_index += 1
            self.change_state(self.States.INTER_TRIAL_INTERVAL, metadata)
        elif isinstance(event, PybEvents.StateExitEvent):
            self.nose_poke_lights[0].toggle(False)
            self.nose_poke_lights[2].toggle(False)

    def is_complete(self):
        return self.trial_index == len(self.trial_sequence)
