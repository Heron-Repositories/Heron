
import platform
import os
import time
import sys
import signal
import math
from struct import *
import logging
import psutil
import json
import numpy as np
from pathlib import Path
from Heron.communication.source_com import SourceCom
from Heron.communication.source_worker import SourceWorker
from Heron.communication.transform_com import TransformCom
from Heron.communication.transform_worker import TransformWorker
from Heron.communication.sink_com import SinkCom
from Heron.communication.sink_worker import SinkWorker


def convert_to_number (s):
    return int.from_bytes(s.encode(), 'little')


def convert_from_number (n):
    return n.to_bytes(math.ceil(n.bit_length() / 8), 'little').decode()


def base10_to_base256(number, normalise=False):
    pixels = np.array([0, 0, 0])
    i = 0
    while number > 256:
        pixels[i] = (number % 255)
        number = int(number / 255)
        i += 1
    pixels[i] = number
    pixels = pixels / 255 if normalise else pixels
    return pixels


def full_split_path(path):
    """
    Splits a path to its constituent folders and returns a list of all of the folders
    :param path: The path string
    :return: The list of strings of folders
    """
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
    """
    Function to provide accurate time delay in millisecond
    :param delay: Delay in milliseconds
    :return: Nothing
    """
    target_time = time.perf_counter() + delay/1000
    while time.perf_counter() < target_time:
        pass


def print_and_logging(message):
    print(message)
    logging.debug(message)


def choose_color_according_to_operations_type(operations_parent_name):
    """
    Returns a colour to colour the operations list in the gui according to the type they belong to
    :param operations_parent_name: Name of operation (it included the type)
    :return: The colour
    """
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
    :return: A new int +step larger than the previous one returned
    """
    while True:
        yield str(starting_port)
        starting_port = starting_port + step


def add_heron_to_pythonpath():
    heron_path = os.Path(os.path.dirname(os.path.realpath(__file__)))


def register_exit_signals(function_to_register):
    """
    In windows it registers a function to the SIGBREAK signal, while in linux to the SIGTERM signal
    :param function_to_register: The function to register
    :return: Nothing
    """
    if platform.system() == 'Windows':
        signal.signal(signal.SIGBREAK, function_to_register)
    elif platform.system() == 'Linux':
        signal.signal(signal.SIGTERM, function_to_register)


def setup_logger(name, log_file, level=logging.DEBUG):

    formatter = logging.Formatter(fmt='%(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def add_timestamp_to_filename(file_name, datetime):

    filename = file_name.split('.')
    date_time = '{}'.format(datetime).replace(':', '-').replace(' ', '_').split('.')[0]
    file_name = '{}_{}.{}'.format(filename[0], date_time, filename[1])
    return file_name


def pin_process_to_core(affinity):
    affinity = [int(affinity)]
    proc = psutil.Process()  # get self pid
    aff_before = proc.cpu_affinity()
    proc.cpu_affinity(affinity)
    aff_after = proc.cpu_affinity()
    print('Setting CPU affinity of Com process with PID: {} (and its Worker process) from {} to {}'
          .format(proc.pid, aff_before, aff_after))


def get_ssh_info_file():
    ssh_info_file = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))), 'communication',
                                 'ssh_info.json')
    if not os.path.exists(ssh_info_file):
        with open(ssh_info_file, 'w+') as f:
            json.dump({"0": {
                "Name": "localhost",
                "IP": "192.168.126.1",
                "Port": 22,
                "username": "user",
                "password": "None"
            }}, f, indent=4)
    with open(ssh_info_file) as f:
        ssh_info = json.load(f)

    return ssh_info

def parse_arguments_to_com(args):
    """
    Turns the list of argv arguments that is sent to a com process (by the editor) into appropriate list of strings
    and lists (of topics). It is up to the node's start_exec function to create a list of argv that can be properly
    parsed.
    :param args: The argv returned by the sys.argv
    :return: port = the initial port for the com process,
    receiving_topics = a list of the names of the topics the process receives (inputs) link at
    sending_topics = a list of the names of the topics the process sends (outputs) link at
    parameters_topic = the node_name of the topic the process receives parameter updates from the node
    verbose = Whether to print out comments while running
    ssh_local_server = The ID of the local ssh server (see ssh_info.json) if the node is to run its worker_exec over ssh
    ssh_remote_server = The ID of the remote ssh server (see ssh_info.json) if the node is to run its worker_exec over ssh
    worker_exec = The python script (or executable) of the worker_exec process
    cpu_to_pin = The cpu core to pin the Com and Worker executables
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
    parameters_topic = args[-6]
    verbose = args[-5]
    ssh_local_server = args[-4]
    ssh_remote_server = args[-3]
    worker_exec = args[-2]
    cpu_to_pin = args[-1]

    return port, receiving_topics, sending_topics, parameters_topic, verbose, \
        ssh_local_server, ssh_remote_server, worker_exec, cpu_to_pin


def parse_arguments_to_worker(args):
    """
    Turns the list of argv arguments that is send to a com process (by the editor) into appropriate list of strings
    and lists (of topics). It is up to the com's start_worker function (in the *Com.start_worker functions) to create a
    list of argv that can be properly parsed.
    :param args: The argv returned by the sys.argv
    :return: port = the initial port for the worker_exec process,
    parameters_topic = the node_name of the topic the process receives parameter updates from the node
    receiving_topics = a list of the names of the topics the process receives (inputs) link at
    verbose = the verbosity of the worker_exec process (True or False)
    ssh_local_ip = The ip of the local computer (the one running the Heron GUI)
    ssh_local_username = The username of the ssh server running on the local computer
    ssh_local_password = The password of the ssh server running on the local computer
    """
    args = args[1:]
    port = args[0]
    parameters_topic = args[1]
    num_of_receiving_topics = int(args[2])
    receiving_topics = []
    for i in range(num_of_receiving_topics):
        receiving_topics.append(args[i+3])
    num_sending_topics = args[-5]
    savestate_folder = args[-4]
    ssh_local_ip = args[-3]
    ssh_local_username = args[-2]
    ssh_local_password = args[-1]

    return port, parameters_topic, receiving_topics, num_sending_topics, savestate_folder,\
           ssh_local_ip, ssh_local_username, ssh_local_password


def start_the_source_communications_process(node_attribute_type, node_attribute_names):
    """
    Creates a SourceCom object for a source process
    (i.e. initialises the worker_exec process and keeps the zmq communication between the worker_exec and the forwarders)
    :return: The SourceCom object
    """

    push_port, _, sending_topics, parameters_topic, verbose, ssh_local_server_id, ssh_remote_server_id, worker_exec,\
        cpu_to_pin = parse_arguments_to_com(sys.argv)

    outputs = []
    for i, t in enumerate(node_attribute_type):
        if 'Output' in t:
            outputs.append(node_attribute_names[i])

    com_object = SourceCom(sending_topics=sending_topics, parameters_topic=parameters_topic, port=push_port,
                           worker_exec=worker_exec, verbose=verbose, ssh_local_server_id=ssh_local_server_id,
                           ssh_remote_server_id=ssh_remote_server_id, outputs=outputs, cpu_to_pin=cpu_to_pin)

    com_object.connect_sockets()
    com_object.start_heartbeat_thread()
    com_object.start_worker_process()

    return com_object


def start_the_source_worker_process(work_function, end_of_life_function, initialisation_function=None):
    """
    Creates a SourceWorker for a worker_exec process of a Source
    :param work_function:
    :return:
    """
    port, parameters_topic, _, num_sending_topics, savestate_folder, ssh_local_ip, ssh_local_username, ssh_local_password\
        = parse_arguments_to_worker(sys.argv)

    worker_object = SourceWorker(port=port, parameters_topic=parameters_topic,
                                 initialisation_function=initialisation_function,
                                 end_of_life_function=end_of_life_function,
                                 num_sending_topics=num_sending_topics, savenodestate_path=savestate_folder,
                                 ssh_local_ip=ssh_local_ip, ssh_local_username=ssh_local_username,
                                 ssh_local_password=ssh_local_password)
    worker_object.connect_socket()
    worker_object.start_heartbeat_thread()
    worker_object.start_parameters_thread()
    work_function(worker_object)


def start_the_transform_communications_process(node_attribute_type, node_attribute_names):
    """
    Creates a TransformCom object for a transformation process
    (i.e. initialises the worker_exec process and keeps the zmq communication between the worker_exec
    and the forwarder)
    :return: The TransformCom object
    """
    push_port, receiving_topics, sending_topics, parameters_topic, verbose, ssh_local_server_id, ssh_remote_server_id,\
        worker_exec, cpu_to_pin = parse_arguments_to_com(sys.argv)

    outputs = []
    for i, t in enumerate(node_attribute_type):
        if 'Output' in t:
            outputs.append(node_attribute_names[i])

    com_object = TransformCom(sending_topics=sending_topics, receiving_topics=receiving_topics,
                              parameters_topic=parameters_topic, push_port=push_port, worker_exec=worker_exec,
                              verbose=verbose, ssh_local_server_id=ssh_local_server_id,
                              ssh_remote_server_id=ssh_remote_server_id, outputs=outputs, cpu_to_pin=cpu_to_pin)
    com_object.connect_sockets()
    com_object.start_heartbeat_thread()
    com_object.start_worker()

    return com_object


def start_the_transform_worker_process(work_function, end_of_life_function, initialisation_function=None):
    """
    Starts the _worker process of the Transform that grabs link from the _com process, does something with them
    and sends them back to the _com process. It also grabs any updates of the parameters of the worker_exec function
    :return: The TransformWorker object
    """
    pull_port, parameters_topic, receiving_topics, num_sending_topics, savestate_folder, ssh_local_ip, ssh_local_username, \
        ssh_local_password = parse_arguments_to_worker(sys.argv)

    buffer = {}
    for rt in receiving_topics:
        buffer[rt] = []

    worker_object = TransformWorker(recv_topics_buffer=buffer, pull_port=pull_port,
                                    initialisation_function=initialisation_function, work_function=work_function,
                                    end_of_life_function=end_of_life_function, parameters_topic=parameters_topic,
                                    num_sending_topics=num_sending_topics, savenodestate_path=savestate_folder,
                                    ssh_local_ip=ssh_local_ip, ssh_local_username=ssh_local_username,
                                    ssh_local_password=ssh_local_password)
    worker_object.connect_sockets()

    return worker_object


def start_the_sink_communications_process():
    """
    Creates a Sink object for a sink process
    (i.e. initialises the worker_exec process and keeps the zmq communication between the worker_exec
    and the forwarder)
    :return: The SinkCom object
    """
    push_port, receiving_topics, _, parameters_topic, verbose, ssh_local_server_id, ssh_remote_server_id, worker_exec,\
        cpu_to_pin = parse_arguments_to_com(sys.argv)

    com_object = SinkCom(receiving_topics=receiving_topics, parameters_topic=parameters_topic,
                         push_port=push_port, worker_exec=worker_exec, verbose=verbose,
                         ssh_local_server_id=ssh_local_server_id, ssh_remote_server_id=ssh_remote_server_id,
                         cpu_to_pin=cpu_to_pin)
    com_object.connect_sockets()
    com_object.start_heartbeat_thread()
    com_object.start_worker()

    return com_object


def start_the_sink_worker_process(work_function, end_of_life_function, initialisation_function=None):
    """
    Starts the _worker process of the Sink that grabs link from the _com process, does something with them
    and sends them back to the _com process. It also grabs any updates of the parameters of the worker_exec function
    :return: The SinkWorker object
    """

    pull_port, parameters_topic, receiving_topics, num_sending_topics, savestate_folder, ssh_local_ip, ssh_local_username, \
        ssh_local_password = parse_arguments_to_worker(sys.argv)

    buffer = {}
    for rt in receiving_topics:
        buffer[rt] = []

    worker_object = SinkWorker(recv_topics_buffer=buffer, pull_port=pull_port,
                               initialisation_function=initialisation_function, work_function=work_function,
                               end_of_life_function=end_of_life_function, parameters_topic=parameters_topic,
                               num_sending_topics=num_sending_topics, savenodestate_path=savestate_folder,
                               ssh_local_ip=ssh_local_ip, ssh_local_username=ssh_local_username,
                               ssh_local_password=ssh_local_password)
    worker_object.connect_sockets()

    return worker_object


