
import numpy as np
import config as cfg
from statemachine import StateMachine, State
from Heron import constants as ct


class RewardOnPokeStateMachine(StateMachine):
    number_of_pellets = cfg.number_of_pellets
    reward_on_poke_delay = cfg.reward_on_poke_delay

    print(number_of_pellets, reward_on_poke_delay)

    command_to_screens = np.array(['Cue=0, Manipulandum=0, Target=0, Trap=0'])
    command_to_food_poke = np.array([ct.IGNORE])
    poke_timer = 0

    constant_to_update_poke_without_starting_trial = -1
    
    # States
    no_poke_no_avail = State("NP_NA", initial=True)
    poke_no_avail = State("P_NA")
    poke_avail = State("P_A")
    no_poke_avail = State("P_NA")
    failed = State("F")
    succeeded = State("S")
    
    #Transitions
    running_around_no_availability_0 = no_poke_no_avail.to(no_poke_no_avail)
    just_poked_1 = no_poke_no_avail.to(poke_no_avail)
    leaving_poke_early_2 = poke_no_avail.to(no_poke_no_avail)
    waiting_in_poke_before_availability_3 = poke_no_avail.to(poke_no_avail)
    availability_started_4 = poke_no_avail.to(poke_avail)
    waiting_in_poke_while_availability_5 = poke_avail.to(poke_avail)
    leaving_poke_while_availability_6 = poke_avail.to(no_poke_avail)
    poking_again_while_availability_7 = no_poke_avail.to(poke_avail)
    running_around_while_availability_8 = no_poke_avail.to(no_poke_avail)
    too_long_in_poke_9 = poke_avail.to(failed)
    too_long_running_around_10 = no_poke_avail.to(failed)
    got_it_11 = no_poke_avail.to(succeeded)
    poking_at_fail_12 = failed.to(poke_no_avail)
    initialise_after_fail_13 = failed.to(no_poke_no_avail)
    initialise_after_success_14 = succeeded.to(no_poke_no_avail)

    def on_running_around_no_availability_0(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer = 0

    def on_just_poked_1(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer += 0.1
        #print('ooo Just poked')

    def on_leaving_poke_early_2(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer = 0
        #print('ooo Left too early')

    def on_waiting_in_poke_before_availability_3(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer += 0.1

    def on_availability_started_4(self):
        self.command_to_screens = np.array(['Cue=1, Manipulandum=0, Target=0, Trap=0'])
        self.command_to_food_poke = np.array([cfg.number_of_pellets])
        self.poke_timer = 0
        #print('ooo Availability started')

    def on_waiting_in_poke_while_availability_5(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer = 0

    def on_leaving_poke_while_availability_6(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer = 0
        #print('ooo Pulled while Availability is on')

    def on_poking_again_while_availability_7(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer = 0
        #print('ooo Re poked while availability is on')

    def on_running_around_while_availability_8(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer = 0

    def on_too_long_in_poke_9(self):
        self.command_to_screens = np.array(['Cue=0, Manipulandum=0, Target=0, Trap=0'])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer = 0
        #print('ooo Did not pull out fast enough')

    def on_too_long_running_around_10(self):
        self.command_to_screens = np.array(['Cue=0, Manipulandum=0, Target=0, Trap=0'])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer = 0
        #print('ooo Run around too long')

    def on_got_it_11(self):
        self.command_to_screens = np.array(['Cue=0, Manipulandum=0, Target=0, Trap=0'])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer = 0
        #print('ooo GOT IT')

    def on_poking_at_fail_12(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer += 0.1
        #print('ooo Back in poke from Fail')

    def on_initialise_after_fail_13(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer = 0
        #print('ooo Start again from Fail')

    def on_initialise_after_success_14(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        self.poke_timer = 0
        #print('ooo Start again after Success')