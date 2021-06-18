
import time
import threading
import pickle
import os
import signal
import zmq
import cv2
from Heron import constants as ct
from zmq.eventloop import ioloop, zmqstream
from Heron.communication.socket_for_serialization import Socket
from Heron.communication.ssh_com import SSHCom


class TransformWorker:
    def __init__(self, recv_topics_buffer, pull_port, work_function, end_of_life_function, parameters_topic, verbose,
                 ssh_local_ip=' ', ssh_local_username=' ', ssh_local_password=' '):

        self.pull_data_port = pull_port
        self.push_data_port = str(int(self.pull_data_port) + 1)
        self.pull_heartbeat_port = str(int(self.pull_data_port) + 2)
        self.work_function = work_function
        self.end_of_life_function = end_of_life_function
        self.parameters_topic = parameters_topic
        self.verbose = verbose
        self.recv_topics_buffer = recv_topics_buffer
        self.node_name = parameters_topic.split('##')[-2]
        self.node_index = self.parameters_topic.split('##')[-1]

        self.ssh_com = SSHCom(ssh_local_ip=ssh_local_ip, ssh_local_username=ssh_local_username,
                              ssh_local_password=ssh_local_password)

        self.time_of_pulse = time.perf_counter()
        self.port_sub_parameters = ct.PARAMETERS_FORWARDER_PUBLISH_PORT
        self.port_pub_proof_of_life = ct.PROOF_OF_LIFE_FORWARDER_SUBMIT_PORT
        self.visualisation_on = False
        self.visualisation_thread = None

        self.context = None
        self.socket_pull_data = None
        self.stream_pull_data = None
        self.socket_push_data = None
        self.socket_sub_parameters = None
        self.stream_parameters = None
        self.parameters = None
        self.socket_pull_heartbeat = None
        self.stream_heartbeat = None
        self.thread_heartbeat = None
        self.socket_pub_proof_of_life = None
        self.thread_proof_of_life = None
        self.worker_result = None

    def connect_sockets(self):
        """
        Sets up the sockets to do the communication with the transform_com process through the forwarders
        (for the link and the parameters).
        :return: Nothing
        """
        self.context = zmq.Context()

        # Setup the socket and the stream that receives the pre-transformed data from the com
        self.socket_pull_data = Socket(self.context, zmq.PULL)
        self.socket_pull_data.setsockopt(zmq.LINGER, 0)
        self.socket_pull_data.set_hwm(1)
        self.ssh_com.connect_socket_to_local(self.socket_pull_data, r'tcp://127.0.0.1', self.pull_data_port)
        self.stream_pull_data = zmqstream.ZMQStream(self.socket_pull_data)
        self.stream_pull_data.on_recv(self.data_callback, copy=False)

        # Setup the socket and the stream that receives the parameters of the worker_exec function from the node (gui_com)
        self.socket_sub_parameters = Socket(self.context, zmq.SUB)
        self.socket_sub_parameters.setsockopt(zmq.LINGER, 0)
        self.ssh_com.connect_socket_to_local(self.socket_sub_parameters, r'tcp://127.0.0.1', self.port_sub_parameters)
        self.socket_sub_parameters.subscribe(self.parameters_topic)
        self.stream_parameters = zmqstream.ZMQStream(self.socket_sub_parameters)
        self.stream_parameters.on_recv(self.parameters_callback, copy=False)

        # Setup the socket that pushes the transformed data to the com
        self.socket_push_data = Socket(self.context, zmq.PUSH)
        self.socket_push_data.setsockopt(zmq.LINGER, 0)
        self.socket_push_data.set_hwm(1)
        self.socket_push_data.bind(r"tcp://127.0.0.1:{}".format(self.push_data_port))

        # Setup the socket that receives the heartbeat from the com
        self.socket_pull_heartbeat = self.context.socket(zmq.PULL)
        self.socket_pull_heartbeat.setsockopt(zmq.LINGER, 0)
        self.ssh_com.connect_socket_to_local(self.socket_pull_heartbeat, r'tcp://127.0.0.1', self.pull_heartbeat_port)
        self.stream_heartbeat = zmqstream.ZMQStream(self.socket_pull_heartbeat)
        self.stream_heartbeat.on_recv(self.heartbeat_callback, copy=False)

        # Setup the socket that publishes the fact that the worker_exec is up and running to the node com so that it
        # can then update the parameters of the worker_exec
        self.socket_pub_proof_of_life = Socket(self.context, zmq.PUB)
        self.socket_pub_proof_of_life.setsockopt(zmq.LINGER, 0)
        self.ssh_com.connect_socket_to_local(self.socket_pub_proof_of_life, r'tcp://127.0.0.1',
                                             self.port_pub_proof_of_life, skip_ssh=True)

    def data_callback(self, data):
        """
        The callback that is called when link is send from the previous com process this com process is connected to
        (receives link from and shares a common topic) and pushes the link to the worker_exec.
        The link are a three zmq.Frame list. The first is the topic (used for the worker_exec to distinguish which input the
        link have come from in the case of multiple input nodes). The other two items are the details and the link load
        of the numpy array coming from the previous node).
        :param data: The link received
        :return: Nothing
        """
        data = [data[0].bytes, data[1].bytes, data[2].bytes]
        results = self.work_function(data, self.parameters)
        for array_in_list in results:
            self.socket_push_data.send_array(array_in_list, copy=False)

    def parameters_callback(self, parameters_in_bytes):
        """
        The callback called when there is an update of the parameters (worker_exec function's parameters) from the node
        (send by the gui_com)
        :param parameters_in_bytes:
        :return:
        """
        if len(parameters_in_bytes) > 1:
            args_pyobj = parameters_in_bytes[1].bytes  # remove the topic
            args = pickle.loads(args_pyobj)
            if args is not None:
                self.parameters = args
                #print('Updated parameters in {} = {}'.format(self.parameters_topic, args))

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
                pid = os.getpid()
                self.end_of_life_function()
                self.on_kill(pid)
                os.kill(pid, signal.SIGTERM)
            time.sleep(ct.HEARTBEAT_RATE)

    def proof_of_life(self):
        """
        When the worker_exec process starts it sends to the gui_com (through the proof_of_life_forwarder thread) a signal
        that lets the node (in the gui_com process) that the worker_exec is running and ready to receive parameter updates.
        :return: Nothing
        """

        while self.worker_result is None:
            cv2.waitKey(1)
        print('Sending POL from {} {}'.format(self.node_name, self.node_index))
        self.socket_pub_proof_of_life.send_string(self.parameters_topic + '##' + 'POL')

    def visualisation_loop(self):
        """
        When the visualisation parameter in a node is set to True then this loop starts in a new visualisation thread.
        The thread terminates when the visualisation_on boolean is turned off
        :return: Nothing
        """
        window_showing = False

        while True:
            while self.visualisation_on:
                if not window_showing:
                    window_name = '{} {}'.format(self.node_name, self.node_index)
                    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                    cv2.imshow(window_name, self.worker_result)
                    cv2.waitKey(1)
                    window_showing = True
                if window_showing:
                    width = cv2.getWindowImageRect(window_name)[2]
                    height = cv2.getWindowImageRect(window_name)[3]
                    try:
                        image = cv2.resize(self.worker_result, (width, height), interpolation=cv2.INTER_AREA)
                        cv2.imshow(window_name, image)
                        cv2.waitKey(1)
                    except Exception as e:
                        print(e)
            cv2.destroyAllWindows()
            cv2.waitKey(1)
            window_showing = False

    def visualisation_loop_init(self):
        """
        The function that is run at every cycle of the WORKER_FUNCTION to check if the visualisation_on bool is True
        for the first time. When that happens it starts the visualisation loop. The loop takes care of the showing
        and hiding the visualisation window
        :return: Nothing
        """
        if self.visualisation_on and self.visualisation_thread is None:
            self.visualisation_thread = threading.Thread(target=self.visualisation_loop, daemon=True)
            self.visualisation_on = True
            self.visualisation_thread.start()

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

    def on_kill(self, pid):
        print('Killing {} {} with pid {}'.format(self.node_name, self.node_index, pid))
        try:
            self.socket_pull_data.close()
            self.socket_sub_parameters.close()
            self.socket_push_data.close()
            self.socket_pull_heartbeat.close()
            self.socket_pub_proof_of_life.close()
        except Exception as e:
            print('Trying to kill Transform worker {} failed with error: {}'.format(self.node_name, e))
        finally:
            self.context.term()
            self.ssh_com.kill_tunneling_processes()








