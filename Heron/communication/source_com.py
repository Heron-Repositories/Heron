
import zmq
import atexit
from Heron import constants as ct
from Heron.communication.socket_for_serialization import Socket
from Heron.communication import gui_com
from Heron import general_utils as gu
import subprocess
from zmq.eventloop import ioloop, zmqstream
import time


class SourceCom:
    def __init__(self, sending_topic, state_topic, port, worker_exec, verbose=False):
        self.sending_topic = sending_topic
        self.state_topic = state_topic
        self.port = port
        self.worker = worker_exec
        self.context = zmq.Context()
        self.index = 0
        self.time = int(1000000 * time.perf_counter())
        self.verbose = verbose

        self.socket_pub_state = None
        self.socket_pub_data = None
        self.socket_pull_data = None
        self.stream_pull = None

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

    def connect_sockets(self):
        """
        Start the required sockets to communicate with the data forwarder and the source_com processes
        :return: Nothing
        """
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

    @staticmethod
    def publish_parameters_to_worker(topic, arguments_list):
        """
        Uses the gui's publish state socket to publish the argument_list with the correct topic. This will be read by
        the worker's subscribe state socket (which subscribes to the specific topic) and update the parameters that the
        worker's work function is using
        :return: Nothing
        """
        #print(topic)
        #print(arguments_list)
        gui_com.SOCKET_PUB_STATE.send_string(topic, flags=zmq.SNDMORE)
        gui_com.SOCKET_PUB_STATE.send_pyobj(arguments_list)

    def start_worker(self, arguments_list):
        """
        Starts the worker process and then sends the parameters as are currently on the node to the process
        :param arguments_list: The argument list that has all the parameters for the worker (as given in the node's gui)
        :return: Nothing
        """
        worker = subprocess.Popen(['python', self.worker, self.port, self.state_topic])

        if self.verbose:
            print('Source {} PID = {}.'.format(self.sending_topic, worker.pid))
        atexit.register(gu.kill_child, worker.pid)

        # We need to send the parameter values on the node to the worker right after it starts.
        time.sleep(1)  # Allow the worker process to start before sending the current parameters
        self.publish_parameters_to_worker(self.state_topic, arguments_list)

    def start_ioloop(self):
        ioloop.IOLoop.instance().start()












