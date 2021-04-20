

import zmq
from Heron.communication.socket_for_serialization import Socket


class SourceWorker:
    def __init__(self, port, verbose=False):
        self.port_push = port
        self.verbose = verbose

        self.socket_push_data = None

    def connect_socket(self):
        context = zmq.Context()

        self.socket_push_data = Socket(context, zmq.PUSH)
        self.socket_push_data.set_hwm(1)
        self.socket_push_data.connect(r"tcp://127.0.0.1:{}".format(self.port_push))

        if self.verbose:
            print('Starting Source worker on port {}'.format(self.port_push))