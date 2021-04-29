
import time
import threading
import pickle
import os
import signal
import zmq
from Heron import constants as ct
from Heron.communication.socket_for_serialization import Socket
from zmq.eventloop import ioloop, zmqstream


class TransformWorker:
    def __init__(self, pull_port, work_function, state_topic, verbose):

        self.pull_data_port = pull_port
        self.push_data_port = str(int(self.pull_data_port) + 1)
        self.pull_heartbeat_port = str(int(self.pull_data_port) + 2)
        self.work_function = work_function
        self.state_topic = state_topic
        self.verbose = verbose

        self.time_of_pulse = time.perf_counter()
        self.port_sub_state = ct.STATE_FORWARDER_PUBLISH_PORT

        self.context = None
        self.socket_pull_data = None
        self.stream_pull_data = None
        self.socket_push_data = None
        self.socket_sub_state = None
        self.stream_state = None
        self.state = None
        self.socket_pull_heartbeat = None
        self.stream_heartbeat = None
        self.thread_heartbeat = None

    def connect_sockets(self):
        """
        Sets up the sockets to do the communication with the transform_com process through the forwarders
        (for the data and the state).
        :return: Nothing
        """
        self.context = zmq.Context()

        # Setup the socket and the stream that receives the data from the com to be worked upon
        self.socket_pull_data = Socket(self.context, zmq.PULL)
        self.socket_pull_data.set_hwm(1)
        self.socket_pull_data.bind(r"tcp://127.0.0.1:{}".format(self.pull_data_port))
        self.stream_pull_data = zmqstream.ZMQStream(self.socket_pull_data)
        self.stream_pull_data.on_recv(self.data_callback)

        # Setup the socket and the stream that receives the parameters of the worker function from the node (gui_com)
        self.socket_sub_state = Socket(self.context, zmq.SUB)
        self.socket_sub_state.connect(r'tcp://localhost:{}'.format(self.port_sub_state))
        self.socket_sub_state.subscribe(self.state_topic)
        self.stream_state = zmqstream.ZMQStream(self.socket_sub_state)
        self.stream_state.on_recv(self.parameters_callback)

        # Setup the socket that sends the results to the com
        self.socket_push_data = Socket(self.context, zmq.PUSH)
        self.socket_push_data.set_hwm(1)
        self.socket_push_data.connect(r"tcp://127.0.0.1:{}".format(self.push_data_port))

        # Setup the socket that receives the heartbeat from the com
        self.socket_pull_heartbeat = self.context.socket(zmq.PULL)
        self.socket_pull_heartbeat.bind(r'tcp://127.0.0.1:{}'.format(self.pull_heartbeat_port))
        self.stream_heartbeat = zmqstream.ZMQStream(self.socket_pull_heartbeat)
        self.stream_heartbeat.on_recv(self.heartbeat_callback)

    def data_callback(self, data):
        """
        The callback that is called when data is send from the previous com process this com process is connected to
        (receives data from and shares a common topic) and pushes the data to the worker.
        The data are a three items list. The first is the topic (used for the worker to distinguish which input the
        data have come from in the case of multiple input nodes). The other two items are the details and the data load
        of the numpy array coming from the previous node).
        :param data: The data received
        :return: Nothing
        """
        results = self.work_function(data, self.state)
        for array_in_list in results:
            self.socket_push_data.send_array(array_in_list, copy=False)

    def parameters_callback(self, binary_state):
        """
        The callback called when there is an update of the state (worker function's parameters) from the node
        (send by the gui_com)
        :param binary_state:
        :return:
        """
        #print(binary_state)
        args_pyobj = binary_state[1]  # remove the topic
        args = pickle.loads(args_pyobj)
        self.state = args

    def heartbeat_callback(self, pulse):
        """
        The callback called when the com send a 'PULSE'. It registers the time the 'PULSE' has been received
        :param pulse: The pulse (message from the com's push) received
        :return:
        """
        self.time_of_pulse = time.perf_counter()

    def heartbeat_loop(self):
        """
        The loop that checks whether the latest 'PULSE' received from the com's heartbeat push is not too stale.
        If it is then the current process is killed
        :return:
        """
        while True:
            current_time = time.perf_counter()
            if current_time - self.time_of_pulse > 0.5 + ct.HEARTBEAT_RATE:
                pid = os.getpid()
                print('Killing pid {}'.format(pid))
                os.kill(pid, signal.SIGTERM)
            time.sleep(int(ct.HEARTBEAT_RATE / 2))

    def start_ioloop(self):
        """
        Starts the heartbeat thread daemon and the ioloop of the zmqstreams
        :return:
        """
        self.thread_heartbeat = threading.Thread(target=self.heartbeat_loop, daemon=True)
        self.thread_heartbeat.start()
        ioloop.IOLoop.instance().start()








