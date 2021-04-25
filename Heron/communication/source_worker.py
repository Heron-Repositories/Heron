
import time
import threading
import zmq
import os
import signal
import pickle
from Heron.communication.socket_for_serialization import Socket
from Heron import constants as ct


class SourceWorker:
    def __init__(self, port, state_topic, verbose=False):
        self.state_topic = state_topic
        self.data_port = port
        self.heartbeat_port = str(int(self.data_port) + 1)
        self.verbose = verbose

        self.time_of_pulse = time.perf_counter()
        self.port_sub_state = ct.STATE_FORWARDER_PUBLISH_PORT

        self.context = None
        self.socket_push_data = None
        self.socket_sub_state = None
        self.stream_state = None
        self.thread_state = None
        self.state = None
        self.socket_pull_heartbeat = None
        self.stream_heartbeat = None
        self.thread_heartbeat = None

    def connect_socket(self):
        """
        Sets up the sockets to do the communication with the source_com process through the forwarders
        (for the data and the state).
        :return: Nothing
        """
        self.context = zmq.Context()

        # Setup the socket that pushes the data to the com
        self.socket_push_data = Socket(self.context, zmq.PUSH)
        self.socket_push_data.set_hwm(1)
        self.socket_push_data.connect(r"tcp://127.0.0.1:{}".format(self.data_port))

        if self.verbose:
            print('Starting Source worker on port {}'.format(self.data_port))

        # Setup the socket that receives the parameters of the worker function from the node
        self.socket_sub_state = Socket(self.context, zmq.SUB)
        self.socket_sub_state.connect(r'tcp://localhost:{}'.format(self.port_sub_state))
        self.socket_sub_state.subscribe(self.state_topic)

        # Setup the socket that receives the heartbeat from the com
        self.socket_pull_heartbeat = self.context.socket(zmq.PULL)
        self.socket_pull_heartbeat.bind(r'tcp://127.0.0.1:{}'.format(self.heartbeat_port))

    def update_arguments(self):
        """
        This updates the self.state from the parameters send form the node (through the gui_com)
        :return: Nothing
        """
        try:
            topic = self.socket_sub_state.recv(flags=zmq.NOBLOCK)
            binary_state = self.socket_sub_state.recv()
            args = pickle.loads(binary_state)
            #print(args)
            self.state = args
        except zmq.Again as e:
            pass

    def arguments_loop(self):
        """
        The loop that updates the arguments (self.state)
        :return: Nothing
        """
        while True:
            self.update_arguments()
            time.sleep(0.2)

    def start_parameters_thread(self):
        """
        Start the thread that runs the infinite arguments_loop
        :return: Nothing
        """
        self.thread_state = threading.Thread(target=self.arguments_loop, daemon=True)
        self.thread_state.start()

    def heartbeat_loop(self):
        """
        The loop that reads the heartbeat 'PULSE' from the source_com. If it takes too long to receive the new one
        it kills the worker process
        :return: Nothing
        """
        while True:
            if self.socket_pull_heartbeat.poll(timeout=1200 * ct.HEARTBEAT_RATE):
                self.socket_pull_heartbeat.recv()
            else:
                pid = os.getpid()
                print('Killing pid {}'.format(pid))
                os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)

    def start_heartbeat_thread(self):
        """
        Start the heartbeat thread that run the infinite heartbeat_loop
        :return: Nothing
        """
        self.thread_heartbeat = threading.Thread(target=self.heartbeat_loop, daemon=True)
        self.thread_heartbeat.start()

