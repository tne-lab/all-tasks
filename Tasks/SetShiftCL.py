import collections
from enum import Enum

import numpy as np

from Components.Both import Both
from Components.Stimmer import Stimmer

from Events import PybEvents
from ..Tasks.SetShift import SetShift


class SetShiftCL(SetShift):
    """@DynamicAttrs"""
    class States(Enum):
        INITIATION = 0
        RESPONSE = 1
        INTER_TRIAL_INTERVAL = 2
        FIT_DELAY = 3

    @staticmethod
    def get_components():
        comps = super(SetShiftCL, SetShiftCL).get_components()
        comps['bayes'] = [Both]
        comps['stim'] = [Stimmer]
        return comps

    @staticmethod
    def get_constants():
        constants = super(SetShiftCL, SetShiftCL).get_constants()
        constants['fit'] = False
        constants['delay'] = 3.5
        constants['max_delay'] = 15
        constants['fit_delay'] = 5
        return constants

    @staticmethod
    def get_variables():
        variables = super(SetShiftCL, SetShiftCL).get_variables()
        variables['param_queue'] = collections.deque()
        variables['params'] = {'trial': 0, 'period': 7692, 'amp': 0, 'pw': 10}
        variables['delay_time'] = 0
        return variables

    def init_state(self):
        return self.States.FIT_DELAY

    def start(self):
        super(SetShiftCL, self).start()
        self.bayes.write({'command': 'initialize'})
        self.stim.parametrize(0, [1, 1], round(self.params['period']), 100000000000,
                              round(self.params['amp']) * np.array([[1, -1], [1, -1]]), round(self.params['pw']) * np.array([1, 1]))
        self.log_event(PybEvents.InfoEvent(self.metadata["chamber"], "STIM_CHANGE", 0, metadata=self.params))
        self.stim.start(0)

    def stop(self):
        super(SetShiftCL, self).stop()
        self.stim.parametrize(0, [1, 1], round(self.params['period']), 1000, round(self.params['amp']) * np.array([[-1, 1], [-1, 1]]),
                              round(self.params['pw']) * np.array([1, 1]))
        self.stim.start(0)
        self.bayes.write({'command': 'save'})

    def all_states(self, event: PybEvents.PybEvent) -> bool:
        if isinstance(event, PybEvents.ComponentChangedEvent) and event.comp is self.bayes:
            new_params = self.bayes.get_state()
            for params in new_params:
                self.param_queue.appendleft(params)
            return True
        return super(SetShiftCL, self).all_states(event)

    def FIT_DELAY(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):
            self.set_timeout("fit_delay", self.fit_delay)
        elif isinstance(event, PybEvents.TimeoutEvent) and event.name == "fit_delay":
            self.change_state(self.States.INTER_TRIAL_INTERVAL)

    def INITIATION(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):
            self.set_timeout("response_timeout", self.max_delay)
        elif isinstance(event, PybEvents.ComponentChangedEvent) and event.comp is self.nose_pokes[1] and event.comp:
            self.delay_time = self.time_in_state()
        elif isinstance(event, PybEvents.TimeoutEvent) and event.name == "response_timeout":
            self.bayes.write({'command': 'add_data', 'y': {'RT': None, 'Acc': False, 'DT': self.max_delay}, 'x': self.params})
            self.change_state(self.States.INTER_TRIAL_INTERVAL)
            return
        super(SetShiftCL, self).INITIATION(event)

    def INTER_TRIAL_INTERVAL(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):
            self.set_timeout("stim_change", self.delay)
        elif isinstance(event, PybEvents.TimeoutEvent) and event.name == "stim_change":
            if len(self.param_queue) > 0:
                temp = self.param_queue.pop()
                print(temp)
                self.params.update(temp)
            self.stim.parametrize(0, [1, 1], round(self.params['period']), 100000000000, round(self.params['amp']) * np.array([[1, -1], [1, -1]]),
                                  [round(self.params['pw'])] * 2)
            self.log_event(PybEvents.InfoEvent(self.metadata["chamber"], "STIM_CHANGE", 0, metadata=self.params))
        super(SetShiftCL, self).INTER_TRIAL_INTERVAL(event)

    def RESPONSE(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.ComponentChangedEvent) and (
                event.comp is self.nose_pokes[0] or event.comp is self.nose_pokes[2]) and event.comp:
            if self.cur_trial < self.n_random_start or self.cur_trial >= self.n_random_start + self.correct_to_switch * len(
                    self.rule_sequence):
                acc = None
            else:
                if self.rule_sequence[self.cur_rule] == 0:
                    acc = (event.comp is self.nose_pokes[0] and not self.light_sequence[self.cur_trial]) or (
                            event.comp is self.nose_pokes[2] and self.light_sequence[self.cur_trial])
                elif self.rule_sequence[self.cur_rule] == 1:
                    acc = event.comp is self.nose_pokes[0]
                else:
                    acc = event.comp is self.nose_pokes[2]
            self.bayes.write({'command': 'add_data', 'y': {'RT': None if self.time_in_state() > self.response_duration else self.time_in_state(),
                                                           'Acc': acc, 'DT': self.delay_time}, 'x': self.params})
        elif isinstance(event, PybEvents.TimeoutEvent) and event.name == "response_timeout":
            self.bayes.write({'command': 'add_data', 'y': {'RT': None, 'Acc': False, 'DT': self.delay_time}, 'x': self.params})
        super(SetShiftCL, self).RESPONSE(event)
