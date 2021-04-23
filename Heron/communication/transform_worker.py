

import zmq
from Heron import constants as ct
from Heron.communication.socket_for_serialization import Socket
from zmq.eventloop import ioloop, zmqstream
import pickle


class TransformWorker:
    def __init__(self, pull_port, push_port, work_function, state_topic, verbose):
        self.pull_port = pull_port
        self.push_port = push_port
        self.work_function = work_function
        self.state_topic = state_topic
        self.verbose = verbose

        self.context = None
        self.socket_pull_data = None
        self.stream_pull = None
        self.socket_push_data = None
        self.port_sub_state = ct.STATE_FORWARDER_PUBLISH_PORT
        self.socket_sub_state = None
        self.stream_state = None
        self.state = None

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
        self.socket_pull_data.bind(r"tcp://127.0.0.1:{}".format(self.pull_port))
        self.stream_pull = zmqstream.ZMQStream(self.socket_pull_data)
        self.stream_pull.on_recv(self.data_callback)

        # Setup the socket and the stream that receives the parameters of the worker function from the node
        self.socket_sub_state = Socket(self.context, zmq.SUB)
        self.socket_sub_state.connect(r'tcp://localhost:{}'.format(self.port_sub_state))
        self.socket_sub_state.subscribe(self.state_topic)
        self.stream_state = zmqstream.ZMQStream(self.socket_sub_state)
        self.stream_state.on_recv(self.arguments_callback)

        # Setup the socket that sends the results to the com
        self.socket_push_data = Socket(self.context, zmq.PUSH)
        self.socket_push_data.set_hwm(1)
        self.socket_push_data.connect(r"tcp://127.0.0.1:{}".format(self.push_port))

    def data_callback(self, data):
        result = self.work_function(data, self.state)
        self.socket_push_data.send_array(result, copy=False)

    def arguments_callback(self, binary_state):
        args_pyobj = binary_state[1]  # remove the topic
        args = pickle.loads(args_pyobj)
        self.state = args

    def start_ioloop(self):
        ioloop.IOLoop.instance().start()








