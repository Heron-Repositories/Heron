
import threading
import platform
import signal
import os
import time
from pathlib import Path
import json
import subprocess
import zmq
import numpy as np
import copy
from dearpygui import simple
from dearpygui.core import *
from Heron.gui import operations_list as op
from Heron.general_utils import choose_color_according_to_operations_type
from Heron.communication.socket_for_serialization import Socket
from Heron import constants as ct

operations_list = op.operations_list  # This generates all of the Operation dataclass instances currently
# in the Heron/Operations directory


class Node:
    def __init__(self, name):
        self.name = name
        self.operation = None
        self.node_index = None
        self.process = None
        self.topics_out = []
        self.topics_in = []
        self.starting_port = None
        self.num_of_inputs = 0
        self.num_of_outputs = 0
        self.coordinates = [100, 100]
        self.node_parameters = None
        self.node_parameters_combos_items = []
        self.verbose = 0
        self.context = None
        self.socket_pub_parameters = None
        self.socket_sub_proof_of_life = None

        self.get_corresponding_operation()
        self.get_node_index()
        self.assign_default_parameters()
        self.get_numbers_of_inputs_and_outputs()
        self.generate_default_topics()

        self.ssh_server_id_and_names = None
        self.get_ssh_server_names_and_ids()
        self.ssh_local_server = self.ssh_server_id_and_names[0]
        self.ssh_remote_server = self.ssh_server_id_and_names[0]
        self.worker_executable = self.operation.worker_exec

    def initialise_parameters_socket(self):
        if self.context is None:
            self.context = zmq.Context()
        self.socket_pub_parameters = Socket(self.context, zmq.PUB)
        self.socket_pub_parameters.setsockopt(zmq.LINGER, 0)
        self.socket_pub_parameters.connect(r"tcp://127.0.0.1:{}".format(ct.PARAMETERS_FORWARDER_SUBMIT_PORT))

    def initialise_proof_of_life_socket(self):
        if self.context is None:
            self.context = zmq.Context()
        self.socket_sub_proof_of_life = self.context.socket(zmq.SUB)
        self.socket_sub_proof_of_life.setsockopt(zmq.LINGER, 0)
        self.socket_sub_proof_of_life.connect(r"tcp://127.0.0.1:{}".format(ct.PROOF_OF_LIFE_FORWARDER_PUBLISH_PORT))
        self.socket_sub_proof_of_life.setsockopt(zmq.SUBSCRIBE,
                                                 '{}'.format(self.name.replace(' ', '_')).encode('ascii'))

    def remove_from_editor(self):
        delete_item(self.name)

    def get_numbers_of_inputs_and_outputs(self):
        for at in self.operation.attribute_types:
            if at == 'Input':
                self.num_of_inputs = self.num_of_inputs + 1
            if at == 'Output':
                self.num_of_outputs = self.num_of_outputs + 1

    def get_corresponding_operation(self):
        name = self.name.split('##')[0]
        for op in operations_list:
            if op.name == name:
                self.operation = copy.deepcopy(op)
                break

    def assign_default_parameters(self):
        self.node_parameters = self.operation.parameters_def_values
        for default_parameter in self.operation.parameters_def_values:
            if type(default_parameter) == list:
                self.node_parameters_combos_items.append(default_parameter)
            else:
                self.node_parameters_combos_items.append(None)

    def get_node_index(self):
        self.node_index = self.name.split('##')[-1]

    def generate_default_topics(self):
        for at in self.operation.attribute_types:
            if 'Input' in at:
                self.topics_in.append('NothingIn')
            if 'Output' in at:
                self.topics_out.append('NothingOut')

    def add_topic_in(self, topic):
        topic = topic.replace(' ', '_')
        for i, t in enumerate(self.topics_in):
            if t == 'NothingIn':
                self.topics_in[i] = topic
                break

    def add_topic_out(self, topic):
        topic = topic.replace(' ', '_')
        for i, t in enumerate(self.topics_out):
            if t == 'NothingOut':
                self.topics_out[i] = topic
                break

    def remove_topic_in(self, topic):
        if len(self.topics_in) == 1:
            if self.topics_in[0] == topic:
                self.topics_in[0] = 'NothingIn'
        else:
            for i, t in enumerate(self.topics_in):
                if t == topic:
                    self.topics_in[i] = ''
                    break

    def remove_topic_out(self, topic):
        if len(self.topics_out) == 1:
            if self.topics_out[0] == topic:
                self.topics_out[0] = 'NothingOut'
        else:
            for i, t in enumerate(self.topics_out):
                if t == topic:
                    del self.topics_out[i]
                    break

    def update_parameters(self):
        if self.socket_pub_parameters is None:
            self.initialise_parameters_socket()
        attribute_name = 'Parameters' + '##{}##{}'.format(self.operation.name, self.node_index)
        for i, parameter in enumerate(self.operation.parameters):
            self.node_parameters[i] = get_value('{}##{}'.format(parameter, attribute_name))
        topic = self.operation.name + '##' + self.node_index
        topic = topic.replace(' ', '_')
        self.socket_pub_parameters.send_string(topic, flags=zmq.SNDMORE)
        self.socket_pub_parameters.send_pyobj(self.node_parameters)
        #print('Node {} updating parameters {}'.format(self.name, self.node_parameters))

    def spawn_node_on_editor(self):
        self.context = zmq.Context()
        self.initialise_parameters_socket()
        with simple.node(name=self.name, parent='Node Editor##Editor',
                         x_pos=self.coordinates[0], y_pos=self.coordinates[1]):
            colour = choose_color_according_to_operations_type(self.operation.parent_dir)
            set_item_color(self.name, style=mvGuiCol_TitleBg, color=colour)

            # Loop through all the attributes defined in the operation (as seen in the *_com.py file) and put them on
            # the node
            for i, attr in enumerate(self.operation.attributes):

                if self.operation.attribute_types[i] == 'Input':
                    output_type = False
                    static = False
                elif self.operation.attribute_types[i] == 'Output':
                    output_type = True
                    static = False
                elif self.operation.attribute_types[i] == 'Static':
                    output_type = False
                    static = True

                attribute_name = attr + '##{}##{}'.format(self.operation.name, self.node_index)

                with simple.node_attribute(attribute_name, parent=self.operation.name + '##{}'.format(self.node_index),
                                           output=output_type, static=static):
                    add_text('##' + attr + ' Name{}##{}'.format(self.operation.name, self.node_index), default_value=attr)

                    if 'Parameters' in attr:
                        for k, parameter in enumerate(self.operation.parameters):
                            if self.operation.parameter_types[k] == 'int':
                                add_input_int('{}##{}'.format(parameter, attribute_name),
                                              default_value=self.node_parameters[k],
                                              callback=self.update_parameters)
                            elif self.operation.parameter_types[k] == 'str':
                                add_input_text('{}##{}'.format(parameter, attribute_name),
                                               default_value=self.node_parameters[k],
                                               callback=self.update_parameters)
                            elif self.operation.parameter_types[k] == 'float':
                                add_input_float('{}##{}'.format(parameter, attribute_name),
                                                default_value=self.node_parameters[k],
                                                callback=self.update_parameters)
                            elif self.operation.parameter_types[k] == 'bool':
                                add_checkbox('{}##{}'.format(parameter, attribute_name),
                                             default_value=self.node_parameters[k],
                                             callback=self.update_parameters)
                            elif self.operation.parameter_types[k] == 'list':
                                add_combo('{}##{}'.format(parameter, attribute_name),
                                          items=self.node_parameters_combos_items[k],
                                          default_value=self.node_parameters[k][0],
                                          callback=self.update_parameters)
                            simple.set_item_width('{}##{}'.format(parameter, attribute_name), width=100)

                    add_spacing(name='##Spacing##'+attribute_name, count=3)

            # Add the extra input button with its popup window for extra inputs like ssh and verbosity
            self.extra_input_window()

    def extra_input_window(self):
        attr = 'Extra_Input'
        attribute_name = attr + '##{}##{}'.format(self.operation.name, self.node_index)
        with simple.node_attribute(attribute_name, parent=self.operation.name + '##{}'.format(self.node_index),
                                   output=False, static=True):

            add_image_button('##' + attr + ' Name{}##{}'.format(self.operation.name, self.node_index),
                             value=os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir,
                                                'resources', 'Blue_glass_button_square_34x34.png'),
                             callback=self.update_ssh_combo_boxes)
            with simple.popup(popupparent='##' + attr + ' Name{}##{}'.format(self.operation.name, self.node_index),
                              name='Extra input##{}##{}'.format(self.operation.name, self.node_index),
                              mousebutton=mvMouseButton_Left):

                with simple.child('##Window#Extra input##{}##{}'.format(self.operation.name, self.node_index),
                                  width=430, height=180):

                    # Add the local ssh input
                    add_dummy(height=10)
                    add_dummy(width=10)
                    add_same_line()
                    add_text('SSH local server')

                    add_same_line()
                    add_dummy(width=80)
                    add_same_line()
                    add_text('SSH remote server')

                    add_dummy(width=10)
                    add_same_line()
                    add_combo('##SSH local server##Extra input##{}##{}'.format(self.operation.name, self.node_index),
                              items=self.ssh_server_id_and_names,  width=140, default_value=self.ssh_local_server,
                              callback=self.assign_local_server,
                              tip='Add the details of the ssh server running on\n the machine that is running the '
                                  'editor.')
                    add_same_line()
                    add_dummy(width=40)
                    add_same_line()
                    add_combo(
                        '##SSH remote server ##Extra input##{}##{}'.format(self.operation.name, self.node_index),
                        items=self.ssh_server_id_and_names,  width=140, default_value=self.ssh_remote_server,
                        callback=self.assign_remote_server,
                        tip='Add the details of the ssh server that is running on\n the machine that will run the '
                            'worker process of the node.')

                    add_dummy(height=10)
                    add_dummy(width=10)
                    add_same_line()
                    add_text('Python script (or executable) of worker process')

                    add_dummy(width=10)
                    add_same_line()
                    add_input_text(
                        '##Worker executable##Extra input##{}##{}'.format(self.operation.name, self.node_index),
                        width=400, default_value=self.worker_executable, callback=self.assign_worker_executable,
                        tip='Input either the full path of the python script (e.g. /my files/my_script.py) \nor the  '
                            'python command and the script (e.g. pyhton3 /my files/my_script.p) \nor an executable '
                            'file that the system knows how to handle\n(and which speaks the Heron communication '
                            'protocol).\nThe default script is the one that comes with the {} operation.\nIf no command'
                            ' is given with a python script (.py) then Heron will try to run it with the command python'
                            '.\nHeron will look locally first for the script/executable.\nIf it is not found then it '
                            'will assume it resides in the remote machine.'.format(self.name.split('##')[0]))

                    # Add the verbocity input
                    add_dummy(height=6)
                    add_dummy(width=10)
                    add_same_line()
                    attr = 'Verbocity'
                    attribute_name = attr + '##{}##{}'.format(self.operation.name, self.node_index)
                    add_text('##' + attr + ' Name{}##{}'.format(self.operation.name, self.node_index),
                             default_value=attr)
                    add_dummy(width=10)
                    add_same_line()
                    add_input_int('##{}'.format(attribute_name), default_value=self.verbose, callback=self.update_verbosity)
                    simple.set_item_width('##{}'.format(attribute_name), width=100)

    def update_verbosity(self, sender, data):
        self.verbose = get_value(sender)

    def get_ssh_server_names_and_ids(self):
        ssh_info_file = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent, 'communication',
                                     'ssh_info.json')
        with open(ssh_info_file) as f:
            ssh_info = json.load(f)
        self.ssh_server_id_and_names = ['None']
        for id in ssh_info:
            self.ssh_server_id_and_names.append(id + ' ' + ssh_info[id]['Name'])

    def update_ssh_combo_boxes(self):
        self.get_ssh_server_names_and_ids()

        if does_item_exist('##SSH local server##Extra input##{}##{}'.format(self.operation.name, self.node_index)):
            configure_item('##SSH local server##Extra input##{}##{}'.format(self.operation.name, self.node_index),
                           items=self.ssh_server_id_and_names)
        if does_item_exist('##SSH remote server##Extra input##{}##{}'.format(self.operation.name, self.node_index)):
            configure_item('##SSH remote server##Extra input##{}##{}'.format(self.operation.name, self.node_index),
                           items=self.ssh_server_id_and_names)

    def assign_local_server(self, sender, data):
        self.ssh_local_server = get_value(sender)

    def assign_remote_server(self, sender, data):
        self.ssh_remote_server = get_value(sender)

    def assign_worker_executable(self, sender, data):
        self.worker_executable = get_value(sender)

    def start_com_process(self):
        self.initialise_proof_of_life_socket()
        arguments_list = ['python', self.operation.executable, self.starting_port]
        num_of_inputs = len(np.where(np.array(self.operation.attribute_types) == 'Input')[0])
        num_of_outputs = len(np.where(np.array(self.operation.attribute_types) == 'Output')[0])
        arguments_list.append(str(num_of_inputs))
        if 'Input' in self.operation.attribute_types:
            for topic_in in self.topics_in:
                arguments_list.append(topic_in)
        arguments_list.append(str(num_of_outputs))
        if 'Output' in self.operation.attribute_types:
            for topic_out in self.topics_out:
                arguments_list.append(topic_out)
        arguments_list.append(self.name.replace(" ", "_"))

        attribute_name = 'Verbocity##{}##{}'.format(self.operation.name, self.node_index)
        verbocity = str(self.verbose > 0)
        arguments_list.append(verbocity)
        arguments_list.append(self.ssh_local_server.split(' ')[0])  # pass only the ID part of the 'ID name' string
        arguments_list.append(self.ssh_remote_server.split(' ')[0])
        arguments_list.append(self.worker_executable)

        self.process = subprocess.Popen(arguments_list, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

        #print('Pid of Com {} {} = {}'.format(self.name, self.node_index, self.process.pid))
        # Wait until the worker_exec sends a proof_of_life signal (i.e. it is up and running).
        self.wait_for_proof_of_life()

        # Then update the parameters
        self.update_parameters()
        configure_item('##{}'.format(attribute_name), enabled=False)

    def sending_parameters_multiple_times(self):
        for i in range(20):
            self.update_parameters()
            time.sleep(0.5)

    def start_thread_to_send_parameters_multiple_times(self):
        thread_parameters = threading.Thread(target=self.sending_parameters_multiple_times, daemon=True)
        thread_parameters.start()

    def wait_for_proof_of_life(self):
        self.socket_sub_proof_of_life.recv()
        self.socket_sub_proof_of_life.recv_string()
        print('ooo Received POL from {} {}'.format(self.name, self.node_index))

    def stop_com_process(self):
        self.socket_sub_proof_of_life.disconnect(r"tcp://127.0.0.1:{}".format(ct.PROOF_OF_LIFE_FORWARDER_PUBLISH_PORT))
        self.socket_sub_proof_of_life.close()

        if platform.system() == 'Windows':
            self.process.send_signal(signal.CTRL_BREAK_EVENT)
        elif platform.system() == 'Linux':
            self.process.terminate()
        time.sleep(0.5)
        self.process.kill()
        self.process = None

        attribute_name = 'Verbocity##{}##{}'.format(self.operation.name, self.node_index)
        configure_item('##{}'.format(attribute_name), enabled=True)


