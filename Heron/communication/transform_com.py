
import numpy as np
import time
import threading
import zmq
import os
import psutil

from datetime import datetime
from Heron.communication.socket_for_serialization import Socket
from Heron import constants as ct, general_utils as gu
from Heron.communication.ssh_com import SSHCom


class TransformCom:

    def __init__(self, receiving_topics, sending_topics, parameters_topic, push_port, worker_exec, verbose=True,
                 ssh_local_server_id='None', ssh_remote_server_id='None', outputs=None, cpu_to_pin='Any'):
        self.receiving_topics = receiving_topics
        self.sending_topics = sending_topics
        self.parameters_topic = parameters_topic
        self.push_data_port = push_port
        self.pull_data_port = str(int(self.push_data_port) + 1)
        self.push_heartbeat_port = str(int(self.push_data_port) + 2)
        self.worker_exec = worker_exec

        self.verbose, self.relic = self.define_verbosity_and_relic(verbose)

        self.all_loops_running = True
        self.ssh_com = SSHCom(self.worker_exec, ssh_local_server_id, ssh_remote_server_id)
        self.outputs = outputs
        self.cpu_to_pin = cpu_to_pin
        if cpu_to_pin != 'Any':
            gu.pin_process_to_core(cpu_to_pin)

        self.port_pub_data = ct.DATA_FORWARDER_SUBMIT_PORT
        self.port_sub_data = ct.DATA_FORWARDER_PUBLISH_PORT
        self.port_pub_parameters = ct.PARAMETERS_FORWARDER_SUBMIT_PORT
        self.poller = zmq.Poller()

        self.context = None
        self.socket_sub_data = None
        self.stream_sub = None
        self.socket_push_data = None
        self.socket_pull_data = None
        self.socket_pub_data = None
        self.socket_push_heartbeat = None

        self.index = 0

        # If self.verbose is a string it is the file name to log things in. If it is an int it is the level of the verbosity
        self.logger = None
        if self.verbose != 0:
            try:
                self.verbose = int(self.verbose)
            except:
                log_file_name = gu.add_timestamp_to_filename(self.verbose, datetime.now())
                self.logger = gu.setup_logger('Transform', log_file_name)
                self.logger.info('Index of data packet given : Index of data packet received : Topic : '
                                 'Computer Time of Data In : Computer Time of Data Out')
                self.verbose = False

    def connect_sockets(self):
        """
        Start the required sockets to communicate with the link forwarder and the worker_com processes
        :return: Nothing
        """
        if self.verbose:
            print('Starting Transform Node with PID = {}'.format(os.getpid()))
        self.context = zmq.Context()

        # Socket for subscribing to data from node connected to the input
        self.socket_sub_data = Socket(self.context, zmq.SUB)
        self.socket_sub_data.setsockopt(zmq.LINGER, 0)
        self.socket_sub_data.set_hwm(len(self.receiving_topics))
        self.socket_sub_data.connect("tcp://127.0.0.1:{}".format(self.port_sub_data))
        for rt in self.receiving_topics:
            self.socket_sub_data.setsockopt(zmq.SUBSCRIBE, rt.encode('ascii'))
        self.poller.register(self.socket_sub_data, zmq.POLLIN)

        # Socket for pushing the data to the worker_exec
        self.socket_push_data = Socket(self.context, zmq.PUSH)
        self.socket_push_data.setsockopt(zmq.LINGER, 0)
        self.socket_push_data.set_hwm(1)
        self.socket_push_data.bind(r"tcp://*:{}".format(self.push_data_port))

        # Socket for pulling transformed data from the worker_exec
        self.socket_pull_data = Socket(self.context, zmq.PULL)
        self.socket_pull_data.setsockopt(zmq.LINGER, 0)
        self.socket_pull_data.set_hwm(1)
        self.socket_pull_data.connect(r"tcp://127.0.0.1:{}".format(self.pull_data_port))

        self.poller.register(self.socket_pull_data, zmq.POLLIN)

        # Socket for publishing transformed data to the data forwarder
        self.socket_pub_data = Socket(self.context, zmq.PUB)
        self.socket_pub_data.setsockopt(zmq.LINGER, 0)
        self.socket_pub_data.set_hwm(len(self.sending_topics))
        self.socket_pub_data.connect(r"tcp://127.0.0.1:{}".format(self.port_pub_data))

        # Socket for pushing the heartbeat to the worker_exec
        self.socket_push_heartbeat = self.context.socket(zmq.PUSH)
        self.socket_push_heartbeat.bind(r'tcp://*:{}'.format(self.push_heartbeat_port))
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

    def heartbeat_loop(self):
        """
        The loop that send a 'PULSE' heartbeat to the worker_exec process to keep it alive (every ct.HEARTBEAT_RATE seconds)
        :return: Nothing
        """
        while self.all_loops_running:
            self.socket_push_heartbeat.send_string('PULSE')
            time.sleep(ct.HEARTBEAT_RATE)

    def start_heartbeat_thread(self):
        """
        The daemon thread that runs the infinite heartbeat_loop
        :return: Noting
        """
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()

    def start_worker(self):
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

        arguments_list.append(str(self.push_data_port))
        arguments_list.append(str(self.parameters_topic))
        arguments_list.append(str(len(self.receiving_topics)))
        for i in range(len(self.receiving_topics)):
            arguments_list.append(self.receiving_topics[i])
        arguments_list.append(str(len(self.sending_topics)))
        arguments_list.append(str(self.relic))
        arguments_list = self.ssh_com.add_local_server_info_to_arguments(arguments_list)

        worker_pid = self.ssh_com.start_process(arguments_list)

        self.ssh_com.connect_socket_to_remote(self.socket_pull_data,
                                                         r"tcp://127.0.0.1:{}".format(self.pull_data_port))

    def get_sub_data(self):
        """
        Gets the link from the forwarder. It assumes that each message has four parts:
        The topic
        The data_index, an int that increases by one for every message the previous node sends
        The data_time, the time.perf_counter() result at the time the previous node send its message
        The messagedata, the array of link
        :return: Nothing
        """
        prev_topic = self.socket_sub_data.recv()
        prev_data_index = self.socket_sub_data.recv()
        prev_data_time = self.socket_sub_data.recv()
        prev_messagedata = self.socket_sub_data.recv_data()
        # The following while ensures that the transform works only on the the latest available
        # message from the previous node. If the transform is too slow compared to the input node
        # this while throws all past messages away.
        while prev_topic:
            topic = prev_topic
            data_index = prev_data_index
            data_time = prev_data_time
            messagedata = prev_messagedata
            try:
                prev_topic = self.socket_sub_data.recv(zmq.NOBLOCK)
                prev_data_index = self.socket_sub_data.recv(zmq.NOBLOCK)
                prev_data_time = self.socket_sub_data.recv(zmq.NOBLOCK)
                prev_messagedata = self.socket_sub_data.recv_data(zmq.NOBLOCK)
            except:
                prev_topic = None
                pass
        return topic, data_index, data_time, messagedata

    def start_ioloop(self):
        """
        Start the io loop for the transform node. It reads the link from the previous node's _com process,
        pushes it to the worker_com process,
        waits for the results,
        grabs the resulting link from the worker_com process and
        publishes the transformed link to the link forwarder with this nodes' topic
        :return: Nothing
        """
        while self.all_loops_running:
            t1 = time.perf_counter()
            data_in_time = datetime.now()

            try:
                # The timeout=1 means things coming in faster than 1000Hz will be lost but if timeout is set to 0 then
                # the CPU utilization goes to around 10% which quickly kills the CPU (if there are 2 or 3 Transforms in
                # the pipeline)
                sockets_in = dict(self.poller.poll(timeout=1))

                while not sockets_in:
                    sockets_in = dict(self.poller.poll(timeout=1))

                if self.socket_sub_data in sockets_in and sockets_in[self.socket_sub_data] == zmq.POLLIN:
                    topic, data_index, data_time, messagedata = self.get_sub_data()
                    sockets_in = dict(self.poller.poll(timeout=1))

                    if self.verbose == 1:
                        print("--- Transform from {} to {}, data index {} at time {} s"
                              .format(topic, self.sending_topics, data_index, data_time))

                    # Send link to be transformed to the worker_exec
                    self.socket_push_data.send(topic, flags=zmq.SNDMORE)
                    self.socket_push_data.send_data(messagedata, copy=False)

                    t2 = time.perf_counter()

                # Get the transformed link (wait for the socket_pull_data to get some link from the worker_exec)
                sockets_in = dict(self.poller.poll(timeout=None))

                ignoring_outputs = [False] * len(self.outputs)
                new_message_data = []
                for i in range(len(self.outputs)):
                    header = self.socket_pull_data.recv()
                    bytes = self.socket_pull_data.recv()
                    array_data = Socket.reconstruct_data_from_bytes_message([header, bytes])
                    new_message_data.append(array_data)

                    if type(array_data) == np.ndarray:
                        if type(array_data[0]) == np.str_:
                            if array_data[0] == ct.IGNORE:
                                ignoring_outputs[i] = True

                t3 = time.perf_counter()

                if self.verbose == 1:
                    print('ooooo Results got back at time {} s ooooo'.format(t3))

                # Publish the results. Each array in the list of arrays is published to its own sending topic
                # (matched by order) assuming there is no ignore signal from the worker.
                for i, st in enumerate(self.sending_topics):
                    for k, output in enumerate(self.outputs):
                        if output.replace(' ', '_') in st.split('##')[0]:
                            break

                    if ignoring_outputs[k] is False:
                        self.socket_pub_data.send("{}".format(st).encode('ascii'), flags=zmq.SNDMORE)
                        self.socket_pub_data.send("{}".format(self.index).encode('ascii'), flags=zmq.SNDMORE)
                        self.socket_pub_data.send("{}".format(t3).encode('ascii'), flags=zmq.SNDMORE)
                        self.socket_pub_data.send_data(new_message_data[k], copy=False)

                        # This delay is critical to get single output to multiple inputs to work!
                        gu.accurate_delay(ct.DELAY_BETWEEN_SENDING_DATA_TO_NEXT_NODE_MILLISECONDS)
                t4 = time.perf_counter()

                self.index = self.index + 1

                if self.verbose == 1:
                    print("---Times to: "
                          "\n1) Transport link from previous com to worker_exec = {} ms, "
                          "\n2) Do the transformation in the worker and get back to the com the data = {} ms"
                          "\n3) Publish transformed data to the next node = {} ms" \
                          .format((t2 - t1) * 1000, (t3 - t2)*1000, (t4 - t3) * 1000))
                    print('=============================')
                if self.logger:
                    self.logger.info('{} : {} : {} : {} : {}'.format(self.index, data_index, topic, data_in_time,
                                                                     datetime.now()))
            except Exception as e:
                print(e)

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
            self.poller.unregister(socket=self.socket_sub_data)
            self.poller.unregister(socket=self.socket_pull_data)
            self.socket_sub_data.close()
            self.socket_push_data.close()
            self.socket_pull_data.close()
            self.socket_pub_data.close()
            self.socket_push_heartbeat.close()
        except Exception as e:
            print('Trying to kill Transform com {} failed with error: {}'.format(self.sending_topics, e))
        finally:
            self.context.term()