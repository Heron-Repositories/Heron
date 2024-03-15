
import time
import threading
import pickle
import os
import signal
import zmq
import numpy as np
import sys

from zmq.eventloop import ioloop, zmqstream
from Heron import constants as ct, general_utils as gu
from Heron.communication.socket_for_serialization import Socket
from Heron.communication.ssh_com import SSHCom
from Heron.gui.save_node_state import SaveNodeState


class SinkWorker:
    def __init__(self, recv_topics_buffer, pull_port, initialisation_function, work_function, end_of_life_function,
                 parameters_topic, num_sending_topics, savenodestate_path,
                 ssh_local_ip=' ', ssh_local_username=' ', ssh_local_password=' '):

        self.pull_data_port = pull_port
        self.push_data_port = str(int(self.pull_data_port) + 1)
        self.pull_heartbeat_port = str(int(self.pull_data_port) + 2)
        self.work_function = work_function
        self.initialisation_function = initialisation_function
        self.end_of_life_function = end_of_life_function
        self.parameters_topic = parameters_topic
        self.num_sending_topics = int(num_sending_topics)
        self.recv_topics_buffer = recv_topics_buffer

        self.loops_on = True
        self.initialised = False
        self.node_name = self.parameters_topic.split('##')[-2]
        self.node_index = self.parameters_topic.split('##')[-1]

        self.savenodestate_path = savenodestate_path
        self.heron_savenodestate = None
        self.num_of_iters_to_update_savenodestate_substate = None

        self.ssh_com = SSHCom(ssh_local_ip=ssh_local_ip, ssh_local_username=ssh_local_username,
                              ssh_local_password=ssh_local_password)

        self.time_of_pulse = time.perf_counter()
        self.port_sub_parameters = ct.PARAMETERS_FORWARDER_PUBLISH_PORT
        self.port_pub_proof_of_life = ct.PROOF_OF_LIFE_FORWARDER_SUBMIT_PORT

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
        self.index = 0

    def connect_sockets(self):
        """
        Sets up the sockets to do the communication with the transform_com process through the forwarders
        (for the link and the parameters).
        :return: Nothing
        """
        self.context = zmq.Context()

        # Setup the socket and the stream that receives the data from the com to be worked upon
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

        # Setup the socket that pushes the end of worker function signal to the com
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

        # Setup the socket that sends (publishes) the fact that the worker_exec is up and running to the node com so that it
        # can then update the parameters of the worker_exec
        self.socket_pub_proof_of_life = Socket(self.context, zmq.PUB)
        self.socket_pub_proof_of_life.setsockopt(zmq.LINGER, 0)
        self.ssh_com.connect_socket_to_local(self.socket_pub_proof_of_life, r'tcp://127.0.0.1',
                                             self.port_pub_proof_of_life, skip_ssh=False)

    def data_callback(self, data):
        """
        The callback that is called when link is send from the previous com process this com process is connected to
        (receives link from and shares a common topic) and pushes the link to the worker_exec.
        The link are a three zmq.Frame list. The first is the topic (used for the worker_exec to distinguish which input the
        link have come from in the case of multiple input nodes). The other two items are the details and the link load
        of the numpy array coming from the previous node). Once the work function returns the com process is notified
        with a ct.IGNORE signal
        :param data: The link received
        :return: Nothing
        """
        if self.initialised:
            data = [data[0].bytes, data[1].bytes, data[2].bytes] # Turn that on if the stream_pull_data.on_recv has copy=False

            try:
                self.work_function(data, self.parameters, self.savenodestate_update_substate_df)
            except TypeError:
                self.work_function(data, self.parameters)

            self.index += 1
        self.socket_push_data.send_data(np.array([ct.IGNORE]), copy=False)

    def savenodestate_create_parameters_df(self, **parameters):
        """
        Creates a new savenodestate with the Parameters pandasdf in it or adds the Parameters pandasdf in the existing Node's
        Relic.
        :param parameters: The dictionary of the parameters. The keys of the dict will become the column names of the
        pandasdf
        :return: Nothing
        """
        self._savenodestate_create_df('Parameters', **parameters)

    def savenodestate_create_substate_df(self, **variables):
        """
        Creates a new savenodestate with the Substate pandasdf in it or adds the Substate pandasdf in the existing Node's Relic.
        :param variables: The dictionary of the variables to save. The keys of the dict will become the column names of
        the pandasdf
        :return: Nothing
        """
        self._savenodestate_create_df('Substate', **variables)

    def _savenodestate_create_df(self, type, **variables):
        """
        Base function to create either a Parameters or a Substate pandasdf in a new or the existing Node's Relic
        :param type: Parameters or Substate
        :param variables: The variables dictionary to be saved in the pandas. The keys of the dict will become the c
        olumn names of the pandasdf
        :return: Nothing
        """
        if self.heron_savenodestate is None:
            self.heron_savenodestate = SaveNodeState(self.savenodestate_path, self.node_name,
                                                  self.node_index, self.num_of_iters_to_update_savenodestate_substate)
        if self.heron_savenodestate.operational:
            self.heron_savenodestate.create_the_pandasdf(type, **variables)

    def savenodestate_update_substate_df(self, **variables):
        """
        Updates the Substate pandasdf of the Node's Relic
        :param variables: The Substate's variables dict
        :return: Nothing
        """
        self.heron_savenodestate.update_the_substate_pandasdf(self.index, **variables)

    def parameters_callback(self, parameters_in_bytes):
        """
        The callback called when there is an update of the parameters (worker_exec function's parameters) from the node
        (send by the gui_com)
        :param parameters_in_bytes:
        :return:
        """
        #print('UPDATING PARAMETERS OF {} {}'.format(self.node_name, self.node_index))
        if len(parameters_in_bytes) > 1:
            args_pyobj = parameters_in_bytes[1].bytes  # remove the topic
            args = pickle.loads(args_pyobj)
            if args is not None:
                self.parameters = args
                if not self.initialised and self.initialisation_function is not None:
                    self.initialised = self.initialisation_function(self)
                #print('Updated parameters in {} = {}'.format(self.parameters_topic, args))

                if self.initialised and self.heron_savenodestate is not None and self.heron_savenodestate.operational:
                    self.heron_savenodestate.update_the_parameters_pandasdf(parameters=self.parameters, worker_index=self.index)

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
        while self.loops_on:
            current_time = time.perf_counter()
            if current_time - self.time_of_pulse > ct.HEARTBEAT_RATE * ct.HEARTBEATS_TO_DEATH:
                pid = os.getpid()
                self.end_of_life_function()
                self.on_kill(pid)
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.5)
            time.sleep(ct.HEARTBEAT_RATE)
        self.socket_pull_heartbeat.close()

    def proof_of_life(self):
        """
        When the worker_exec process starts it sends to the gui_com (through the proof_of_life_forwarder thread) a signal
        that lets the node (in the gui_com process) that the worker_exec is running and ready to receive parameter updates.
        :return: Nothing
        """
        # gu.print_and_logging('--- Sending POL from {} {}'.format(self.node_name, self.node_index))
        for i in range(100):
            try:
                self.socket_pub_proof_of_life.send(self.parameters_topic.encode('ascii'), zmq.SNDMORE)
                self.socket_pub_proof_of_life.send_string('POL')
            except:
                pass
            gu.accurate_delay(10)
        # gu.print_and_logging('--- Finished sending POL from {}'.format(self.node_name))

    def start_ioloop(self):
        """
        Starts the heartbeat thread daemon and the ioloop of the zmqstreams
        :return: Nothing
        """
        self.thread_heartbeat = threading.Thread(target=self.heartbeat_loop, daemon=True)
        self.thread_heartbeat.start()

        self.thread_proof_of_life = threading.Thread(target=self.proof_of_life, daemon=True)
        self.thread_proof_of_life.start()
        print('Started Worker {}_{} process with PID = {}'.format(self.node_name, self.node_index, os.getpid()))
        ioloop.IOLoop.instance().start()
        print('!!! WORKER {} HAS STOPPED'.format(self.parameters_topic))

    def on_kill(self, pid):
        print('Killing {} {} with pid {}'.format(self.node_name, self.node_index, pid))

        if self.heron_savenodestate is not None and self.heron_savenodestate.substate_pandasdf_exists:
            self.heron_savenodestate.save_substate_at_death()

        try:
            self.loops_on = False
            self.stream_pull_data.close()
            self.stream_parameters.close()
            self.stream_heartbeat.close()
            self.socket_pull_data.close()
            self.socket_push_data.close()
            self.socket_sub_parameters.close()
            self.socket_pub_proof_of_life.close()
        except Exception as e:
            print('Trying to kill Transform worker {} failed with error: {}'.format(self.node_name, e))
        finally:
            self.context.term()
            self.ssh_com.kill_tunneling_processes()








