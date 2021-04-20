
import zmq
import atexit
from Heron import constants as ct
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
import subprocess
from zmq.eventloop import ioloop, zmqstream
import time

class SourceCom:
    def __init__(self, topic, port, worker_exec, verbose=False):
        self.topic = topic
        self.port = port
        self.worker = worker_exec
        self.context = zmq.Context()
        self.index = 0
        self.verbose = verbose

        self.socket_pub_state = None
        self.socket_pub_data = None
        self.socket_pull_data = None
        self.stream_pull = None

    def on_receive_data_from_worker(self, msg):
        # The index of the data packet is the system's time in microseconds
        self.index = int(1000000 * time.perf_counter())  # self.index + 1

        if self.verbose:
            print('----------')
        data = Socket.reconstruct_array_from_bytes_message(msg)

        self.socket_pub_state.send_string(str(self.index))

        self.socket_pub_data.send("{}".format(self.topic).encode('ascii'), flags=zmq.SNDMORE)
        self.socket_pub_data.send("{}".format(self.index).encode('ascii'), flags=zmq.SNDMORE)
        self.socket_pub_data.send_array(data, copy=False)
        if self.verbose:
            print("Sink sending to {} with index {}".format(self.topic, self.index))

    def connect_sockets(self):
        port_pull = self.port
        self.socket_pull_data = Socket(self.context, zmq.PULL)
        self.socket_pull_data.set_hwm(1)
        self.socket_pull_data.bind(r"tcp://127.0.0.1:{}".format(port_pull))
        self.stream_pull = zmqstream.ZMQStream(self.socket_pull_data)
        self.stream_pull.on_recv(self.on_receive_data_from_worker)

        port_pub = ct.DATA_FORWARDER_SUBMIT_PORT
        self.socket_pub_data = Socket(self.context, zmq.PUB)
        self.socket_pub_data.set_hwm(1)
        self.socket_pub_data.connect(r"tcp://localhost:{}".format(port_pub))

        port_pub_state = ct.STATE_FORWARDER_SUBMIT_PORT
        self.socket_pub_state = Socket(self.context, zmq.PUB)
        self.socket_pub_state.CONFLATE = 1
        self.socket_pub_state.connect(r"tcp://localhost:{}".format(port_pub_state))

    def start_worker(self):
        print(self.worker)
        print(self.port)
        worker = subprocess.Popen(['python', self.worker, self.port])

        if self.verbose:
            print('Source {} PID = {}.'.format(self.topic, worker.pid))
        atexit.register(gu.kill_child, worker.pid)

    def start_ioloop(self):
        ioloop.IOLoop.instance().start()












