
import sys
from os import path
import time
import numpy as np

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron import general_utils as gu
from Heron.Operations.Sources.Input import key_com
from Heron.communication.source_worker import SourceWorker
from pynput.keyboard import Listener


worker_object: SourceWorker
listener: Listener
key_pressed_and_released = [None, None]
new_input_for_vis = False


def on_key_pressed(key):
    global key_pressed_and_released
    key_pressed_and_released[0] = key.char


def on_key_released(key):
    global key_pressed_and_released
    global new_input_for_vis
    key_pressed_and_released[1] = key.char
    new_input_for_vis = key.char


def visualisation_to_stdout():
    global worker_object
    global new_input_for_vis
    global key_pressed_and_released
    while True:
        while worker_object.visualisation_on:
            if new_input_for_vis:
                print(new_input_for_vis)
                if new_input_for_vis == worker_object.worker_result:
                    print('Outputing :{}'.format(worker_object.worker_result))
                new_input_for_vis = False


def start_key_press_capture(_worker_object):
    global worker_object
    global key_pressed_and_released
    global listener

    worker_object = _worker_object
    waiting_for_key = None
    worker_object.set_new_visualisation_loop(visualisation_to_stdout)

    while waiting_for_key is None:
        try:
            waiting_for_key = str(worker_object.parameters[1])
        except:
            time.sleep(0.1)

    listener = Listener(on_press=on_key_pressed, on_release=on_key_released)
    listener.start()

    while True:
        if key_pressed_and_released[0] == waiting_for_key and \
           key_pressed_and_released[1] == waiting_for_key:
            worker_object.worker_result = np.array([waiting_for_key])
            worker_object.socket_push_data.send_array(worker_object.worker_result, copy=False)
            worker_object.visualisation_loop_init()
            key_pressed_and_released = [None, None]
        try:
            worker_object.visualisation_on = worker_object.parameters[0]
        except:
            worker_object.visualisation_on = key_com.ParametersDefaultValues[0]


def on_end_of_life():
    global listener
    listener.stop()


if __name__ == "__main__":
    gu.start_the_source_worker_process(start_key_press_capture, on_end_of_life)