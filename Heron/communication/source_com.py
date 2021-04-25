
import zmq
import atexit
import time
import threading
from Heron import constants as ct
from Heron.communication.socket_for_serialization import Socket
from Heron.communication import gui_com
from Heron import general_utils as gu
import subprocess
from zmq.eventloop import ioloop, zmqstream


class SourceCom:
    def __init__(self, sending_topic, state_topic, port, worker_exec, verbose=False):
        self.sending_topic = sending_topic
        self.state_topic = state_topic
        self.data_port = port
        self.heartbeat_port = str(int(self.data_port) + 1)
        self.worker = worker_exec
        self.context = zmq.Context()
        self.index = 0
        self.time = int(1000000 * time.perf_counter())
        self.verbose = verbose

        self.port_pub = ct.DATA_FORWARDER_SUBMIT_PORT

        self.socket_pub_state = None
        self.socket_pub_data = None
        self.socket_pull_data = None
        self.stream_pull = None
        self.socket_push_heartbeat = None

    def connect_sockets(self):
        """
        Start the required sockets to communicate with the data forwarder and the source_com processes
        :return: Nothing
        """

        # Socket for pulling the data from the worker
        self.socket_pull_data = Socket(self.context, zmq.PULL)
        self.socket_pull_data.set_hwm(1)
        self.socket_pull_data.bind(r"tcp://127.0.0.1:{}".format(self.data_port))
        self.stream_pull = zmqstream.ZMQStream(self.socket_pull_data)
        self.stream_pull.on_recv(self.on_receive_data_from_worker)

        # Socket for publishing the data to the data forwarder
        self.socket_pub_data = Socket(self.context, zmq.PUB)
        self.socket_pub_data.set_hwm(1)
        self.socket_pub_data.connect(r"tcp://localhost:{}".format(self.port_pub))

        # Socket for pushing the heartbeat to the worker
        # Socket for publishing the heartbeat to the worker
        self.socket_push_heartbeat = self.context.socket(zmq.PUSH)
        self.socket_push_heartbeat.connect(r'tcp://127.0.0.1:{}'.format(self.heartbeat_port))
        self.socket_push_heartbeat.set_hwm(1)

    def on_receive_data_from_worker(self, msg):
        """
        The callback that runs every time data is received from the worker process. It takes the data and passes it
        onto the data forwarder
        :param msg: The data packet (carrying the actual data (np array))
        :return:
        """
        # The index of the data packet is the system's time in microseconds
        self.time = int(1000000 * time.perf_counter())
        self.index = self.index + 1

        data = Socket.reconstruct_array_from_bytes_message(msg)

        self.socket_pub_data.send("{}".format(self.sending_topic).encode('ascii'), flags=zmq.SNDMORE)
        self.socket_pub_data.send("{}".format(self.index).encode('ascii'), flags=zmq.SNDMORE)
        self.socket_pub_data.send("{}".format(self.time).encode('ascii'), flags=zmq.SNDMORE)
        self.socket_pub_data.send_array(data, copy=False)
        if self.verbose:
            print('----------')
            print("Sink sending to {} with index {} at time {}".format(self.sending_topic, self.index, self.time))

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

    def start_worker_process(self, arguments_list):
        """
        Starts the worker process and then sends the parameters as are currently on the node to the process
        :param arguments_list: The argument list that has all the parameters for the worker (as given in the node's gui)
        :return: Nothing
        """
        worker = subprocess.Popen(['python', self.worker, self.data_port, self.state_topic, str(self.verbose)])

        if self.verbose:
            print('Source {} PID = {}.'.format(self.sending_topic, worker.pid))
        atexit.register(gu.kill_child, worker.pid)

        # We need to send the parameter values on the node to the worker right after it starts.
        time.sleep(1)  # Allow the worker process to start before sending the current parameters
        self.publish_parameters_to_worker(self.state_topic, arguments_list)

    def start_ioloop(self):
        """
        Starts the ioloop of the zmqstream
        :return: Nothing
        """
        ioloop.IOLoop.instance().start()












