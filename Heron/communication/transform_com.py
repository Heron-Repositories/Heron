


import subprocess
import zmq
import atexit
import os
from Heron.communication.socket_for_serialization import Socket
from Heron.general_utils import kill_child
from Heron import constants as ct
import time


class TransformCom:
    def __init__(self, receiving_topic, sending_topic, push_port, pull_port, worker_exec, verbose=True):
        self.receiving_topic = receiving_topic
        self.sending_topic = sending_topic
        self.push_port = push_port
        self.pull_port = pull_port
        self.worker_exec = worker_exec
        self.verbose = verbose

        self.port_pub_data = ct.DATA_FORWARDER_SUBMIT_PORT
        self.port_sub_data = ct.DATA_FORWARDER_PUBLISH_PORT
        self.port_pub_state = ct.STATE_FORWARDER_SUBMIT_PORT
        self.port_sub_state = ct.STATE_FORWARDER_PUBLISH_PORT

        self.context = None
        self.socket_sub_data = None
        self.socket_sub_state = None
        self.socket_push_data = None
        self.socket_pull_data = None
        self.socket_pub_data = None
        self.socket_pub_state = None

        self.index = -1

    def get_sub_data(self):
        topic = self.socket_sub_data.recv()
        data_index = self.socket_sub_data.recv()
        messagedata = self.socket_sub_data.recv_array()

        return topic, data_index, messagedata

    def connect_sockets(self):
        if self.verbose:
            print('Starting Transform Node with PID = {}'.format(os.getpid()))
        self.context = zmq.Context()

        # Sockets for subscribing to data from previous node and pushing it to the worker
        self.socket_sub_state = Socket(self.context, zmq.SUB)
        self.socket_sub_state.CONFLATE = 1
        self.socket_sub_state.connect(r'tcp://localhost:{}'.format(self.port_sub_state))
        self.socket_sub_state.SUBSCRIBE = ""

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

        self.socket_pub_state = Socket(self.context, zmq.PUB)
        self.socket_pub_state.CONFLATE = 1
        self.socket_pub_state.connect(r"tcp://localhost:{}".format(self.port_pub_state))

        self.socket_pub_data = Socket(self.context, zmq.PUB)
        self.socket_pub_data.set_hwm(1)
        self.socket_pub_data.connect(r"tcp://localhost:{}".format(self.port_pub_data))

    def start_worker(self):
        worker = subprocess.Popen(
            ['python', self.worker_exec, str(self.pull_port), str(self.push_port)])

        if self.verbose:
            print('Transform from {} to {} worker com with PID = {}.'.format(self.receiving_topic, self.sending_topic, worker.pid))

        atexit.register(kill_child, worker.pid)

    def start_ioloop(self):
        while True:

            # GOld code using the state index
            #while self.index == self.socket_sub_state.recv_string():
            #    pass
            #self.index = self.socket_sub_state.recv_string()
            #_, data_index, messagedata = self.get_sub_data()

            #while int(self.index) > int(data_index):

            # Get data from subsribed node
            t1 = time.perf_counter()
            _, data_index, messagedata = self.get_sub_data()
            if self.verbose:
                print("-Transform from {} to {}, index {}".format(self.receiving_topic,
                                                                                self.sending_topic,
                                                                                data_index))

            # Send data to be transformed to the worker
            self.socket_push_data.send_array(messagedata, copy=False)
            t2 = time.perf_counter()
            # Get the transformed data (wait for it)
            new_message_data = self.socket_pull_data.recv_array()


            # Publish the data's index and the data
            self.socket_pub_state.send_string(str(self.index))

            self.socket_pub_data.send("{}".format(self.sending_topic).encode('ascii'), flags=zmq.SNDMORE)
            self.socket_pub_data.send("{}".format(self.index).encode('ascii'), flags=zmq.SNDMORE)
            self.socket_pub_data.send_array(new_message_data, copy=False)
            t3 = time.perf_counter()

            if self.verbose:
                print("---Times to: i) transport data from worker to worker = {}, 2) publish transformed data = {}".format((t2 - t1) * 1000,
                                                                                                     (t3 - t1) * 1000))

