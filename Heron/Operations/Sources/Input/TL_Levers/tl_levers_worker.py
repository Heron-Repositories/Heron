
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import copy
import numpy as np
import serial
from Heron import general_utils as gu


arduino_serial: serial.Serial
loop_on = True
buffer = ''


def initialise(_worker_object):
    global arduino_serial

    try:
        parameters = _worker_object.parameters
        com_port = parameters[0]
    except Exception as e:
        print(e)
        return False

    try:
        arduino_serial = serial.Serial(com_port)
    except Exception as e:
        print(e)

    return True


def get_string(string_in):
    global buffer

    if '\n' in string_in:
        result = copy.copy(buffer) + copy.copy(string_in.split('\n')[0])
        buffer = copy.copy(string_in.split('\n')[1])
    else:
        buffer = buffer + copy.copy(string_in)
        result = False

    return result


def get_lever_pressing_time(string):
    """
    Returns the time a Lever is pressed
    :return: The time in ms that one of the levers is being pressed. Positive time means Left lever, negative means Right
    """
    [left_string, right_string] = string.split('#')
    left_time = int(left_string.split('=')[1])
    right_time = -int(right_string.split('=')[1])
    if left_time != 0:
        return left_time
    else:
        return right_time


def arduino_data_capture(_worker_object):
    global arduino_serial
    global loop_on

    worker_object = _worker_object
    while loop_on:
        try:
            worker_object.visualisation_on = worker_object.parameters[0]
            bytes_in_buffer = arduino_serial.in_waiting
            if bytes_in_buffer > 0:
                string_in = arduino_serial.read(bytes_in_buffer).decode('utf-8')

                final_string = get_string(string_in)
                if final_string:
                    time = get_lever_pressing_time(final_string)
                    if time:
                        worker_object.worker_visualisable_result = np.array([time])
                        worker_object.socket_push_data.send_array(worker_object.worker_visualisable_result, copy=False)
        except:
            pass



def on_end_of_life():
    global arduino_serial
    arduino_serial.reset_input_buffer()
    arduino_serial.close()


if __name__ == "__main__":
    gu.start_the_source_worker_process(worker_function=arduino_data_capture,
                                       end_of_life_function=on_end_of_life,
                                       initialisation_function=initialise)