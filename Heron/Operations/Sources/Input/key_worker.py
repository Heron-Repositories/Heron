
import sys
from os import path
import time
import dearpygui.dearpygui as dpg

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron import general_utils as gu
from Heron.Operations.Sources.Input import key_com

capturing_key_on = False


def capture_key_press(worker_object):
    global capturing_key_on

    if not capturing_key_on:  # Get the parameters from the node
        while not capturing_key_on:
            try:
                key = worker_object.parameters[1]
                capturing_key_on = True
            except:
                time.sleep(0.1)

    while True:
        worker_object.worker_result = np.array([dpg.is_key_pressed(key)])
        worker_object.socket_push_data.send_array(worker_object.worker_result, copy=False)
        try:
            worker_object.visualisation_on = worker_object.parameters[0]
        except:
            worker_object.visualisation_on = key_com.ParametersDefaultValues[0]

        worker_object.visualisation_loop_init()


def on_end_of_life():
    pass


if __name__ == "__main__":
    gu.start_the_source_worker_process(capture_key_press(), on_end_of_life)