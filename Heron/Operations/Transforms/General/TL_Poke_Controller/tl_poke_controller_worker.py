
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
import time
import serial
import threading
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu, constants as ct

need_parameters = True
arduino_serial: serial.Serial
avail_time: float
avail_freq: int
succ_freq: int
availability_period_is_running = False


def freq_to_signal(freq):
    freq = int(freq)
    if freq < 500:
        freq = 500
    if freq > 5000:
        freq = 5000
    return chr(int(freq/500 + 97)).encode('utf-8')


def initialise(_worker_object):
    global arduino_serial
    global avail_time
    global avail_freq
    global succ_freq

    try:
        parameters = _worker_object.parameters
        com_port = parameters[0]
        avail_time = parameters[1]
        avail_freq = parameters[2]
        succ_freq = parameters[3]
    except Exception as e:
        print(e)
        return False

    try:
        arduino_serial = serial.Serial(com_port)
    except Exception as e:
        print(e)
    return True


def start_availability_thread():
    global arduino_serial
    global availability_period_is_running
    global avail_time
    global avail_freq
    global succ_freq

    sleep_dt = 0.18
    total_steps = int(avail_time / sleep_dt)

    availability_period_is_running = True
    arduino_serial.reset_input_buffer()
    step = 0
    while availability_period_is_running:

        bytes_in_buffer = arduino_serial.in_waiting
        string_in = arduino_serial.read(bytes_in_buffer).decode('utf-8')
        #print(step)
        if bytes_in_buffer:
            #print(string_in)
            if '555\r\n' in string_in:
                #print('Play success sound and give food')
                availability_period_is_running = False
                try:
                    arduino_serial.write('a'.encode('utf-8'))
                    arduino_serial.write(freq_to_signal(succ_freq))
                    time.sleep(1.5 * sleep_dt)
                    arduino_serial.write(freq_to_signal(succ_freq))
                except Exception as e:
                    print(e)
        elif step >= total_steps:
            #print('Finish')
            availability_period_is_running = False
            arduino_serial.write(freq_to_signal(1000))
            time.sleep(1.2 * sleep_dt)
            arduino_serial.write(freq_to_signal(500))
        else:
            #print('Play Availability sound')
            try:
                arduino_serial.write(freq_to_signal(avail_freq))
                arduino_serial.read(arduino_serial.in_waiting)
            except Exception as e:
                print(e)
            time.sleep(sleep_dt)
        step += 1


def start_availability_period(data, parameters):
    global availability_period_is_running

    # topic = data[0].decode('utf-8')
    message = Socket.reconstruct_array_from_bytes_message(data[1:])

    if ct.IGNORE == message[0]:
        result = [np.array([ct.IGNORE])]
    else:
        if 'start' == message[0]:
            if not availability_period_is_running:
                try:
                    avail_thread = threading.Thread(target=start_availability_thread)
                    avail_thread.start()
                except Exception as e:
                    print(e)
        result = [np.array([availability_period_is_running])]

    return result


def on_end_of_life():
    global arduino_serial
    arduino_serial.reset_input_buffer()
    arduino_serial.close()


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(work_function=start_availability_period,
                                                          end_of_life_function=on_end_of_life,
                                                          initialisation_function=initialise)
    worker_object.start_ioloop()
