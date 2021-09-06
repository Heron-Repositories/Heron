
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.Operations.Transforms.General.TL_Experiment_Phases_1_3 import tl_experiment_phases_1_3_com as the_com

input_names: list
output_names: list
input_state: dict
output_state: dict
detected_angle_buffer_size = 10
detected_angle_buffer = []
manipulandum_state: int
poke_state: str
angle_shown_state: int
last_motor_state: str

NOT_DETECTED = 'Not Detected'


def initialise(worker_object):
    global input_names, output_names
    global input_state, output_state
    input_names = the_com.NodeAttributeNames[:3]
    output_names = the_com.NodeAttributeNames[3:]
    for i, name in enumerate(input_names):
        input_names[i] = name.replace(' ', '_')
    for i, name in enumerate(output_names):
        output_names[i] = name.replace(' ', '_')

    input_state = {input_names[0]: 'Not Detected', input_names[1]: 'Not Shown', input_names[2]: False}
    output_state = {output_names[0]: 'Not Used', output_names[1]: False,
                    output_names[2]: False, output_names[3]: 'Ignore'}

    return True


def topic_to_input_state_key(topic):
    global input_names
    for input_name in input_names:
        if input_name in topic:
            return input_name
    print('Topic not found in Input Names! Something is Wrong!')
    return 'No Key'


def create_results_from_output_state():
    global output_names
    global output_state
    results = []
    for o_name in output_names:
        results.append(np.array([output_state[o_name]]))

    return results


def update_manipulandum_state():
    global input_names
    global input_state
    global detected_angle_buffer_size
    global detected_angle_buffer
    global manipulandum_state

    if detected_angle_buffer_size > len(detected_angle_buffer):
        detected_angle_buffer.append(input_state[input_names[0]])

    manipulandum_state = None
    if not NOT_DETECTED in detected_angle_buffer and np.std(detected_angle_buffer) < 0.5:
        manipulandum_state = np.average(detected_angle_buffer)


def main_loop(data, parameters):
    global input_names, output_names
    global input_state, output_state

    try:
        t = input_names[0]
    except:
        initialise(None)

    topic = data[0].decode('utf-8')
    #print(topic)

    input_key = topic_to_input_state_key(topic)

    if input_key == 'No Key':
        return create_results_from_output_state()

    message = data[1:]  # data[0] is the topic
    data_array = Socket.reconstruct_array_from_bytes_message_cv2correction(message)
    input_state[input_key] = data_array[0]

    if input_key == input_names[0]:
        update_manipulandum_state()


    results = create_results_from_output_state()

    #print(results)
    #print('-------------------------')

    return results


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(main_loop, on_end_of_life, initialise)
    worker_object.start_ioloop()
