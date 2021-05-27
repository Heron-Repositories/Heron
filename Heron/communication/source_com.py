
import zmq
import atexit
import time
import threading
from Heron import constants as ct
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
import subprocess
from zmq.eventloop import ioloop, zmqstream


class SourceCom:
    def __init__(self, sending_topics, parameters_topic, port, worker_exec, verbose=False):
        self.sending_topics = sending_topics
        self.sending_topic = self.sending_topics[0]  # TODO need to deal with multiple outputs
        self.parameters_topic = parameters_topic
        self.data_port = port
        self.heartbeat_port = str(int(self.data_port) + 1)
        self.worker = worker_exec
        self.context = zmq.Context()
        self.index = 0
        self.time = int(1000000 * time.perf_counter())
        self.previous_time = self.time
        self.verbose = verbose

        self.port_pub = ct.DATA_FORWARDER_SUBMIT_PORT

        #self.socket_pub_parameters = None
        self.socket_pub_data = None
        self.socket_pull_data = None
        self.stream_pull_data = None
        self.socket_push_heartbeat = None
        self.average_sending_time = 0

    def connect_sockets(self):
        """
        Start the required sockets to communicate with the link forwarder and the source_com processes
        :return: Nothing
        """

        # Socket for pulling the data from the worker
        self.socket_pull_data = Socket(self.context, zmq.PULL)
        self.socket_pull_data.set_hwm(1)
        self.socket_pull_data.bind(r"tcp://127.0.0.1:{}".format(self.data_port))
        # TODO: Add ssh to remote server
        self.stream_pull_data = zmqstream.ZMQStream(self.socket_pull_data)
        self.stream_pull_data.on_recv(self.on_receive_data_from_worker)

        # Socket for publishing the data to the data forwarder
        self.socket_pub_data = Socket(self.context, zmq.PUB)
        self.socket_pub_data.set_hwm(1)
        self.socket_pub_data.connect(r"tcp://127.0.0.1:{}".format(self.port_pub))

        # Socket for pushing the heartbeat to the worker
        # Socket for publishing the heartbeat to the worker
        self.socket_push_heartbeat = self.context.socket(zmq.PUSH)
        self.socket_push_heartbeat.connect(r'tcp://127.0.0.1:{}'.format(self.heartbeat_port))
        self.socket_push_heartbeat.set_hwm(1)

    def on_receive_data_from_worker(self, msg):
        """
        The callback that runs every time link is received from the worker process. It takes the link and passes it
        onto the link forwarder
        :param msg: The link packet (carrying the actual link (np array))
        :return:
        """
        # The node_index of the link packet is the system's time in microseconds
        data = Socket.reconstruct_array_from_bytes_message(msg)

        self.time = int(1000000 * time.perf_counter())
        self.index = self.index + 1

        self.socket_pub_data.send("{}".format(self.sending_topic).encode('ascii'), flags=zmq.SNDMORE)
        self.socket_pub_data.send("{}".format(self.index).encode('ascii'), flags=zmq.SNDMORE)
        self.socket_pub_data.send("{}".format(self.time).encode('ascii'), flags=zmq.SNDMORE)
        self.socket_pub_data.send_array(data, copy=False)

        if self.verbose:
            dt = self.time - self.previous_time
            if self.index > 3:
                self.average_sending_time = self.average_sending_time * (self.index - 1) / self.index + dt / self.index
            print('----------')
            print("Source with topic {} sending packet with data_index {} at time {}".format(self.sending_topic, self.index, self.time))
            print('Time Diff between packages = {}. Average package sending time = {} ms'.format(dt/1000, self.average_sending_time / 1000))
        self.previous_time = self.time

    def heartbeat_loop(self):
        """
        Sending every ct.HEARTBEAT_RATE a 'PULSE' to the worker so that it stays alive
        :return: Nothing
        """
        while True:
            self.socket_push_heartbeat.send_string('PULSE')
            time.sleep(ct.HEARTBEAT_RATE)

    def start_heartbeat_thread(self):
        """
        Starts the daemon thread that runs the self.heartbeat loop
        :return: Nothing
        """
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()

    def start_worker_process(self):
        """
        Starts the worker process and then sends the parameters as are currently on the node to the process
        :param arguments_list: The argument list that has all the parameters for the worker (as given in the node's gui)
        :return: Nothing
        """
        # TODO: Add possibility of starting script over ssh
        worker = subprocess.Popen(['python', self.worker, self.data_port, self.parameters_topic, str(0), str(self.verbose)])

        if self.verbose:
            print('Source {} PID = {}.'.format(self.sending_topic, worker.pid))
        atexit.register(gu.kill_child, worker.pid)

    def start_ioloop(self):
        """
        Starts the ioloop of the zmqstream
        :return: Nothing
        """
        ioloop.IOLoop.instance().start()












