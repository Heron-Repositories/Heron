
import os
import time
import sys
import signal
from struct import *
from Heron.communication.source_com import SourceCom
from Heron.communication.source_worker import SourceWorker
from Heron.communication.transform_com import TransformCom
from Heron.communication.transform_worker import TransformWorker
from Heron.communication.sink_com import SinkCom
from Heron.communication.sink_worker import SinkWorker


def full_split_path(path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts

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
    try:
        os.kill(child_pid, signal.SIGTERM)
        #print('Killed process {}'.format(child_pid))
    except:
        print('Failed to kill process {}'.format(child_pid))


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
    receiving_topics = a list of the names of the topics the process receives (inputs) link at
    sending_topics = a list of the names of the topics the process sends (outputs) link at
    parameters_topic = the node_name of the topic the process receives parameter updates from the node
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
    parameters_topic = args[-2]
    verbose = args[-1]

    return port, receiving_topics, sending_topics, parameters_topic, verbose


def parse_arguments_to_worker(args):
    """
    Turns the list of argv arguments that is send to a com process (by the editor) into appropriate list of strings
    and lists (of topics). It is up to the com's start_worker function to create a list of argv that can be properly
    parsed.
    :param args: The argv returned by the sys.argv
    :return: port = the initial port for the worker process,
    parameters_topic = the node_name of the topic the process receives parameter updates from the node
    receiving_topics = a list of the names of the topics the process receives (inputs) link at
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


def start_the_source_communications_process(process_exec_file):
    """
    Creates a SourceCom object for a source process
    (i.e. initialises the worker process and keeps the zmq communication between the worker and the forwarders)
    :return: The SourceCom object
    """

    push_port, _, sending_topics, parameters_topic, verbose = parse_arguments_to_com(sys.argv)
    verbose = verbose == 'True'

    com_object = SourceCom(sending_topics=sending_topics, parameters_topic=parameters_topic, port=push_port,
                           worker_exec=process_exec_file, verbose=verbose)

    com_object.connect_sockets()
    com_object.start_heartbeat_thread()
    com_object.start_worker_process()

    return com_object


def start_the_source_worker_process(worker_function, end_of_life_function):
    """
    Creates a SourceWorker for a worker process of a Source
    :param worker_function:
    :return:
    """
    port, parameters_topic, _, verbose = parse_arguments_to_worker(sys.argv)
    verbose = verbose == 'True'

    worker_object = SourceWorker(port=port, parameters_topic=parameters_topic, end_of_life_function=end_of_life_function,
                                 verbose=verbose)
    worker_object.connect_socket()
    worker_object.start_heartbeat_thread()
    worker_object.start_parameters_thread()
    worker_function(worker_object)


def start_the_transform_communications_process(process_exec_file):
    """
    Creates a TransformCom object for a transformation process
    (i.e. initialises the worker process and keeps the zmq communication between the worker
    and the forwarder)
    :return: The TransformCom object
    """
    push_port, receiving_topics, sending_topics, parameters_topic, verbose = parse_arguments_to_com(sys.argv)
    verbose = verbose == 'True'

    com_object = TransformCom(sending_topics=sending_topics, receiving_topics=receiving_topics, parameters_topic=parameters_topic,
                              push_port=push_port, worker_exec=process_exec_file, verbose=verbose)
    com_object.connect_sockets()
    com_object.start_heartbeat_thread()
    com_object.start_worker()

    return com_object


def start_the_transform_worker_process(work_function, end_of_life_function):
    """
    Starts the _worker process of the Transform that grabs link from the _com process, does something with them
    and sends them back to the _com process. It also grabs any updates of the parameters of the worker function
    :return: The TransformWorker object
    """

    pull_port, parameters_topic, receiving_topics, verbose = parse_arguments_to_worker(sys.argv)
    verbose = verbose == 'True'

    buffer = {}
    for rt in receiving_topics:
        buffer[rt] = []

    worker_object = TransformWorker(recv_topics_buffer=buffer, pull_port=pull_port, work_function=work_function,
                                    end_of_life_function=end_of_life_function, parameters_topic=parameters_topic,
                                    verbose=verbose)
    worker_object.connect_sockets()

    return worker_object


def start_the_sink_communications_process(process_exec_file):
    """
    Creates a TransformCom object for a transformation process
    (i.e. initialises the worker process and keeps the zmq communication between the worker
    and the forwarder)
    :return: The TransformCom object
    """
    push_port, receiving_topics, _, parameters_topic, verbose = parse_arguments_to_com(sys.argv)
    verbose = verbose == 'True'

    com_object = SinkCom(receiving_topics=receiving_topics, parameters_topic=parameters_topic,
                         push_port=push_port, worker_exec=process_exec_file, verbose=verbose)
    com_object.connect_sockets()
    com_object.start_heartbeat_thread()
    com_object.start_worker()

    return com_object


def start_the_sink_worker_process(work_function, end_of_life_function):
    """
    Starts the _worker process of the Transform that grabs link from the _com process, does something with them
    and sends them back to the _com process. It also grabs any updates of the parameters of the worker function
    :return: The TransformWorker object
    """

    pull_port, parameters_topic, receiving_topics, verbose = parse_arguments_to_worker(sys.argv)
    verbose = verbose == 'True'

    buffer = {}
    for rt in receiving_topics:
        buffer[rt] = []

    worker_object = SinkWorker(recv_topics_buffer=buffer, pull_port=pull_port, work_function=work_function,
                               end_of_life_function=end_of_life_function, parameters_topic=parameters_topic,
                               verbose=verbose)
    worker_object.connect_sockets()

    return worker_object


