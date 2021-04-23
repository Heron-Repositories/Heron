
import subprocess
import zmq
import atexit
import os
from Heron.communication.socket_for_serialization import Socket
from Heron.general_utils import kill_child
from Heron import constants as ct
from Heron.communication import gui_com
import time


class TransformCom:

    def __init__(self, receiving_topic, sending_topic, state_topic, push_port, pull_port, worker_exec, verbose=True):
        self.receiving_topic = receiving_topic
        self.sending_topic = sending_topic
        self.state_topic = state_topic
        self.push_port = push_port
        self.pull_port = pull_port
        self.worker_exec = worker_exec
        self.verbose = verbose

        self.port_pub_data = ct.DATA_FORWARDER_SUBMIT_PORT
        self.port_sub_data = ct.DATA_FORWARDER_PUBLISH_PORT
        self.port_pub_state = ct.STATE_FORWARDER_SUBMIT_PORT

        self.context = None
        self.socket_sub_data = None
        self.socket_push_data = None
        self.socket_pull_data = None
        self.socket_pub_data = None

        self.index = -1

    def get_sub_data(self):
        """
        Gets the data from the forwarder. It assumes that each message has four parts:
        The topic
        The data_index, an int that increases by one for every message the previous node sends
        The data_time, the time.perf_counter() result at the time the previous node send its message
        The messagedata, the array of data
        :return: Nothing
        """
        topic = self.socket_sub_data.recv()
        data_index = self.socket_sub_data.recv()
        data_time = self.socket_sub_data.recv()
        messagedata = self.socket_sub_data.recv_array()

        return topic, data_index, data_time, messagedata

    def connect_sockets(self):
        """
        Start the required sockets to communicate with the data forwarder and the worker_com processes
        :return: Nothing
        """
        if self.verbose:
            print('Starting Transform Node with PID = {}'.format(os.getpid()))
        self.context = zmq.Context()

        # Sockets for subscribing to data from previous node and pushing it to the worker
        self.socket_sub_data = Socket(self.context, zmq.SUB)
        self.socket_sub_data.set_hwm(1)
        self.socket_sub_data.connect("tcp://localhost:{}".format(self.port_sub_data))
        self.socket_sub_data.SUBSCRIBE = self.receiving_topic

        self.socket_push_data = Socket(self.context, zmq.PUSH)
        self.socket_push_data.set_hwm(1)
        self.socket_push_data.connect(r"tcp://127.0.0.1:{}".format(self.push_port))

        # Sockets for pulling data from the worker and publishing it to the next Operations
        self.socket_pull_data = Socket(self.context, zmq.PULL)
        self.socket_pull_data.set_hwm(1)
        self.socket_pull_data.bind(r"tcp://127.0.0.1:{}".format(self.pull_port))

        self.socket_pub_data = Socket(self.context, zmq.PUB)
        self.socket_pub_data.set_hwm(1)
        self.socket_pub_data.connect(r"tcp://localhost:{}".format(self.port_pub_data))

    @staticmethod
    def publish_parameters_to_worker(topic, arguments_list):
        """
        Uses the gui's publish state socket to publish the argument_list with the correct topic. This will be read by
        the worker's subscribe state socket (which subscribes to the specific topic) and update the parameters that the
        worker's work function is using
        :return: Nothing
        """
        gui_com.SOCKET_PUB_STATE.send_string(topic, flags=zmq.SNDMORE)
        gui_com.SOCKET_PUB_STATE.send_pyobj(arguments_list)

    def start_worker(self, arguments_list):
        """
        Starts the worker process and then sends the parameters as are currently on the node to the process
        :param arguments_list: The argument list that has all the parameters for the worker (as given in the node's gui)
        :return: Nothing
        """
        worker = subprocess.Popen(
            ['python', self.worker_exec, str(self.pull_port), str(self.push_port), str(self.state_topic),
             str(self.verbose)])
        atexit.register(kill_child, worker.pid)

        if self.verbose:
            print('Transform from {} to {} worker com with PID = {}.'.format(self.receiving_topic,
                                                                             self.sending_topic,
                                                                             worker.pid))

        # We need to send the parameter values on the node to the worker right after it starts.
        time.sleep(0.5) # Allow the worker process to start before sending the current parameters
        self.publish_parameters_to_worker(self.state_topic, arguments_list)

    def start_ioloop(self):
        """
        Start the io loop for the transform node. It reads the data from the previous node's _com process,
        pushes it to the worker_com process,
        waits for the results,
        grabs the resulting data from the worker_com process and
        publishes the transformed data to the data forwarder with this nodes' topic
        :return: Nothing
        """
        while True:

            # Get data from subsribed node
            t1 = time.perf_counter()
            _, data_index, data_time, messagedata = self.get_sub_data()
            if self.verbose:
                print("-Transform from {} to {}, index {} at time {}".format(self.receiving_topic,
                                                                             self.sending_topic,
                                                                             data_index,
                                                                             data_time))

            # Send data to be transformed to the worker
            self.socket_push_data.send_array(messagedata, copy=False)
            t2 = time.perf_counter()

            # Get the transformed data (wait for it)
            new_message_data = self.socket_pull_data.recv_array()
            results_time = int(1000000 * time.perf_counter())

            if self.verbose:
                print('--Results got back at time {}'.format(results_time))

            # Publish the results
            self.socket_pub_data.send("{}".format(self.sending_topic).encode('ascii'), flags=zmq.SNDMORE)
            self.socket_pub_data.send("{}".format(self.index).encode('ascii'), flags=zmq.SNDMORE)
            self.socket_pub_data.send("{}".format(results_time).encode('ascii'), flags=zmq.SNDMORE)
            self.socket_pub_data.send_array(new_message_data, copy=False)
            t3 = time.perf_counter()

            if self.verbose:
                print("---Times to: i) transport data from worker to worker = {}, "
                      "2) publish transformed data = {}".format((t2 - t1) * 1000, (t3 - t1) * 1000))

