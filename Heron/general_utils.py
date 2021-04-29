
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


def parse_arguments_to_com(args):
    args = args[1:]
    port = args[0]
    num_of_receiving_topics = int(args[1])
    receiving_topics = []
    sending_topics = []
    if num_of_receiving_topics > 0:
        for i in range(num_of_receiving_topics):
            receiving_topics.append(args[i + 2])
    num_of_sending_topics = int(args[num_of_receiving_topics + 2])
    if num_of_sending_topics > 0:
        for k in range(num_of_sending_topics):
            sending_topics.append(args[k + num_of_receiving_topics + 3])
    state_topic = args[-1]

    return port, receiving_topics, sending_topics, state_topic


def parse_arguments_to_worker(args):
    args = args[1:]
    port = args[0]
    state_topic = args[1]
    num_of_receiving_topics = int(args[2])
    receiving_topics = []
    for i in range(num_of_receiving_topics):
        receiving_topics.append(args[i+3])
    verbose = args[-1]

    return port, state_topic, receiving_topics, verbose


def get_next_available_port_group(starting_port, step):
    """
    A generator that creates the next port jumping over ports at a step of ct.MAXIMUM_RESERVED_SOCKETS_PER_NODE
    :return:
    """
    while True:
        yield str(starting_port)
        starting_port = starting_port + step