
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
import queue
import time
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
start_trial_lever_press_time = 0.0
mean_dt = 0.1
dt_history = queue.Queue(10)
current_time: float
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
    global current_time

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

    state_machine = sm.StateMachine(no_mtt, mean_dt)

    initialise_man_target_trap_object()

    current_time = time.perf_counter()
    return True


def initialise_man_target_trap_object():
    global man_targ_trap

    if not no_mtt:
        man_targ_trap = mtt.MTT(variable_targets, max_distance_to_target, mean_dt, speed, must_lift_at_target)


def create_average_speed_of_levers_updating():
    global mean_dt
    global dt_history
    global current_time

    if dt_history.full():
        dt_history.get()
    dt_history.put(time.perf_counter() - current_time)

    mean_dt = np.mean(dt_history.queue)

    current_time = time.perf_counter()


def recalibrate_lever_press_time():
    global lever_press_time
    global start_trial_lever_press_time

    if lever_press_time == 0:
        start_trial_lever_press_time = 0
    if np.sign(lever_press_time) == np.sign(start_trial_lever_press_time) and \
            np.abs(lever_press_time) > np.abs(start_trial_lever_press_time):
        lever_press_time_from_end_of_last_trial = lever_press_time - start_trial_lever_press_time
    else:
        lever_press_time_from_end_of_last_trial = lever_press_time

    return lever_press_time_from_end_of_last_trial


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
    global start_trial_lever_press_time
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

    # Calculate the (running average) time it takes for the levers to push new data to this Node and update it for the
    # state_machine and the man_targ_trap objects that need it
    create_average_speed_of_levers_updating()
    state_machine.dt = mean_dt
    if not no_mtt:
        man_targ_trap.dt = mean_dt

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
        result = [np.array([ct.IGNORE]), np.array([ct.IGNORE]), np.array([ct.IGNORE])]
        return result

    if availability_on != prev_avail:
        #print(' ================ Availability = {}'.format(availability_on))
        prev_avail = availability_on

    if poke_on != prev_poke:
        #print(' ================ Poke = {}'.format(poke_on))
        prev_poke = poke_on

    command_to_vibration_arduino_controller = np.array(['d'])  # That means turn vibration off

    if not poke_on and not availability_on:
        if state_machine.current_state == state_machine.no_poke_no_avail:
            state_machine.running_around_no_availability_0()

        elif state_machine.current_state == state_machine.poke_no_avail:
            state_machine.leaving_poke_early_2()

        elif state_machine.current_state == state_machine.poke_avail:
            state_machine.too_long_in_poke_9()

        elif state_machine.current_state == state_machine.no_poke_avail:
            if state_machine.poke_timer < reward_on_poke_delay:
                state_machine.got_it_11()
            else:
                state_machine.too_long_running_around_10()

        elif state_machine.current_state == state_machine.failed:
            state_machine.initialise_after_fail_13()
            initialise_man_target_trap_object()

        elif state_machine.current_state == state_machine.succeeded:
            state_machine.initialise_after_success_14()
            initialise_man_target_trap_object()

    elif poke_on and not availability_on:
        if state_machine.current_state == state_machine.no_poke_no_avail:
            if not no_mtt:
                man_targ_trap.back_to_initial_positions()
                state_machine.man_targ_trap = man_targ_trap.positions_of_visuals
            state_machine.just_poked_1()

        # The state "Poke No Availability" (P_NA) is where most of the logic happens. Here is where the animal has to
        # either wait long enough (either looking at the manipulandum moving by itself (Stage 3) or not (Stage 2))
        # or manipulate the levers to reach the target (Stages 4 and 5)
        elif state_machine.current_state == state_machine.poke_no_avail:
            state_machine.waiting_in_poke_before_availability_3()

            if no_mtt:  # If the man., target, trap are invisible (Stage 2) ...
                if state_machine.poke_timer > reward_on_poke_delay:  # ... and the poke waiting time is up ...
                    availability_on = True
                    state_machine.availability_started_4()  # ... reward the animal.

            else:  # (Stages 3 to 5)
                if levers_state == 0:  # If the Levers are off (Stage 3) ...
                    #  ... update the position of the manipulandum.
                    state_machine.man_targ_trap = \
                        man_targ_trap.calculate_positions_for_auto_movement(state_machine.poke_timer,
                                                                            reward_on_poke_delay)
                    if state_machine.poke_timer > reward_on_poke_delay:  # If the poke waiting time is up ...
                        availability_on = True
                        state_machine.availability_started_4()  # ... reward the animal.

                else:  # If the Levers are on (being either on vibrate or on silent) (Stages 4 and 5)
                    lever_press_time_from_end_of_last_trial = recalibrate_lever_press_time()

                    state_machine.man_targ_trap = \
                        man_targ_trap.calculate_positions_for_levers_movement(lever_press_time_from_end_of_last_trial)
                    if levers_state == 1:  # If the levers state is On-Vibrating ...
                        # ... turn vibration on.
                        if man_targ_trap.up_or_down:
                            command_to_vibration_arduino_controller = np.array(['a'])
                        else:
                            command_to_vibration_arduino_controller = np.array(['s'])

                    if man_targ_trap.has_man_reached_target():  # If the man. reached the target ...
                        availability_on = True
                        state_machine.availability_started_4()  # ... reward the animal.
                    elif man_targ_trap.has_man_reached_trap():  # If the man. reached the trap ...
                        availability_on = False
                        start_trial_lever_press_time = lever_press_time
                        state_machine.fail_to_trap_15()  # ... start again.

        elif state_machine.current_state == state_machine.poke_avail:
            state_machine.too_long_in_poke_9()

        elif state_machine.current_state == state_machine.no_poke_avail:
            state_machine.too_long_running_around_10()

        elif state_machine.current_state == state_machine.failed:
            state_machine.poking_at_fail_12()
            initialise_man_target_trap_object()

    elif not poke_on and availability_on:
        if state_machine.current_state == state_machine.poke_avail:
            state_machine.leaving_poke_while_availability_6()

        elif state_machine.current_state == state_machine.no_poke_avail:
            state_machine.running_around_while_availability_8()

    elif poke_on and availability_on:
        if state_machine.current_state == state_machine.poke_avail:
            state_machine.waiting_in_poke_while_availability_5()

        elif state_machine.current_state == state_machine.no_poke_avail:
            state_machine.poking_again_while_availability_7()

    result = [state_machine.command_to_screens,
              state_machine.command_to_food_poke,
              command_to_vibration_arduino_controller]
    #print(' ooo Result = {}'.format(result))
    return result


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(work_function=experiment,
                                                          end_of_life_function=on_end_of_life,
                                                          initialisation_function=initialise)
    worker_object.start_ioloop()
