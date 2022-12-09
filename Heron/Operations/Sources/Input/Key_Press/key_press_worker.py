
import sys
from os import path
import time
import numpy as np

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron import general_utils as gu
from Heron.Operations.Sources.Input.Key_Press import key_press_com
from Heron.communication.source_worker import SourceWorker
from Heron.gui.visualisation_dpg import VisualisationDPG
from pynput.keyboard import Listener

worker_object: SourceWorker
listener: Listener
key_pressed_and_released = [None, None]
previous_user_input = False
loop_on = True
new_input_for_vis = ''
vis: VisualisationDPG


def on_key_pressed(key):
    global key_pressed_and_released
    try:
        key_pressed_and_released[0] = key.char
    except:
        pass


def on_key_released(key):
    global key_pressed_and_released
    global previous_user_input
    global new_input_for_vis

    try:
        key_pressed_and_released[1] = key.char
        new_input_for_vis = key.char
    except:
        new_input_for_vis = 'No special keys please'


def visualisation_to_stdout(vis_object):
    global previous_user_input
    global key_pressed_and_released
    global new_input_for_vis

    while True:
        while vis_object.visualisation_on:
            if new_input_for_vis:
                print(new_input_for_vis)
                if len(vis_object.visualised_data) == 1 and new_input_for_vis == vis_object.visualised_data[0]:
                    print('Outputing :{}'.format(vis_object.visualised_data))
                new_input_for_vis = False


def start_key_press_capture(_worker_object):
    global worker_object
    global key_pressed_and_released
    global listener
    global loop_on
    global vis

    worker_object = _worker_object
    vis = VisualisationDPG(_node_name=_worker_object.node_name, _node_index=_worker_object.node_index,
                           _visualisation_type='Value', _buffer=20)
    listener = Listener(on_press=on_key_pressed, on_release=on_key_released)
    listener.start()

    worker_object.savenodestate_create_parameters_df(visualisation_on=vis.visualisation_on, key='')

    while loop_on:
        try:
            waiting_for_key = str(worker_object.parameters[1])
            worker_object.initialised = True
        except:
            waiting_for_key = key_press_com.ParametersDefaultValues[1]

        if key_pressed_and_released[0] == waiting_for_key and \
           key_pressed_and_released[1] == waiting_for_key:
            data = np.array([waiting_for_key])
            vis.visualise(data)
            worker_object.send_data_to_com(data)
            worker_object.savenodestate_update_substate_df(key_pressed=data)
            key_pressed_and_released = [None, None]
        try:
            vis.visualisation_on = worker_object.parameters[0]
        except:
            vis.visualisation_on = key_press_com.ParametersDefaultValues[0]

        time.sleep(0.1)


def on_end_of_life():
    global listener
    global loop_on
    loop_on = False
    try:
        listener.stop()
    except:
        pass
    vis.end_of_life()


if __name__ == "__main__":
    gu.start_the_source_worker_process(work_function=start_key_press_capture,
                                       end_of_life_function=on_end_of_life)