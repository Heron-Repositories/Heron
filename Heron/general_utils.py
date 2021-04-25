
import time
import os
import signal
from struct import *


def float_to_binary(num):
    return bin( unpack('I', pack('f', num))[0] )


def binary_to_float(binary):
    int_binary = int(binary, 2)
    return unpack('f', pack('I', int_binary))[0]


def accurate_delay(delay):
    ''' Function to provide accurate time delay in millisecond
    '''
    target_time = time.perf_counter() + delay/1000
    while time.perf_counter() < target_time:
        pass


def kill_child(child_pid):
    print('KILL')
    print(child_pid)
    try:
        child_pid.kill()
    except:
        pass
        #os.kill(child_pid, signal.SIGTERM)


def choose_color_according_to_operations_type(operations_parent_name):
    colour = [255, 255, 255, 100]
    if 'Sources' in operations_parent_name:
        colour = [0, 0, 255, 100]
    elif 'Transforms' in operations_parent_name:
        colour = [0, 255, 0, 100]
    elif 'Sinks' in operations_parent_name:
        colour = [255, 0, 0, 100]

    return colour