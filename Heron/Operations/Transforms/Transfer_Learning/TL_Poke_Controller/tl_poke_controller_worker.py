
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
import serial
import threading
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu, constants as ct

need_parameters = True
arduino_serial: serial.Serial
avail_time: float
avail_freq: int
succ_freq: int
trigger_string: str
availability_period_is_running = False
reward_amount = 1


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
    global trigger_string

    try:
        parameters = _worker_object.parameters
        com_port = parameters[0]
        avail_time = parameters[1]
        avail_freq = parameters[2]
        succ_freq = parameters[3]
        trigger_string = parameters[4]
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
        if bytes_in_buffer and '555\r\n' in string_in:
                availability_period_is_running = False
                try:
                    arduino_serial.write(freq_to_signal(succ_freq))
                    gu.accurate_delay(1500 * sleep_dt)
                    arduino_serial.write(freq_to_signal(succ_freq))
                    gu.accurate_delay(1500 * sleep_dt)
                    for i in np.arange(reward_amount):
                        arduino_serial.write('a'.encode('utf-8'))
                        gu.accurate_delay(500)
                except Exception as e:
                    print(e)
        elif step >= total_steps:
            try:
                availability_period_is_running = False
                arduino_serial.write(freq_to_signal(1000))
                gu.accurate_delay(1200 * sleep_dt)
                arduino_serial.write(freq_to_signal(500))
            except Exception as e:
                print(e)
        else:
            try:
                arduino_serial.write(freq_to_signal(avail_freq))
                arduino_serial.read(arduino_serial.in_waiting)
            except Exception as e:
                print(e)
            gu.accurate_delay(1000 * sleep_dt)
        step += 1


def start_availability_period(data, parameters):
    global availability_period_is_running
    global trigger_string
    global reward_amount

    # topic = data[0].decode('utf-8')
    message = Socket.reconstruct_array_from_bytes_message(data[1:])

    if ct.IGNORE == message[0]:
        result = [np.array([ct.IGNORE])]
    else:
        if not availability_period_is_running:
            if trigger_string == message[0] or trigger_string == 'number':
                if trigger_string == 'number':
                    reward_amount = int(message[0])
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
