


import zmq
from Heron.communication.socket_for_serialization import Socket
from zmq.eventloop import ioloop, zmqstream


class TransformWorker:
    def __init__(self, pull_port, push_port, work_function, verbose):
        self.pull_port = pull_port
        self.push_port = push_port
        self.work_function = work_function
        self.verbose = verbose

        self.context = None
        self.socket_pull_data = None
        self.stream_pull = None
        self.socket_push_data = None

    def connect_sockets(self):
        self.context = zmq.Context()

        # Setup the socket that sends data to the worker to be worked upon
        self.socket_push_data = Socket(self.context, zmq.PUSH)
        self.socket_push_data.set_hwm(1)
        self.socket_push_data.connect(r"tcp://127.0.0.1:{}".format(self.push_port))

        # Setup the socket and the stream that receives the results from the worker
        self.socket_pull_data = Socket(self.context, zmq.PULL)
        self.socket_pull_data.set_hwm(1)
        self.socket_pull_data.bind(r"tcp://127.0.0.1:{}".format(self.pull_port))
        self.stream_pull = zmqstream.ZMQStream(self.socket_pull_data)
        self.stream_pull.on_recv(self.callback)

    def callback(self, data):
        result = self.work_function(data)
        self.socket_push_data.send_array(result, copy=False)

    def start_ioloop(self):
        ioloop.IOLoop.instance().start()








