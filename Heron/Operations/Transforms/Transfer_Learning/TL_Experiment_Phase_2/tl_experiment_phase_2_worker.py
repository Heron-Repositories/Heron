
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import copy
import numpy as np
from enum import Enum
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron import constants as ct

no_mtt: bool
reward_on_poke_delay: float
levers_state: bool
trap_on: bool
max_distance_to_target: int
speed: float
variable_targets: bool
must_lift_at_target: bool

angles_of_visuals: np.empty(4)  # 0th number is if any lever is pressed, 1st is the angle of the manipulandum, 2nd and
# 3rd the angles of the target and trap respectively
initial_angle_of_manipulandum: int
up_or_down: bool


class ExperimentState(Enum):
    PokeOut = 1
    PokeIn_Running = 2
    PokeIn_OnTarget = 3
    PokeIn_Finished_Sucess = 4
    PokeIn_Finished_Failure = 5


experiment_state = ExperimentState.PokeOut
number_of_pellets = 1

# When an animal takes its snout out of poke then the experiment counts how many time steps
# of 100 ms the animal is out of poke. If that number crosses a threshold then the trial aborts.
# VERY IMPORTANT!! This assumes the TL_Levers is sending commands every 100ms. If this changes (in the arduino .ino)
# then this number and its comparisons should change to keep times the same!!
_100ms_time_steps_counter = 20

# When the manipulandum reaches the target then the animal must release the lever. This variable holds
# how many time steps of 100 ms the manipulandum has remained unmoving on target and reward is provided only if this
# crosses a threshold
on_target = 0

time_on_target = 5
error = 3


def initialise(_worker_object):
    global no_mtt
    global reward_on_poke_delay
    global levers_state
    global trap_on
    global max_distance_to_target
    global speed
    global variable_targets
    global must_lift_at_target
    global number_of_pellets
    global worker_object

    try:
        parameters = _worker_object.parameters
        reward_on_poke = parameters[0]
        reward_on_poke_delay = parameters[1]
        trap_on = parameters[2]
        max_distance_to_target = parameters[3]
        speed = parameters[4]
        variable_targets = parameters[5]
        must_lift_at_target = parameters[6]
        number_of_pellets = parameters[7]
    except Exception as e:
        print(e)
        return False

    return True


def initialise_trial():
    global variable_targets
    global initial_angle_of_manipulandum
    global angles_of_visuals

    if variable_targets:
        manipulandum, target, trap = initialise_trial_with_variable_target_trap()
    else:
        manipulandum, target, trap = initialise_trial_with_constant_target_trap()

    initial_angle_of_manipulandum = manipulandum
    angles_of_visuals = np.array([0, manipulandum, target, trap])
    angles_of_visuals = angles_of_visuals - np.max(angles_of_visuals[1:])
    initial_angle_of_manipulandum = copy.copy(angles_of_visuals[1])
    angles_of_visuals[0] = 0


def initialise_trial_with_variable_target_trap():
    global angles_of_visuals
    global max_distance_to_target
    global up_or_down
    global experiment_state

    manipulandum = np.random.randint(-80, -9)
    up_or_down = np.random.binomial(n=1, p=0.5)

    if up_or_down:
        target = np.random.randint(manipulandum + 11, np.min([manipulandum + max_distance_to_target + 12, 0]))
        trap = np.random.randint(-90, manipulandum - 9)
    else:
        trap = np.random.randint(manipulandum + 11, 0)
        target = np.random.randint(np.max([manipulandum - max_distance_to_target - 10, -90]), manipulandum - 9)

    return manipulandum, target, trap


def initialise_trial_with_constant_target_trap():
    global max_distance_to_target
    global up_or_down
    global experiment_state

    up_or_down = np.random.binomial(n=1, p=0.5)

    if up_or_down:
        target = 0
        trap = -90

        manipulandum = np.random.randint(np.max([target - max_distance_to_target - 10, -90]), target - 9)
    else:
        target = -90
        trap = 0

        manipulandum = np.random.randint(target + 11, np.min([target + max_distance_to_target + 12, 0]))

    return manipulandum, target, trap


def update_of_visuals(lever_pressed_time):
    global angles_of_visuals
    global experiment_state
    global on_target
    global error
    global time_on_target

    new_position = int(initial_angle_of_manipulandum + speed * lever_pressed_time / 1000)

    # If the rat is not pressing a lever
    if lever_pressed_time == 0:

        # If the manipulandum has reached the target
        if experiment_state == ExperimentState.PokeIn_OnTarget:
            on_target += 1

            # If the manipulandum has stayed on the target long enough
            if on_target > time_on_target:

                experiment_state = ExperimentState.PokeIn_Finished_Sucess

        # If the manipulandum is not on the target
        else:
            angles_of_visuals[1] = initial_angle_of_manipulandum
            angles_of_visuals[0] = 0

    # If the rat is pressing a lever
    else:
        angles_of_visuals[0] = 1

    # If the target is over (left) of the rotating (translating) manipulandum
    if up_or_down:

        # If the manipulandum still hasn't reached the target
        if angles_of_visuals[1] <= angles_of_visuals[2] - error or angles_of_visuals[1] >= angles_of_visuals[2] + error:
            experiment_state = ExperimentState.PokeIn_Running
            on_target = 0

            # If the correct lever was pressed
            if new_position > angles_of_visuals[1]:
                angles_of_visuals[1] = new_position

            # If the wrong lever was pressed and the trap is on
            if new_position < angles_of_visuals[1] and trap_on:
                angles_of_visuals[1] = new_position

        # If the manipulandum has reached the target but hasn't stayed long enough on it
        if angles_of_visuals[2] - error <= angles_of_visuals[1] <= angles_of_visuals[2] + error \
                and on_target < time_on_target + 1:

            if must_lift_at_target:
                experiment_state = ExperimentState.PokeIn_OnTarget

                # If the rat is till pressing the lever keep moving
                if lever_pressed_time > 0:
                    angles_of_visuals[1] = new_position
            else:
                experiment_state = ExperimentState.PokeIn_Finished_Sucess

        # If the manipulandum reached the trap
        if angles_of_visuals[3] + error > angles_of_visuals[1] > angles_of_visuals[3] - error:
            experiment_state = ExperimentState.PokeIn_Finished_Failure
            on_target = 0

    else:  # If the target is under (right) of the manipulandum do as before with reversed movement

        # If the manipulandum still hasn't reached the target
        if angles_of_visuals[1] >= angles_of_visuals[2] + error or angles_of_visuals[1] <= angles_of_visuals[2] - error:
            experiment_state = ExperimentState.PokeIn_Running
            on_target = 0

            # If the correct lever was pressed
            if new_position < angles_of_visuals[1]:
                angles_of_visuals[1] = new_position

            # If the wrong lever was pressed and the trap is on
            if new_position > angles_of_visuals[1] and trap_on:
                angles_of_visuals[1] = new_position

        # If the manipulandum has reached the target but hasn't stayed long enough on it
        if angles_of_visuals[2] + error >= angles_of_visuals[1] >= angles_of_visuals[2] - error \
                and on_target < time_on_target + 1:

            if must_lift_at_target:
                experiment_state = ExperimentState.PokeIn_OnTarget

                # If the rat is till pressing the lever keep moving
                if lever_pressed_time < 0:
                    angles_of_visuals[1] = new_position
            else:
                experiment_state = ExperimentState.PokeIn_Finished_Sucess

        # If the manipulandum reached the trap
        if angles_of_visuals[3] + error > angles_of_visuals[1] > angles_of_visuals[3] - error:
            experiment_state = ExperimentState.PokeIn_Finished_Failure
            on_target = 0


def experiment(data, parameters):
    global no_mtt
    global reward_on_poke_delay
    global levers_state
    global trap_on
    global speed
    global variable_targets
    global number_of_pellets
    global experiment_state
    global _100ms_time_steps_counter

    try:
        reward_on_poke_delay = parameters[1]
        speed = parameters[4]
        number_of_pellets = parameters[7]
    except:
        pass

    message = data[1:]  # data[0] is the topic
    message = Socket.reconstruct_array_from_bytes_message(message)
    # The first element of the array is whether the rat is in the poke. The second is the milliseconds it has been
    # pressing either the left or the right lever (one is positive the other negative). If it is 0 then the rat is not
    # pressing a lever
    poke_on = message[0]
    lever_press_time = message[1]

    result = [np.array([ct.IGNORE]), np.array([ct.IGNORE])]
    max_100ms_steps_for_poke_out = 10

    # 1. If the no_mtt is on then
    # 1. a. If the rat is in the poke then tell the monitors to turn on and the poke controller
    # to deliver number_of_pellets (assuming the TL Poke Controller Trigger String is set to 'number').
    # 1. b. If the rat is not in the poke turn the monitors off and do not send a message to the poke controller
    # 2. If the no_mtt is off then:
    # 2. a. If the rat i snot in the poke then as above and send the experiment_state to PokeOut
    # 2. b. If the rat is in the poke then:
    # 2. b. i. If the trial has finished successfully then turn off the monitors and deliver number_of_pellets (if the
    # reward poke is in availability mode it will ignore any further commands to deliver reward)
    # 2. b. ii. If the trial has finished unsuccessfully then turn off the monitors and do not send anything to the poke
    # 2. b. iii. If the trial just started then put the state to running, initialise the visuals and update the monitors.
    # 2. b. iv. If the trial was running then update the visuals
    # In cases iii. and iv. send the visuals
    if reward_on_poke:
        if poke_on:
            _100ms_time_steps_counter += 1
            result = [np.array([True]), np.array([ct.IGNORE])]
            if _100ms_time_steps_counter >= reward_on_poke_delay * 10:
                result = [np.array([True]), np.array([number_of_pellets])]
        else:
            _100ms_time_steps_counter = 0
            result = [np.array([False]), np.array([ct.IGNORE])]
    else:
        if not poke_on:
            experiment_state = ExperimentState.PokeOut
            _100ms_time_steps_counter += 1

            if _100ms_time_steps_counter < max_100ms_steps_for_poke_out:
                result = [angles_of_visuals, np.array([ct.IGNORE])]
            else:
                result = [np.array([False]), np.array([ct.IGNORE])]

        else:
            if experiment_state == ExperimentState.PokeIn_Finished_Sucess:
                result = [np.array([False]), np.array([number_of_pellets])]
                _100ms_time_steps_counter = max_100ms_steps_for_poke_out + 1

            elif experiment_state == ExperimentState.PokeIn_Finished_Failure:
                result = [np.array([False]), np.array([ct.IGNORE])]
                _100ms_time_steps_counter = max_100ms_steps_for_poke_out + 1

            elif experiment_state == ExperimentState.PokeOut and _100ms_time_steps_counter > max_100ms_steps_for_poke_out:
                initialise_trial()
                experiment_state = ExperimentState.PokeIn_Running
                result = [angles_of_visuals, np.array([ct.IGNORE])]
                _100ms_time_steps_counter = 0

            elif experiment_state == ExperimentState.PokeIn_Running or \
                    (experiment_state == ExperimentState.PokeOut and _100ms_time_steps_counter < max_100ms_steps_for_poke_out)\
                    or experiment_state == ExperimentState.PokeIn_OnTarget:
                update_of_visuals(lever_press_time)
                result = [angles_of_visuals, np.array([ct.IGNORE])]
                _100ms_time_steps_counter = 0

    return result


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(work_function=experiment,
                                                          end_of_life_function=on_end_of_life,
                                                          initialisation_function=initialise)
    worker_object.start_ioloop()
