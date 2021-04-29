
import subprocess
import atexit
import zmq
import time
import numpy as np
from dearpygui import simple
from dearpygui.core import *
from Heron.gui import operations_list as op
from Heron.general_utils import kill_child, choose_color_according_to_operations_type
from Heron.communication import gui_com

operations_list = op.operations_list  # This generates all of the Operation dataclass instances currently
# in the Heron/Operations directory


class Node:
    def __init__(self, name):
        self.name = name
        self.operation = None
        self.index = None
        self.process_pid = None
        self.topics_out = []
        self.topics_in = []
        self.starting_port = None
        self.num_of_inputs = 0
        self.num_of_outputs = 0
        self.coordinates = [100, 100]
        self.node_parameters = None

        self.get_corresponding_operation()
        self.assign_default_parameters()
        self.get_numbers_of_inputs_and_outputs()
        self.generate_default_topics()
        self.get_node_index()

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
                self.operation = op
                break

    def assign_default_parameters(self):
        self.node_parameters = self.operation.parameters_def_values

    def get_node_index(self):
        self.index = self.name.split('##')[-1]

    def generate_default_topics(self):
        for at in self.operation.attribute_types:
            if 'Input' in at:
                self.topics_in.append('NothingIn')
            if 'Output' in at:
                self.topics_out.append('NothingOut')

    def add_topic_in(self, topic):
        for i, t in enumerate(self.topics_in):
            if t == 'NothingIn':
                self.topics_in[i] = topic
                break

    def add_topic_out(self, topic):
        for i, t in enumerate(self.topics_out):
            if t == 'NothingOut':
                self.topics_out[i] = topic
                break

    def update_parameters(self):
        attribute_name = 'Parameters' + '##{}##{}'.format(self.operation.name, self.index)
        for i, parameter in enumerate(self.operation.parameters):
            self.node_parameters[i] = get_value('{}##{}'.format(parameter, attribute_name))
        topic = self.operation.name + '##' + self.index
        gui_com.SOCKET_PUB_STATE.send_string(topic, flags=zmq.SNDMORE)
        gui_com.SOCKET_PUB_STATE.send_pyobj(self.node_parameters)

    def put_on_editor(self):
        with simple.node(name=self.name, parent='Node Editor##Editor',
                         x_pos=self.coordinates[0], y_pos=self.coordinates[1]):
            colour = choose_color_according_to_operations_type(self.operation.parent_dir)
            set_item_color(self.name, style=mvGuiCol_TitleBg, color=colour)

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

                attribute_name = attr + '##{}##{}'.format(self.operation.name, self.index)

                with simple.node_attribute(attribute_name, parent=self.operation.name + '##{}'.format(self.index),
                                           output=output_type, static=static):
                    add_text('##' + attr + ' Name{}##{}'.format(self.operation.name, self.index), default_value=attr)

                    if 'Parameters' in attr:
                        for i, parameter in enumerate(self.operation.parameters):
                            if self.operation.parameter_types[i] == 'int':
                                add_input_int('{}##{}'.format(parameter, attribute_name),
                                              default_value=self.node_parameters[i],
                                              callback=self.update_parameters)
                            elif self.operation.parameter_types[i] == 'str':
                                add_input_text('{}##{}'.format(parameter, attribute_name),
                                               default_value=self.node_parameters[i],
                                               callback=self.update_parameters)
                            elif self.operation.parameter_types[i] == 'float':
                                add_input_float('{}##{}'.format(parameter, attribute_name),
                                                default_value=self.node_parameters[i],
                                                callback=self.update_parameters)
                            simple.set_item_width('{}##{}'.format(parameter, attribute_name), width=100)

                    add_spacing(name='##Spacing##'+attribute_name, count=3)

    def generate_argument_list_for_executable(self):
        arguments_list = ['python', self.operation.executable, self.starting_port]

    def start_exec(self):
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
        arguments_list.append(self.name)

        self.process_pid = subprocess.Popen(arguments_list)
        atexit.register(kill_child, self.process_pid)

        time.sleep(0.8)
        self.update_parameters()

    def stop_exec(self):
        self.process_pid.kill()
        self.process_pid = None
