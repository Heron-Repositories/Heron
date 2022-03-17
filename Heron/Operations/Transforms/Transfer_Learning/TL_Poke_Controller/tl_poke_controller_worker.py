
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
sleep_dt = 0.18
abort_at_wrong_poke: bool
air_puff_at_wrong_poke: bool
trigger_string: str
availability_period_is_running = False
reward_amount = 1
reward_poke: bool # False is the Old / Right poke, True is the New / Left one
air_puff_thread_is_running: bool
air_puff_timer = 0


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
    global abort_at_wrong_poke
    global air_puff_at_wrong_poke
    global trigger_string
    global reward_poke
    global air_puff_thread_is_running

    try:
        parameters = _worker_object.parameters
        com_port = parameters[0]
        avail_time = parameters[1]
        avail_freq = parameters[2]
        succ_freq = parameters[3]
        abort_at_wrong_poke = parameters[4]
        air_puff_at_wrong_poke = parameters[5]
        trigger_string = parameters[6]
        print(avail_freq, succ_freq)
    except Exception as e:
        print(e)
        return False

    try:
        arduino_serial = serial.Serial(com_port)
    except Exception as e:
        print(e)
        return False

    reward_poke = True
    set_poke_tray()

    if air_puff_at_wrong_poke:
        air_puff_thread_is_running = True
        air_puff_thread = threading.Thread(group=None, target=start_air_puff_thread)
        air_puff_thread.start()

    return True


def failure_sound():
    arduino_serial.write(freq_to_signal(1000))
    gu.accurate_delay(1200 * sleep_dt)
    arduino_serial.write(freq_to_signal(500))


def success_sound():
    if int(succ_freq) != 0:
        arduino_serial.write(freq_to_signal(succ_freq))
        gu.accurate_delay(1500 * sleep_dt)
        arduino_serial.write(freq_to_signal(succ_freq))
    gu.accurate_delay(1500 * sleep_dt)


def availability_sound():
    if int(avail_freq) != 0:
        arduino_serial.write(freq_to_signal(avail_freq))


def start_availability_thread():
    global arduino_serial
    global availability_period_is_running
    global avail_time
    global avail_freq
    global succ_freq
    global reward_poke
    global abort_at_wrong_poke

    total_steps = int(avail_time / sleep_dt)

    availability_period_is_running = True
    bytes_in_buffer = arduino_serial.in_waiting
    while bytes_in_buffer:
        bytes_in_buffer = arduino_serial.in_waiting
        string_in = arduino_serial.read(bytes_in_buffer).decode('utf-8')
        if '555\r\n' in string_in:
            gu.accurate_delay(500)
        arduino_serial.reset_input_buffer()
    step = 0

    while availability_period_is_running:

        bytes_in_buffer = arduino_serial.in_waiting
        string_in = arduino_serial.read(bytes_in_buffer).decode('utf-8')

        success_failure_continue = 2  # 0=success, 1=failure, 2=continue
        # If the string is either 555 or 666 then if it is for the wrong poke and the abort_at_wrong_poke is on then
        # fail, otherwise succeed
        if bytes_in_buffer:
            if '555\r\n' in string_in:
                if not reward_poke:
                    success_failure_continue = 0
                else:
                    if abort_at_wrong_poke:
                        success_failure_continue = 1
                    else:
                        success_failure_continue = 0
            if '666\r\n' in string_in:
                if reward_poke:
                    success_failure_continue = 0
                else:
                    if abort_at_wrong_poke:
                        success_failure_continue = 1
                    else:
                        success_failure_continue = 0

        if success_failure_continue == 0:
                try:
                    success_sound()
                    for _ in np.arange(reward_amount):
                        arduino_serial.write('a'.encode('utf-8'))
                        gu.accurate_delay(500)
                    availability_period_is_running = False
                except Exception as e:
                    print(e)
        elif step >= total_steps or success_failure_continue == 1:
            try:
                failure_sound()
                availability_period_is_running = False
            except Exception as e:
                print(e)
        else:
            try:
                availability_sound()
                arduino_serial.read(arduino_serial.in_waiting)
                availability_period_is_running = True
            except Exception as e:
                print(e)
            gu.accurate_delay(1000 * sleep_dt)
        step += 1


def set_poke_tray():
    global arduino_serial
    global reward_poke

    if reward_poke:
        arduino_serial.write('m'.encode('utf-8'))
    else:
        arduino_serial.write('n'.encode('utf-8'))


def start_air_puff_thread():
    global availability_period_is_running
    global air_puff_thread_is_running
    global previous_availability_for_air_puff
    global air_puff_timer

    while air_puff_thread_is_running:
        if availability_period_is_running:
            air_puff_timer = 0
        if not availability_period_is_running:
            air_puff_timer += 1
            if air_puff_timer < 50:
                arduino_serial.reset_input_buffer()
            else:  # 5 seconds delay
                air_puff_if_poking_outside_availability()

        gu.accurate_delay(100)


def air_puff_if_poking_outside_availability():

    if not availability_period_is_running:
        bytes_in_buffer = arduino_serial.in_waiting
        string_in = arduino_serial.read(bytes_in_buffer).decode('utf-8')

        if bytes_in_buffer:
            if '555\r\n' in string_in or '666\r\n' in string_in:
                arduino_serial.write('y'.encode('utf-8'))
                gu.accurate_delay(200)
                arduino_serial.write('z'.encode('utf-8'))


def start_availability_or_switch_pokes(data, parameters):
    global availability_period_is_running
    global trigger_string
    global reward_amount
    global reward_poke

    topic = data[0].decode('utf-8')
    message = Socket.reconstruct_array_from_bytes_message(data[1:])

    if 'Start' in topic:
        if not availability_period_is_running:
            if trigger_string == message[0] or trigger_string == 'number':
                if trigger_string == 'number':
                    reward_amount = int(message[0])
                try:
                    if message[0] != -1 and message[0] != '-1':  # That allows the result to update without starting another thread
                        avail_thread = threading.Thread(target=start_availability_thread)
                        avail_thread.start()
                except Exception as e:
                    print(e)
        result = [np.array([availability_period_is_running])]
    elif 'Poke' in topic:
        reward_poke = message[0]
        if reward_poke == 'Left' or reward_poke == 'New':
            reward_poke = True
        if reward_poke == 'Right' or reward_poke == 'Old':
            reward_poke = False
        set_poke_tray()
        result = [np.array([availability_period_is_running])]

    return result


def on_end_of_life():
    global arduino_serial
    global air_puff_thread_is_running

    air_puff_thread_is_running = False
    gu.accurate_delay(100)

    arduino_serial.reset_input_buffer()
    arduino_serial.close()


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(work_function=start_availability_or_switch_pokes,
                                                          end_of_life_function=on_end_of_life,
                                                          initialisation_function=initialise)
    worker_object.start_ioloop()
