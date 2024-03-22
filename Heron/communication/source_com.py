
from datetime import datetime
import os
import zmq
import time
import threading
import numpy as np
import psutil

from Heron import constants as ct, general_utils as gu
from Heron.communication.socket_for_serialization import Socket
from zmq.eventloop import ioloop, zmqstream
from Heron.communication.ssh_com import SSHCom


class SourceCom:
    def __init__(self, sending_topics, parameters_topic, port, worker_exec, verbose='||',
                 ssh_local_server_id='None', ssh_remote_server_id='None', outputs=None, cpu_to_pin='Any'):
        self.sending_topics = sending_topics
        self.parameters_topic = parameters_topic
        self.pull_data_port = port
        self.heartbeat_port = str(int(self.pull_data_port) + 1)
        self.worker_exec = worker_exec
        self.index = 0
        self.time = int(1000000 * time.perf_counter())
        self.previous_time = self.time
        self.verbose, self.relic = self.define_verbosity_and_relic(verbose)

        self.all_loops_running = True
        self.ssh_com = SSHCom(self.worker_exec, ssh_local_server_id, ssh_remote_server_id)
        self.outputs = outputs
        self.port_pub = ct.DATA_FORWARDER_SUBMIT_PORT
        self.cpu_to_pin = cpu_to_pin
        if cpu_to_pin != 'Any':
            gu.pin_process_to_core(cpu_to_pin)

        self.context = None
        self.socket_pub_data = None
        self.socket_pull_data = None
        self.stream_pull_data = None
        self.socket_push_heartbeat = None
        self.average_sending_time = 0

        # If self.verbose is a string it is the file name to log things in. If it is an int it is the level of the verbosity
        self.logger = None
        if self.verbose != 0:
            try:
                self.verbose = int(self.verbose)
            except:
                log_file_name = gu.add_timestamp_to_filename(self.verbose, datetime.now())
                self.logger = gu.setup_logger('Source', log_file_name)
                self.logger.info('Index of data packet : Computer Time Data Out')
                self.verbose = False

    def connect_sockets(self):
        """
        Start the required sockets to communicate with the link forwarder and the source_com processes
        :return: Nothing
        """
        if self.verbose:
            print('Starting Source Node with PID = {}'.format(os.getpid()))
        self.context = zmq.Context()

        # Socket for pulling the data from the worker_exec
        self.socket_pull_data = Socket(self.context, zmq.PULL)
        self.socket_pull_data.setsockopt(zmq.LINGER, 0)
        self.socket_pull_data.set_hwm(1)
        self.socket_pull_data.connect(r"tcp://127.0.0.1:{}".format(self.pull_data_port))

        self.stream_pull_data = zmqstream.ZMQStream(self.socket_pull_data)
        self.stream_pull_data.on_recv(self.on_receive_data_from_worker)

        # Socket for publishing the data to the data forwarder
        self.socket_pub_data = Socket(self.context, zmq.PUB)
        self.socket_pub_data.setsockopt(zmq.LINGER, 0)
        self.socket_pub_data.set_hwm(len(self.sending_topics))
        self.socket_pub_data.connect(r"tcp://127.0.0.1:{}".format(self.port_pub))

        # Socket for publishing the heartbeat to the worker_exec
        self.socket_push_heartbeat = self.context.socket(zmq.PUSH)
        self.socket_push_heartbeat.setsockopt(zmq.LINGER, 0)
        self.socket_push_heartbeat.bind(r'tcp://*:{}'.format(self.heartbeat_port))
        self.socket_push_heartbeat.set_hwm(1)

    def define_verbosity_and_relic(self, verbosity_string):
        """
        Splits the string that comes from the Node as verbosity_string into the string (or int) for the logging/printing
        (self.verbose) and the string that carries the path where the relic is to be saved. The self.relic is then
        passed to the worker process
        :param verbosity_string: The string with syntax verbosity||relic
        :return: (int)str vebrose, str relic
        """
        if verbosity_string != '':
            verbosity, relic = verbosity_string.split('||')
            if relic == '':
                relic = '_'
            if verbosity == '':
                return 0, relic
            else:
                return verbosity, relic
        else:
            return 0, ''

    def on_receive_data_from_worker(self, msg):
        """
        The callback that runs every time link is received from the worker_exec process. It takes the link and passes it
        onto the link forwarder
        :param msg: The link packet (carrying the actual link (np array))
        :return:
        """
        # A specific worker with multiple outputs should send from its infinite loop a message with multiple parts
        # (using multiple send_data(data, flags=zmq.SNDMORE) commands). For an example see how the transform_worker
        # sends data to the com from its data_callback function
        # TODO The bellow will not work for multiple outputs. I have to find out how many times a callback is called
        #  when data are send with SNDMORE flag !!!

        ignoring_outputs = [False] * len(self.outputs)
        new_message_data = []
        if len(self.outputs) > 1:
            for i in range(len(self.outputs)):
                array_data = Socket.reconstruct_data_from_bytes_message(msg[i])
                new_message_data.append(array_data)
                if type(array_data[0]) == np.str_:
                    if array_data[0] == ct.IGNORE:
                        ignoring_outputs[i] = True
        else:
            array_data = Socket.reconstruct_data_from_bytes_message(msg)
            new_message_data.append(array_data)
            if type(array_data[0]) == np.str_:
                if array_data[0] == ct.IGNORE:
                    ignoring_outputs[0] = True

        self.time = int(1000000 * time.perf_counter())
        self.index = self.index + 1

        # Publish the results. Each array in the list of arrays is published to its own sending topic
        # (matched by order)
        for i, st in enumerate(self.sending_topics):
            for k, output in enumerate(self.outputs):
                if output.replace(' ', '_') in st.split('##')[0]:
                    break

            if ignoring_outputs[k] is False:
                self.socket_pub_data.send("{}".format(st).encode('ascii'), flags=zmq.SNDMORE)
                self.socket_pub_data.send("{}".format(self.index).encode('ascii'), flags=zmq.SNDMORE)
                self.socket_pub_data.send("{}".format(self.time).encode('ascii'), flags=zmq.SNDMORE)
                self.socket_pub_data.send_data(new_message_data[k], copy=False)
                # This delay is critical to get single output to multiple inputs to work!
                gu.accurate_delay(ct.DELAY_BETWEEN_SENDING_DATA_TO_NEXT_NODE_MILLISECONDS)

            if self.verbose:
                dt = self.time - self.previous_time
                if self.index > 3:
                    self.average_sending_time = self.average_sending_time * (self.index - 1) / self.index + dt / self.index
                print('----------')
                print("Source with topic {} sending packet with data_index {} at time {}".format(self.sending_topics[i],
                                                                                                 self.index, self.time))
                print('Time Diff between packages = {}. Average package sending time = {} ms'.format(dt/1000, self.average_sending_time / 1000))
            if self.logger:
                self.logger.info('{} : {}'.format(self.index, datetime.now()))
            self.previous_time = self.time

    def heartbeat_loop(self):
        """
        Sending every ct.HEARTBEAT_RATE a 'PULSE' to the worker_exec so that it stays alive
        :return: Nothing
        """
        while self.all_loops_running:
            self.socket_push_heartbeat.send_string('PULSE')
            time.sleep(ct.HEARTBEAT_RATE)

    def start_heartbeat_thread(self):
        """
        Starts the daemon thread that runs the self.heartbeat loop
        :return: Nothing
        """
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()

    def start_worker_process(self):
        """
        Starts the worker_exec process and then sends the parameters as are currently on the node to the process
        The pull_data_port of the worker_exec needs to be the push_data_port of the com (obviously).
        The way the arguments are structured is defined by the way they are read by the process. For that see
        general_utilities.parse_arguments_to_worker
        :return: Nothing
        """
        if ('python' in self.worker_exec and os.sep+'python' not in self.worker_exec) or '.py' not in self.worker_exec:
            arguments_list = [self.worker_exec]
        else:
            arguments_list = ['python']
            arguments_list.append(self.worker_exec)

        arguments_list.append(str(self.pull_data_port))
        arguments_list.append(str(self.parameters_topic))
        arguments_list.append(str(0))
        arguments_list.append(str(len(self.sending_topics)))
        arguments_list.append(self.relic)
        arguments_list = self.ssh_com.add_local_server_info_to_arguments(arguments_list)

        worker_pid = self.ssh_com.start_process(arguments_list)
        self.ssh_com.connect_socket_to_remote(self.socket_pull_data,
                                              r"tcp://127.0.0.1:{}".format(self.pull_data_port))

    def start_ioloop(self):
        """
        Starts the ioloop of the zmqstream
        :return: Nothing
        """
        ioloop.IOLoop.instance().start()

    def on_kill(self, signal, frame):
        """
        The function that is called when the parent process sends a SIGBREAK (windows) or SIGTERM (linux) signal.
        It needs signal and frame as parameters
        :param signal: The signal received
        :param frame: I haven't got a clue
        :return: Nothing
        """
        try:
            self.all_loops_running = False
            self.stream_pull_data.close(linger=0)
            self.socket_pull_data.close()
            self.socket_pub_data.close()
            self.socket_push_heartbeat.close()
        except Exception as e:
            print('Trying to kill Source com {} failed with error: {}'.format(self.sending_topics[0], e))
        finally:
            self.context.term()












