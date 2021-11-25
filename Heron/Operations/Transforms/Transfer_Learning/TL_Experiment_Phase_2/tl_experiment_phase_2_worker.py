
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

#import threading
import numpy as np
#import zmq
from enum import Enum
from Heron.communication.socket_for_serialization import Socket
from Heron.communication.transform_worker import TransformWorker
from Heron import general_utils as gu
from Heron import constants as ct

reward_on_poke: bool
movement_type: bool
trap_on: bool
speed: float
angles_of_visuals: np.empty(3)
initial_angle_of_manipulandum: int
up_or_down: bool
class ExperimentState(Enum):
    PokeOut = 1
    PokeIn_Running = 2
    PokeIn_Finished_Sucess = 3
    PokeIn_Finished_Failure = 4
experiment_state = ExperimentState.PokeOut
number_of_pellets = 1
#end_trial_in_the_next_ms = 0
#millis_to_wait_from_poke_empty_to_end_trial = 500
worker_object: TransformWorker


def initialise(_worker_object):
    global reward_on_poke
    global movement_type
    global trap_on
    global speed
    global number_of_pellets
    global worker_object
    try:
        parameters = _worker_object.parameters
        reward_on_poke = parameters[0]
        trap_on = parameters[1]
        speed = parameters[2]
        number_of_pellets = parameters[3]
        worker_object = _worker_object
    except Exception as e:
        print(e)
        return False

    return True


def initialise_trial():
    global angles_of_visuals
    global initial_angle_of_manipulandum
    global up_or_down
    global experiment_state

    manipulandum = np.random.randint(-80, -10)
    initial_angle_of_manipulandum = manipulandum
    up_or_down = np.random.binomial(n=1, p=0.5)
    if up_or_down:
        target = np.random.randint(manipulandum + 11, 0)
        trap = np.random.randint(-90, manipulandum - 9)
    else:
        trap = np.random.randint(manipulandum + 11, 0)
        target = np.random.randint(-90, manipulandum - 9)
    angles_of_visuals = np.array([manipulandum, target, trap])


def update_of_visuals(lever_pressed_time):
    global angles_of_visuals
    global experiment_state

    new_position = int(initial_angle_of_manipulandum + speed * lever_pressed_time / 1000)

    if lever_pressed_time == 0:
        angles_of_visuals[0] = initial_angle_of_manipulandum

    if up_or_down:  # If the target is over (left) of the rotating (translating) manipulandum
        if new_position in np.arange(angles_of_visuals[2], angles_of_visuals[1]):  # If the manipulandum still hasn't reached either the target or the trap
            experiment_state = ExperimentState.PokeIn_Running
            if new_position > angles_of_visuals[0]:  # If the correct lever was pressed
                    angles_of_visuals[0] = new_position

            if new_position < angles_of_visuals[0] and trap_on:  # If the wrong lever was pressed and the trap is on
                    angles_of_visuals[0] = new_position

        elif np.abs(angles_of_visuals[0] - angles_of_visuals[1]) < np.abs(angles_of_visuals[0] - angles_of_visuals[2]):  # If the manipulandum reached the target
            experiment_state = ExperimentState.PokeIn_Finished_Sucess
        else:  # If the manipulandum reached the trap
            experiment_state = ExperimentState.PokeIn_Finished_Failure

    else:  # If the target is under (right) of the manipulandum do as before with reversed movement
        if new_position in np.arange(angles_of_visuals[1], angles_of_visuals[2]): # If the manipulandum still hasn't reached either the target or the trap
            experiment_state = ExperimentState.PokeIn_Running
            if new_position < angles_of_visuals[0]:  # If the correct lever was pressed
                    angles_of_visuals[0] = new_position

            if new_position > angles_of_visuals[0] and trap_on:  # If the wrong lever was pressed and the trap is on
                    angles_of_visuals[0] = new_position

        elif np.abs(angles_of_visuals[0] - angles_of_visuals[1]) < np.abs(angles_of_visuals[0] - angles_of_visuals[2]):  # If the manipulandum reached the target
            experiment_state = ExperimentState.PokeIn_Finished_Sucess
        else:  # If the manipulandum reached the trap
            experiment_state = ExperimentState.PokeIn_Finished_Failure


def experiment(data, parameters):
    global reward_on_poke
    global movement_type
    global trap_on
    global speed
    global number_of_pellets
    global experiment_state

    try:
        number_of_pellets = parameters[3]
    except:
        pass

    topic = data[0].decode('utf-8')
    message = data[1:]  # data[0] is the topic
    message = Socket.reconstruct_array_from_bytes_message(message)
    poke_on = message[0]
    lever_press_time = message[1]

    # 1. If the topic is 'Trial end' that means that the poke has not send a message for the last
    # millis_to_wait_from_poke_empty_to_end_trial milliseconds so send to the TL Task2 Screens Node a False
    # to tell it to turn off the visuals.
    #if topic == 'Trial end':
    #    #print('Trial end')
    #    return [np.array([0]), np.array([ct.IGNORE])]

    # 2. If there is a signal and the topic is not 'Trial end', that means the rat is in the poke.
    # 2. a. If the reward_on_poke is on then tell the screens to turn on and the poke controller
    # to deliver number_of_pellets (assuming the TL Poke Controller Trigger String is set to 'number').
    # Also (re)set the end_trial_in_the_next_ms to millis_to_wait_from_poke_empty_to_end_trial (since the poke is
    # still giving signal).
    # 2. b. If the reward_on_poke is off then:
    # 2. b. i. If the trial has finished successfully then turn off the screens, do not update the
    # end_trial_in_the_next_ms and give reward (the reward signal will be send multiple times but that is ok).
    # 2. b. ii. If the trial has finished unsuccessfully then turn off the screens and do not update the
    # end_trial_in_the_next_ms.
    # 2. b. iii. If the trial just started then put the state to running, update the end_trial_in_the_next_ms and
    # initialise the visuals.
    # 2. b. iv. If the trial was running then update the visuals
    # In cases iii. and iv. send the visuals
    print(experiment_state.name, message)
    if reward_on_poke:
        if poke_on:
            #end_trial_in_the_next_ms = millis_to_wait_from_poke_empty_to_end_trial
            #print('2a')
            return [np.array([True]), np.array([number_of_pellets])]
        else:
            return [np.array([False]), np.array([ct.IGNORE])]
    else:
        if not poke_on:
            experiment_state = ExperimentState.PokeOut
            return [np.array([False]), np.array([ct.IGNORE])]
        else:
            if experiment_state == ExperimentState.PokeIn_Finished_Sucess:
                #print('2b i')
                #end_trial_in_the_next_ms = millis_to_wait_from_poke_empty_to_end_trial
                return [np.array([False]), np.array([number_of_pellets])]

            if experiment_state == ExperimentState.PokeIn_Finished_Failure:
                #print('2b ii')
                #end_trial_in_the_next_ms = millis_to_wait_from_poke_empty_to_end_trial
                return [np.array([False]), np.array([ct.IGNORE])]

            if experiment_state == ExperimentState.PokeOut:
                #print('2b iii')
                #print('---- {} ----'.format(experiment_state.name))
                initialise_trial()
                #end_trial_in_the_next_ms = millis_to_wait_from_poke_empty_to_end_trial
                experiment_state = ExperimentState.PokeIn_Running
                return [angles_of_visuals, np.array([ct.IGNORE])]
            if experiment_state == ExperimentState.PokeIn_Running:
                #print('2b iv')
                #end_trial_in_the_next_ms = millis_to_wait_from_poke_empty_to_end_trial
                experiment_state = ExperimentState.PokeIn_Running
                update_of_visuals(lever_press_time)
                return [angles_of_visuals, np.array([ct.IGNORE])]

        #end_trial_in_the_next_ms = millis_to_wait_from_poke_empty_to_end_trial



def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(work_function=experiment,
                                                          end_of_life_function=on_end_of_life,
                                                          initialisation_function=initialise)
    worker_object.start_ioloop()
