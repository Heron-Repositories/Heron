

import zmq
from zmq.eventloop import ioloop, zmqstream
import pickle
from Heron.communication.socket_for_serialization import Socket
from Heron import  constants as ct


class SourceWorker:
    def __init__(self, port, state_topic, verbose=False):
        self.state_topic = state_topic
        self.port_push = port
        self.verbose = verbose

        self.context = None
        self.socket_push_data = None
        self.socket_sub_state = None
        self.stream_state = None
        self.port_sub_state = ct.STATE_FORWARDER_PUBLISH_PORT
        self.state = None

    def connect_socket(self):
        self.context = zmq.Context()

        self.socket_push_data = Socket(self.context, zmq.PUSH)
        self.socket_push_data.set_hwm(1)
        self.socket_push_data.connect(r"tcp://127.0.0.1:{}".format(self.port_push))

        if self.verbose:
            print('Starting Source worker on port {}'.format(self.port_push))

        # Setup the socket and the stream that receives the parameters of the worker function from the node
        self.socket_sub_state = Socket(self.context, zmq.SUB)
        self.socket_sub_state.connect(r'tcp://localhost:{}'.format(self.port_sub_state))
        self.socket_sub_state.subscribe(self.state_topic)

    def update_arguments(self):
        try:
            topic = self.socket_sub_state.recv(flags=zmq.NOBLOCK)
            binary_state = self.socket_sub_state.recv()
            args = pickle.loads(binary_state)
            #print(args)
            self.state = args
        except zmq.Again as e:
            pass
