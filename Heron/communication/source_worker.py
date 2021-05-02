
import time
import threading
import zmq
import os
import signal
import pickle
import cv2
from Heron.communication.socket_for_serialization import Socket
from Heron import constants as ct


class SourceWorker:
    def __init__(self, port, parameters_topic, end_of_life_function, verbose=False):
        self.parameters_topic = parameters_topic
        self.data_port = port
        self.heartbeat_port = str(int(self.data_port) + 1)
        self.end_of_life_function=end_of_life_function
        self.verbose = verbose
        self.name = parameters_topic.split('##')[-2]
        self.index = parameters_topic.split('##')[-1]

        self.time_of_pulse = time.perf_counter()
        self.port_sub_parameters = ct.PARAMETERS_FORWARDER_PUBLISH_PORT
        self.port_pub_proof_of_life = ct.PROOF_OF_LIFE_FORWARDER_SUBMIT_PORT
        self.running_thread = True
        self.visualisation_on = False
        self.visualisation_thread = threading.Thread(target=self.visualisation_loop, daemon=True)

        self.context = None
        self.socket_push_data = None
        self.socket_sub_parameters = None
        self.stream_parameters = None
        self.thread_parameters = None
        self.parameters = None
        self.socket_pull_heartbeat = None
        self.stream_heartbeat = None
        self.thread_heartbeat = None
        self.socket_pub_proof_of_life = None
        self.thread_proof_of_life = None
        self.worker_result = None

    def connect_socket(self):
        """
        Sets up the sockets to do the communication with the source_com process through the forwarders
        (for the data and the parameters).
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
        self.socket_sub_parameters = Socket(self.context, zmq.SUB)
        self.socket_sub_parameters.connect(r'tcp://localhost:{}'.format(self.port_sub_parameters))
        self.socket_sub_parameters.subscribe(self.parameters_topic)

        # Setup the socket that receives the heartbeat from the com
        self.socket_pull_heartbeat = self.context.socket(zmq.PULL)
        self.socket_pull_heartbeat.bind(r'tcp://127.0.0.1:{}'.format(self.heartbeat_port))

        # Setup the socket that sends (publishes) the fact that the worker is up and running to the node com so that it
        # can then update the parameters of the worker
        self.socket_pub_proof_of_life = Socket(self.context, zmq.PUB)
        self.socket_pub_proof_of_life.connect(r'tcp://127.0.0.1:{}'.format(self.port_pub_proof_of_life))

    def update_parameters(self):
        """
        This updates the self.parameters from the parameters send form the node (through the gui_com)
        :return: Nothing
        """
        try:
            topic = self.socket_sub_parameters.recv(flags=zmq.NOBLOCK)
            parameters_in_bytes = self.socket_sub_parameters.recv(flags=zmq.NOBLOCK)
            args = pickle.loads(parameters_in_bytes)
            self.parameters = args
            # print('TOPIC {}'.format(topic))
            # print('--Source {} binary parameters {}'.format(self.parameters_topic, parameters_in_bytes))
            # print(args)
        except zmq.Again as e:
            pass

    def parameters_loop(self):
        """
        The loop that updates the arguments (self.parameters)
        :return: Nothing
        """
        while True:
            self.update_parameters()
            time.sleep(0.2)

    def start_parameters_thread(self):
        """
        Start the thread that runs the infinite arguments_loop
        :return: Nothing
        """
        self.thread_parameters = threading.Thread(target=self.parameters_loop, daemon=True)
        self.thread_parameters.start()

    def heartbeat_loop(self):
        """
        The loop that reads the heartbeat 'PULSE' from the source_com. If it takes too long to receive the new one
        it kills the worker process
        :return: Nothing
        """
        while True:
            if self.socket_pull_heartbeat.poll(timeout=(1000 * ct.HEARTBEAT_RATE * ct.HEARTBEATS_TO_DEATH)):
                self.socket_pull_heartbeat.recv()
            else:
                pid = os.getpid()
                self.end_of_life_function()
                print('Killing {} {} with pid {}'.format(self.name, self.index, pid))
                os.kill(pid, signal.SIGTERM)
            time.sleep(int(ct.HEARTBEAT_RATE))

    def proof_of_life(self):
        """
        When the worker process starts it sends to the gui_com (through the proof_of_life_forwarder thread) a signal
        that lets the node (in the gui_com process) that the worker is running and ready to receive parameter updates.
        :return: Nothing
        """
        for i in range(2):
            self.socket_pub_proof_of_life.send_string(self.parameters_topic + '##' + 'POL')
            time.sleep(0.2)

    def visualisation_loop(self):
        """
        When the visualisation parameter in a node is set to True then this loop starts in a new visualisation thread.
        The thread terminates when the visualisation_on boolean is turned off
        :return: Nothing
        """
        while self.visualisation_on:
            cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)

            width = cv2.getWindowImageRect("Camera")[2]
            height = cv2.getWindowImageRect("Camera")[3]
            try:
                image = cv2.resize(self.worker_result, (width, height), interpolation=cv2.INTER_AREA)
                cv2.imshow('Camera', image)
                cv2.waitKey(1)
            except:
                pass
        cv2.destroyAllWindows()

    def visualisation_toggle(self):
        """
        The function that is run at every cycle of the WORKER_FUNCTION to check if the visualisation_on bool is True or
        not and turn on or off the visualisation_thread
        :return: Nothing
        """
        if self.visualisation_on and not self.visualisation_thread.is_alive():
            self.visualisation_on = True
            self.visualisation_thread.start()
        if not self.visualisation_on and not self.visualisation_thread.is_alive():
            self.visualisation_thread = threading.Thread(target=self.visualisation_loop, daemon=True)

    def start_heartbeat_thread(self):
        """
        Start the heartbeat thread that run the infinite heartbeat_loop
        :return: Nothing
        """
        self.thread_heartbeat = threading.Thread(target=self.heartbeat_loop, daemon=True)
        self.thread_heartbeat.start()

        self.thread_proof_of_life = threading.Thread(target=self.proof_of_life, daemon=True)
        self.thread_proof_of_life.start()

