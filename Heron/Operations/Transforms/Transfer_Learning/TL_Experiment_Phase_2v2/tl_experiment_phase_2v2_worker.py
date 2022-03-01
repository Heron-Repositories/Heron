
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
import copy
from statemachine import StateMachine
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron import constants as ct
import config as cfg
import state_machine as sm
import man_targ_trap as mtt

no_mtt: bool
reward_on_poke_delay: float
levers_state: int  # 0 = Off, 1 = On-Vibrating, 2 = On-Silent
max_distance_to_target: int
speed: float
variable_targets: bool
must_lift_at_target: bool
number_of_pellets: int
availability_on = False
poke_on = False
prev_avail = True
prev_poke = True
lever_press_time = 0.0
dt = 0.1  # This comes from the TL Levers Node where the arduino code that controls the arduino that reads the levers
          # updates every 0.1s and thus the TL Levers Node drives the system at that speed

state_machine: StateMachine
man_targ_trap: mtt.MTT


def initialise(_worker_object):
    global no_mtt
    global reward_on_poke_delay
    global levers_state
    global max_distance_to_target
    global speed
    global variable_targets
    global must_lift_at_target
    global number_of_pellets
    global worker_object
    global availability_on
    global state_machine
    global man_targ_trap

    levers_states_dict = {'Off': 0, 'On-Vibrating': 1, 'On-Silent': 2}
    try:
        parameters = _worker_object.parameters
        no_mtt = parameters[0]
        reward_on_poke_delay = parameters[1]
        levers_state = levers_states_dict[parameters[2]]
        max_distance_to_target = parameters[3]
        speed = parameters[4]
        variable_targets = parameters[5]
        must_lift_at_target = parameters[6]
        number_of_pellets = parameters[7]
    except Exception as e:
        print(e)
        return False

    cfg.reward_on_poke_delay = reward_on_poke_delay
    cfg.number_of_pellets = number_of_pellets

    state_machine = sm.StateMachine(no_mtt, dt)

    if not no_mtt:
        man_targ_trap = mtt.MTT(variable_targets, max_distance_to_target, dt)

    return True


def experiment(data, parameters):
    global no_mtt
    global reward_on_poke_delay
    global levers_state
    global speed
    global variable_targets
    global number_of_pellets
    global availability_on
    global poke_on
    global lever_press_time
    global state_machine
    global prev_avail
    global prev_poke
    global man_targ_trap

    try:
        reward_on_poke_delay = parameters[1]
        speed = parameters[4]
        number_of_pellets = parameters[7]
    except:
        pass

    topic = data[0].decode('utf-8')
    message = data[1:]
    message = Socket.reconstruct_array_from_bytes_message(message)

    if 'Levers_Box_In' in topic:
        # The first element of the array is whether the rat is in the poke. The second is the milliseconds it has been
        # pressing either the left or the right lever (one is positive the other negative). If it is 0 then the rat is
        # not pressing a lever
        poke_on = message[0]
        lever_press_time = message[1]
    if 'Food_Poke_Update' in topic:
        availability_on = message[0]
        #print('GOT NEW AVAILABILITY = {}'.format(availability_on))
        result = [np.array([ct.IGNORE]), np.array([ct.IGNORE])]
        return result

    if availability_on != prev_avail:
        #print(' ================ Availability = {}'.format(availability_on))
        prev_avail = availability_on

    if poke_on != prev_poke:
        #print(' ================ Poke = {}'.format(poke_on))
        prev_poke = poke_on

    #print(state_machine.current_state, availability_on)

    if not poke_on and not availability_on:
        #print('A')
        if state_machine.current_state == state_machine.no_poke_no_avail:
            state_machine.running_around_no_availability_0()

        elif state_machine.current_state == state_machine.poke_no_avail:
            state_machine.leaving_poke_early_2()
            if not no_mtt:
                man_targ_trap.back_to_initial_positions()

        elif state_machine.current_state == state_machine.poke_avail:
            state_machine.too_long_in_poke_9()

        elif state_machine.current_state == state_machine.no_poke_avail:
            if state_machine.poke_timer < reward_on_poke_delay:
                state_machine.got_it_11()
            else:
                state_machine.too_long_running_around_10()

        elif state_machine.current_state == state_machine.failed:
            state_machine.initialise_after_fail_13()

        elif state_machine.current_state == state_machine.succeeded:
            state_machine.initialise_after_success_14()

    elif poke_on and not availability_on:
        #print('B')
        if state_machine.current_state == state_machine.no_poke_no_avail:
            state_machine.just_poked_1()

        elif state_machine.current_state == state_machine.poke_no_avail:
            state_machine.waiting_in_poke_before_availability_3()
            if levers_state == 0:  # If the Levers are Off ...
                if not no_mtt:  # and the man., target and trap are visible (so they move automatically)
                    #  Update the position of the manipulandum
                    state_machine.man_targ_trap = \
                        man_targ_trap.calculate_positions_for_auto_movement(state_machine.poke_timer,
                                                                            reward_on_poke_delay)
                if state_machine.poke_timer > reward_on_poke_delay:
                    state_machine.availability_started_4()
                    #print('!!!!!!!!!!! {}'.format([state_machine.command_to_screens, state_machine.command_to_food_poke]))
                    availability_on = True
                    if not no_mtt:
                        man_targ_trap = mtt.MTT(variable_targets, max_distance_to_target, dt)

        elif state_machine.current_state == state_machine.poke_avail:
            state_machine.too_long_in_poke_9()

        elif state_machine.current_state == state_machine.no_poke_avail:
            state_machine.too_long_running_around_10()

        elif state_machine.current_state == state_machine.failed:
            state_machine.poking_at_fail_12()

    elif not poke_on and availability_on:
        #print('C')
        if state_machine.current_state == state_machine.poke_avail:
            state_machine.leaving_poke_while_availability_6()

        elif state_machine.current_state == state_machine.no_poke_avail:
            state_machine.running_around_while_availability_8()

    elif poke_on and availability_on:
        #print('D')
        if state_machine.current_state == state_machine.poke_avail:
            state_machine.waiting_in_poke_while_availability_5()

        elif state_machine.current_state == state_machine.no_poke_avail:
            state_machine.poking_again_while_availability_7()

    result = [state_machine.command_to_screens, state_machine.command_to_food_poke]
    #print(result, state_machine.current_state)
    return result


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(work_function=experiment,
                                                          end_of_life_function=on_end_of_life,
                                                          initialisation_function=initialise)
    worker_object.start_ioloop()
