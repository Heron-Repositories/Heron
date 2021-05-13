
import time
import threading
import pickle
import os
import signal
import zmq
from Heron import constants as ct
from Heron.communication.socket_for_serialization import Socket
from zmq.eventloop import ioloop, zmqstream


class SinkWorker:
    def __init__(self, recv_topics_buffer, pull_port, work_function, end_of_life_function, parameters_topic, verbose):

        self.pull_data_port = pull_port
        self.pull_heartbeat_port = str(int(self.pull_data_port) + 1)
        self.work_function = work_function
        self.end_of_life_function = end_of_life_function
        self.parameters_topic = parameters_topic
        self.verbose = verbose
        self.recv_topics_buffer = recv_topics_buffer

        self.op_name = self.parameters_topic.split('##')[-2]
        self.index = self.parameters_topic.split('##')[-1]
        self.time_of_pulse = time.perf_counter()
        self.port_sub_parameters = ct.PARAMETERS_FORWARDER_PUBLISH_PORT
        self.port_pub_proof_of_life = ct.PROOF_OF_LIFE_FORWARDER_SUBMIT_PORT

        self.context = None
        self.socket_pull_data = None
        self.stream_pull_data = None
        self.socket_sub_parameters = None
        self.stream_parameters = None
        self.parameters = None
        self.socket_pull_heartbeat = None
        self.stream_heartbeat = None
        self.thread_heartbeat = None
        self.socket_pub_proof_of_life = None
        self.thread_proof_of_life = None

    def connect_sockets(self):
        """
        Sets up the sockets to do the communication with the transform_com process through the forwarders
        (for the link and the parameters).
        :return: Nothing
        """
        self.context = zmq.Context()

        # Setup the socket and the stream that receives the data from the com to be worked upon
        self.socket_pull_data = Socket(self.context, zmq.PULL)
        self.socket_pull_data.set_hwm(1)
        self.socket_pull_data.bind(r"tcp://127.0.0.1:{}".format(self.pull_data_port))
        self.stream_pull_data = zmqstream.ZMQStream(self.socket_pull_data)
        self.stream_pull_data.on_recv(self.data_callback, copy=False)

        # Setup the socket and the stream that receives the parameters of the worker function from the node (gui_com)
        self.socket_sub_parameters = Socket(self.context, zmq.SUB)
        self.socket_sub_parameters.connect(r'tcp://localhost:{}'.format(self.port_sub_parameters))
        self.socket_sub_parameters.subscribe(self.parameters_topic)
        self.stream_parameters = zmqstream.ZMQStream(self.socket_sub_parameters)
        self.stream_parameters.on_recv(self.parameters_callback, copy=False)

        # Setup the socket that receives the heartbeat from the com
        self.socket_pull_heartbeat = self.context.socket(zmq.PULL)
        self.socket_pull_heartbeat.bind(r'tcp://127.0.0.1:{}'.format(self.pull_heartbeat_port))
        self.stream_heartbeat = zmqstream.ZMQStream(self.socket_pull_heartbeat)
        self.stream_heartbeat.on_recv(self.heartbeat_callback, copy=False)

        # Setup the socket that sends (publishes) the fact that the worker is up and running to the node com so that it
        # can then update the parameters of the worker
        self.socket_pub_proof_of_life = Socket(self.context, zmq.PUB)
        self.socket_pub_proof_of_life.connect(r'tcp://127.0.0.1:{}'.format(self.port_pub_proof_of_life))

    def data_callback(self, data):
        """
        The callback that is called when link is send from the previous com process this com process is connected to
        (receives link from and shares a common topic) and pushes the link to the worker.
        The link are a three zmq.Frame list. The first is the topic (used for the worker to distinguish which input the
        link have come from in the case of multiple input nodes). The other two items are the details and the link load
        of the numpy array coming from the previous node).
        :param data: The link received
        :return: Nothing
        """
        data = [data[0].bytes, data[1].bytes, data[2].bytes] # Turn that on if the stream_pull_data.on_recv has copy=False
        self.work_function(data, self.parameters)

    def parameters_callback(self, parameters_in_bytes):
        """
        The callback called when there is an update of the parameters (worker function's parameters) from the node
        (send by the gui_com)
        :param parameters_in_bytes:
        :return:
        """
        if len(parameters_in_bytes) > 1:
            args_pyobj = parameters_in_bytes[1].bytes  # remove the topic
            args = pickle.loads(args_pyobj)
            if args is not None:
                self.parameters = args
                # print('Updated parameters in {} = {}'.format(self.parameters_topic, args))

    def heartbeat_callback(self, pulse):
        """
        The callback called when the com sends a 'PULSE'. It registers the time the 'PULSE' has been received
        :param pulse: The pulse (message from the com's push) received
        :return:
        """
        self.time_of_pulse = time.perf_counter()

    def heartbeat_loop(self):
        """
        The loop that checks whether the latest 'PULSE' received from the com's heartbeat push is not too stale.
        If it is then the current process is killed
        :return: Nothing
        """
        while True:
            current_time = time.perf_counter()
            if current_time - self.time_of_pulse > ct.HEARTBEAT_RATE * ct.HEARTBEATS_TO_DEATH:
                #print('At {}, CT = {}, time of pulse = {}'.format(self.parameters_topic, current_time, self.time_of_pulse))
                pid = os.getpid()
                self.end_of_life_function()
                print('Killing {} with pid {}'.format(self.parameters_topic, pid))
                os.kill(pid, signal.SIGTERM)
            time.sleep(ct.HEARTBEAT_RATE)

    def proof_of_life(self):
        """
        When the worker process starts it sends to the gui_com (through the proof_of_life_forwarder thread) a signal
        that lets the node (in the gui_com process) that the worker is running and ready to receive parameter updates.
        :return: Nothing
        """
        for i in range(2):
            self.socket_pub_proof_of_life.send_string(self.parameters_topic + '##' + 'POL')
            time.sleep(0.2)

    def start_ioloop(self):
        """
        Starts the heartbeat thread daemon and the ioloop of the zmqstreams
        :return: Nothing
        """
        self.thread_heartbeat = threading.Thread(target=self.heartbeat_loop, daemon=True)
        self.thread_heartbeat.start()

        self.thread_proof_of_life = threading.Thread(target=self.proof_of_life, daemon=True)
        self.thread_proof_of_life.start()

        ioloop.IOLoop.instance().start()
        print('!!! WORKER {} HAS STOPPED'.format(self.parameters_topic))










