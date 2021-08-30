
from datetime import datetime
import os
import zmq
import time
import threading

from Heron import constants as ct, general_utils as gu
from Heron.communication.socket_for_serialization import Socket
from zmq.eventloop import ioloop, zmqstream
from Heron.communication.ssh_com import SSHCom


class SourceCom:
    def __init__(self, sending_topics, parameters_topic, port, worker_exec, verbose='',
                 ssh_local_server_id='None', ssh_remote_server_id='None', multiple_outputs=None):
        self.sending_topics = sending_topics
        self.parameters_topic = parameters_topic
        self.pull_data_port = port
        self.heartbeat_port = str(int(self.pull_data_port) + 1)
        self.worker_exec = worker_exec
        self.index = 0
        self.time = int(1000000 * time.perf_counter())
        self.previous_time = self.time
        self.verbose = verbose
        self.all_loops_running = True
        self.ssh_com = SSHCom(self.worker_exec, ssh_local_server_id, ssh_remote_server_id)
        self.multiple_outputs = multiple_outputs

        self.port_pub = ct.DATA_FORWARDER_SUBMIT_PORT

        self.context = None
        self.socket_pub_data = None
        self.socket_pull_data = None
        self.stream_pull_data = None
        self.socket_push_heartbeat = None
        self.average_sending_time = 0

        # If self.verbose is a string it is the file name to log things in. If it is an int it is the level of the verbosity
        self.logger = None
        if self.verbose != '':
            try:
                self.verbose = int(self.verbose)
            except:
                log_file_name =  gu.add_timestamp_to_filename(self.verbose, datetime.now())
                self.logger = gu.setup_logger('Source', log_file_name)
                self.logger.info('Index of data packet : Computer Time')
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

    def on_receive_data_from_worker(self, msg):
        """
        The callback that runs every time link is received from the worker_exec process. It takes the link and passes it
        onto the link forwarder
        :param msg: The link packet (carrying the actual link (np array))
        :return:
        """
        # The node_index of the link packet is the system's time in microseconds
        data = Socket.reconstruct_array_from_bytes_message(msg)

        new_message_data = []
        if len(self.sending_topics) > 1:
            for i in range(len(self.sending_topics)):
                new_message_data.append(data[i])
        else:
            new_message_data.append(data)

        self.time = int(1000000 * time.perf_counter())
        self.index = self.index + 1

        # Publish the results. Each array in the list of arrays is published to its own sending topic
        # (matched by order)
        for st in self.sending_topics:
            if st != 'NothingOut':
                topic_output_attr = st.split('##')[0]
                if self.multiple_outputs is not None:
                    for mi, mo in enumerate(self.multiple_outputs):
                        if mo in topic_output_attr:
                            i = mi
                else:
                    i = 0

                self.socket_pub_data.send("{}".format(st).encode('ascii'), flags=zmq.SNDMORE)
                self.socket_pub_data.send("{}".format(self.index).encode('ascii'), flags=zmq.SNDMORE)
                self.socket_pub_data.send("{}".format(self.time).encode('ascii'), flags=zmq.SNDMORE)
                self.socket_pub_data.send_array(new_message_data[i], copy=False)

        #self.socket_pub_data.send("{}".format(self.sending_topic).encode('ascii'), flags=zmq.SNDMORE)
        #self.socket_pub_data.send("{}".format(self.index).encode('ascii'), flags=zmq.SNDMORE)
        #self.socket_pub_data.send("{}".format(self.time).encode('ascii'), flags=zmq.SNDMORE)
        #self.socket_pub_data.send_array(data, copy=False)

        if self.verbose:
            dt = self.time - self.previous_time
            if self.index > 3:
                self.average_sending_time = self.average_sending_time * (self.index - 1) / self.index + dt / self.index
            print('----------')
            print("Source with topic {} sending packet with data_index {} at time {}".format(self.sending_topic, self.index, self.time))
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
        if 'python' in self.worker_exec or '.py' not in self.worker_exec:
            arguments_list = [self.worker_exec]
        else:
            arguments_list = ['python']
            arguments_list.append(self.worker_exec)

        arguments_list.append(str(self.pull_data_port))
        arguments_list.append(str(self.parameters_topic))
        arguments_list.append(str(0))
        arguments_list.append(str(self.verbose))
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
            print('Trying to kill Source com {} failed with error: {}'.format(self.sending_topic, e))
        finally:
            self.context.term()












