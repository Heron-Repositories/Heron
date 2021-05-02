
import time
import sys
from struct import *
from Heron.communication.transform_com import TransformCom


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
        print('Failed to kill process {}'.format(child_pid.pid))
        pass


def choose_color_according_to_operations_type(operations_parent_name):
    colour = [255, 255, 255, 100]
    if 'Sources' in operations_parent_name:
        colour = [0, 0, 255, 100]
    elif 'Transforms' in operations_parent_name:
        colour = [0, 255, 0, 100]
    elif 'Sinks' in operations_parent_name:
        colour = [255, 0, 0, 100]

    return colour


def get_next_available_port_group(starting_port, step):
    """
    A generator that creates the next port jumping over ports at a step of ct.MAXIMUM_RESERVED_SOCKETS_PER_NODE
    :return:
    """
    while True:
        yield str(starting_port)
        starting_port = starting_port + step


def parse_arguments_to_com(args):
    """
    Turns the list of argv arguments that is send to a com process (by the editor) into appropriate list of strings
    and lists (of topics). It is up to the node's start_exec function to create a list of argv that can be properly
    parsed.
    :param args: The argv returned by the sys.argv
    :return: port = the initial port for the com process,
    receiving_topics = a list of the names of the topics the process receives (inputs) data at
    sending_topics = a list of the names of the topics the process sends (outputs) data at
    parameters_topic = the name of the topic the process receives parameter updates from the node
    """
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
    parameters_topic = args[-1]

    return port, receiving_topics, sending_topics, parameters_topic


def parse_arguments_to_worker(args):
    """
    Turns the list of argv arguments that is send to a com process (by the editor) into appropriate list of strings
    and lists (of topics). It is up to the com's start_worker function to create a list of argv that can be properly
    parsed.
    :param args: The argv returned by the sys.argv
    :return: port = the initial port for the worker process,
    parameters_topic = the name of the topic the process receives parameter updates from the node
    receiving_topics = a list of the names of the topics the process receives (inputs) data at
    verbose = the verbosity of the worker process (True or False)
    """
    args = args[1:]
    port = args[0]
    parameters_topic = args[1]
    num_of_receiving_topics = int(args[2])
    receiving_topics = []
    for i in range(num_of_receiving_topics):
        receiving_topics.append(args[i+3])
    verbose = args[-1]

    return port, parameters_topic, receiving_topics, verbose


def start_the_communications_process(process_exec_file):
    """
    Creates a TransformCom object for a transformation process
    (i.e. initialises the worker process and keeps the zmq communication between the worker
    and the forwarder)
    The push_port is the port that the canny_com uses to push data to the canny_worker.
    It is called as a separate process.
    :return: The com object
    """
    push_port, receiving_topics, sending_topics, parameters_topic = parse_arguments_to_com(sys.argv)

    com_object = TransformCom(sending_topics=sending_topics, receiving_topics=receiving_topics, parameters_topic=parameters_topic,
                              push_port=push_port, worker_exec=process_exec_file, verbose=False)
    com_object.connect_sockets()
    com_object.start_heartbeat_thread()
    com_object.start_worker()

    return com_object
