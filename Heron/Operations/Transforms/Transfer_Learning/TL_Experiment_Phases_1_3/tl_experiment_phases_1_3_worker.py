
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu, constants as ct
from Heron.Operations.Transforms.Transfer_Learning.TL_Experiment_Phases_1_3 import tl_experiment_phases_1_3_com as the_com

input_names: list
output_names: list
input_state: dict
output_state: dict

detected_angle_buffer_size = 5
detected_angle_buffer = []

manipulandum_state: int  # Set = {None, -90<x<90 | x in R}
poke_state = 'Off'  # Set = {'Off', 'Asked', 'On'}
angle_shown_state = None  # Set = {None, -90<x<90 | x in R}
angle_update_next = 0
last_motor_state = None  # Set = {None, 'CW', 'CCW'} but the None state is only at initialisation

NOT_DETECTED = 'Not Calculated'


def initialise(worker_object):
    global input_names, output_names
    global input_state, output_state
    global last_motor_state

    if worker_object is not None:
        last_motor_state = worker_object.parameters[0]
    input_names = the_com.NodeAttributeNames[1:4]
    output_names = the_com.NodeAttributeNames[4:]
    for i, name in enumerate(input_names):
        input_names[i] = name.replace(' ', '_')
    for i, name in enumerate(output_names):
        output_names[i] = name.replace(' ', '_')

    input_state = {input_names[0]: 'Not Detected', input_names[1]: False, input_names[2]: False}
    output_state = {output_names[0]: ct.IGNORE, output_names[1]: ct.IGNORE,
                    output_names[2]: ct.IGNORE, output_names[3]: ct.IGNORE}

    return True


def topic_to_input_state_key(topic):
    global input_names
    for input_name in input_names:
        if input_name in topic:
            return input_name
    print('Topic not found in Input Names! Something is Wrong!')
    return 'No Key'


def get_results_array_from_output_state_dict():
    global output_names
    global output_state
    results = []
    for o_name in output_names:
        results.append(np.array([output_state[o_name]]))

    return results


def update_manipulandum_state():
    global input_names, input_state
    global detected_angle_buffer_size, detected_angle_buffer
    global manipulandum_state

    if len(detected_angle_buffer) >= detected_angle_buffer_size:
        detected_angle_buffer.pop(0)
    detected_angle_buffer.append(input_state[input_names[0]])

    manipulandum_state = None
    if not NOT_DETECTED in detected_angle_buffer and np.std(detected_angle_buffer) < 1:
        manipulandum_state = np.average(detected_angle_buffer)


def update_poke_state():
    global input_names, input_state
    global poke_state

    if input_state[input_names[2]]:
        poke_state = 'On'
    else:
        poke_state = 'Off'


def update_angle_shown_state():
    global input_names, input_state
    global angle_shown_state

    if input_state[input_names[1]] != 'Not Detected':
        angle_shown_state = input_state[input_names[1]]

    print(angle_shown_state)


def compare_shown_angle_to_manipulandum_angle():
    global manipulandum_state, angle_shown_state

    man_angle = manipulandum_state
    if man_angle < 0:
        man_angle += 180
    shown_angle = angle_shown_state
    if shown_angle < 0:
        shown_angle += 180

    print('man_angle = {}, shown_angle = {}'.format(man_angle, shown_angle))
    if np.abs(man_angle - shown_angle) > 20:
        return False

    return True


def main_loop(data, parameters):
    global input_names, output_names
    global input_state, output_state
    global manipulandum_state, poke_state, angle_shown_state, angle_update_next, last_motor_state

    # 0) If the main_loop has been called before the input_names and the last_motor_state parameter has been properly
    # initialised, detect that and try to initialise them. Also return the function with its defaults.
    try:
        t = input_names[0]
    except:
        initialise(None)

    if last_motor_state is None:
        if parameters is not None:
            last_motor_state = parameters[0]
        else:
            return get_results_array_from_output_state_dict()

    # 1) Initialise the output_state to ct.IGNORE so no signals go out unless they need to
    angle_update_output = ct.IGNORE
    if output_state[output_names[0]] is not ct.IGNORE and output_state[output_names[0]] < 3:
        output_state[output_names[0]] += 1
        angle_update_output = angle_update_output
    output_state = {output_names[0]: angle_update_output, output_names[1]: ct.IGNORE,
                    output_names[2]: ct.IGNORE, output_names[3]: ct.IGNORE}

    # 2) Check if angle_update_next is not 0 (and smaller than 4) and send out an angle update signal.
    # This sends out the angle update signal multiple times so that the return signal from the Random Number
    # Generator doesn't get missed.
    if angle_update_next:
        output_state[output_names[0]] = 1
        if angle_update_next < 4:
            angle_update_next = 0

    # 3) Get the data that came in this Node, find the topic and update the input_state accordingly
    topic = data[0].decode('utf-8')
    #print(topic)
    input_key = topic_to_input_state_key(topic)

    if input_key == 'No Key':  # This happens only if something is very wrong with the topic that came in!
        return get_results_array_from_output_state_dict()

    message = data[1:]  # data[0] is the topic
    data_array = Socket.reconstruct_array_from_bytes_message(message)
    input_state[input_key] = data_array[0]

    # 4) If the input is "Shown Angle" then get the value and update the angle_shown_state
    if input_key == input_names[1]:
        update_angle_shown_state()

    # 5) If the input is "Detected Angle" then get the value and update the manipuladum_state, then check to see
    # if you need to send an 'Asked' signal to the Poke (5)
    if input_key == input_names[0]:
        update_manipulandum_state()

        # 6) If the updated manipulandum_state is a number and the poke_state is not 'Asked' then send a signal
        # to the Poke to get its state, so set the poke_state to 'Asked'
        if (manipulandum_state is not None and poke_state == 'Off') or poke_state == 'On':
            output_state[output_names[3]] = 'Check'
            poke_state = 'Asked'

    # 7) If the input is the Poke Availability State then update the poke_state with that info then check to see if
    # the trial needs to start (7)
    if input_key == input_names[2] and poke_state == 'Asked':
        update_poke_state()

        # 8) If the manipulandum_state is a number and the poke_state is 'Off' then check the angle_shown_state and then
        # send a move command to the correct motor and send a 'start' command to the Poke
        if manipulandum_state is not None and poke_state == 'Off':
            if angle_shown_state is None or (
                    angle_shown_state is not None and compare_shown_angle_to_manipulandum_angle()):
                output_state[output_names[3]] = 'start'
                if last_motor_state == 'CW':
                    last_motor_state = 'CCW'
                    output_state[output_names[2]] = 1
                elif last_motor_state == 'CCW':
                    last_motor_state = 'CW'
                    output_state[output_names[1]] = 1
                if angle_shown_state is not None:
                    angle_update_next += 1

    return get_results_array_from_output_state_dict()


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(main_loop, on_end_of_life, initialise)
    worker_object.start_ioloop()
