
import atexit
import signal
import time
import threading
import zmq
import os
from Heron.communication.socket_for_serialization import Socket
from Heron import constants as ct
from Heron.communication.ssh_com import SSHCom


class SinkCom:

    def __init__(self, receiving_topics, parameters_topic, push_port, worker_exec, verbose=True,
                 ssh_local_server_id='None', ssh_remote_server_id='None'):
        self.receiving_topics = receiving_topics
        self.parameters_topic = parameters_topic
        self.push_data_port = push_port
        self.push_heartbeat_port = str(int(self.push_data_port) + 1)
        self.worker_exec = worker_exec
        self.verbose = verbose
        self.heartbeat_loop_running = True
        self.ssh_com = SSHCom(self.worker_exec, ssh_local_server_id, ssh_remote_server_id)

        self.port_sub_data = ct.DATA_FORWARDER_PUBLISH_PORT
        self.port_pub_parameters = ct.PARAMETERS_FORWARDER_SUBMIT_PORT
        self.poller = zmq.Poller()

        self.context = None
        self.socket_sub_data = None
        self.stream_sub = None
        self.socket_push_data = None
        self.socket_push_heartbeat = None

        self.index = -1

        atexit.register(self.on_kill)
        signal.signal(signal.SIGTERM, self.on_kill)

    def connect_sockets(self):
        """
        Start the required sockets to communicate with the link forwarder and the worker_com processes
        :return: Nothing
        """
        if self.verbose:
            print('Starting Sink Node with PID = {}'.format(os.getpid()))
        self.context = zmq.Context()

        # Socket for subscribing to data from nodes connected to the input
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
        self.socket_push_data.bind(r"tcp://127.0.0.1:{}".format(self.push_data_port))

        # Socket for pushing the heartbeat to the worker_exec
        self.socket_push_heartbeat = self.context.socket(zmq.PUSH)
        self.socket_push_heartbeat.setsockopt(zmq.LINGER, 0)
        self.socket_push_heartbeat.bind(r'tcp://127.0.0.1:{}'.format(self.push_heartbeat_port))
        self.socket_push_heartbeat.set_hwm(1)

    def heartbeat_loop(self):
        """
        The loop that send a 'PULSE' heartbeat to the worker_exec process to keep it alive (every ct.HEARTBEAT_RATE seconds)
        :return: Nothing
        """
        while self.heartbeat_loop_running:
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

        if 'python' in self.worker_exec or '.py' not in self.worker_exec:
            arguments_list = [self.worker_exec]
        else:
            arguments_list = ['python']
            arguments_list.append(self.worker_exec)

        arguments_list.append(str(self.push_data_port))
        arguments_list.append(str(self.parameters_topic))
        arguments_list.append(str(len(self.receiving_topics)))
        for i in range(len(self.receiving_topics)):
            arguments_list.append(self.receiving_topics[i])
        arguments_list.append(str(self.verbose))
        arguments_list = self.ssh_com.add_local_server_info_to_arguments(arguments_list)

        #self.worker_pid = subprocess.Popen(arguments_list)
        worker_pid = self.ssh_com.start_process(arguments_list)

        if self.verbose:
            print('Starting Sink worker {} with PID = {} getting data from .'.format(self.worker_exec,
                                                                                     self.receiving_topics, worker_pid))

    def get_sub_data(self):
        """
        Gets the link from the forwarder. It assumes that each message has four parts:
        The topic
        The data_index, an int that increases by one for every message the previous node sends
        The data_time, the time.perf_counter() result at the time the previous node send its message
        The messagedata, the array of link
        :return: Nothing
        """
        topic = self.socket_sub_data.recv()
        data_index = self.socket_sub_data.recv()
        data_time = self.socket_sub_data.recv()
        messagedata = self.socket_sub_data.recv_array()

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
        while True:
            # Get link from subsribed node
            t1 = time.perf_counter()

            sockets_in = dict(self.poller.poll(timeout=0))
            #while not sockets_in:
            #    sockets_in = dict(self.poller.poll(timeout=0))

            #t2 = time.perf_counter()

            if self.socket_sub_data in sockets_in and sockets_in[self.socket_sub_data] == zmq.POLLIN:
                topic, data_index, data_time, messagedata = self.get_sub_data()

                if self.verbose:
                    print("-Sink from {}, data_index {} at time {}".format(topic, data_index, data_time))

                # Send link to be transformed to the worker_exec
                self.socket_push_data.send(topic, flags=zmq.SNDMORE)
                self.socket_push_data.send_array(messagedata, copy=False)
                t3 = time.perf_counter()

                if self.verbose:
                    #print("---Time waiting for new data = {}".format((t2 - t1) * 1000))
                    print("---Time to transport link from worker_exec to worker_exec = {}".format((t3 - t1) * 1000))

    def on_kill(self, signal, frame):
        try:
            self.heartbeat_loop_running = False
            self.poller.unregister(socket=self.socket_sub_data)
            self.socket_sub_data.close()
            self.socket_push_data.close()
            self.socket_push_heartbeat.close()
        except Exception as e:
            print('Trying to kill Sink com {} failed with error: {}'.format(self.sending_topic, e))
        finally:
            self.context.term()