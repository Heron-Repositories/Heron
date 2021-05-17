
import cv2
import subprocess
import zmq
import numpy as np
from dearpygui import simple
from dearpygui.core import *
from Heron.gui import operations_list as op
from Heron.general_utils import choose_color_according_to_operations_type
from Heron.communication import gui_com

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

        self.get_corresponding_operation()
        self.assign_default_parameters()
        self.get_numbers_of_inputs_and_outputs()
        self.generate_default_topics()
        self.get_node_index()

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
                self.operation = op
                break

    def assign_default_parameters(self):
        self.node_parameters = self.operation.parameters_def_values

    def get_node_index(self):
        self.node_index = self.name.split('##')[-1]

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
        attribute_name = 'Parameters' + '##{}##{}'.format(self.operation.name, self.node_index)
        for i, parameter in enumerate(self.operation.parameters):
            self.node_parameters[i] = get_value('{}##{}'.format(parameter, attribute_name))
        topic = self.operation.name + '##' + self.node_index
        gui_com.SOCKET_PUB_PARAMETERS.send_string(topic, flags=zmq.SNDMORE)
        gui_com.SOCKET_PUB_PARAMETERS.send_pyobj(self.node_parameters)
        #print('Node {} updating parameters {}'.format(self.name, self.node_parameters))

    def spawn_node_on_editor(self):
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
                            elif self.operation.parameter_types[i] == 'bool':
                                add_checkbox('{}##{}'.format(parameter, attribute_name),
                                             default_value=self.node_parameters[i],
                                             callback=self.update_parameters)
                            simple.set_item_width('{}##{}'.format(parameter, attribute_name), width=100)

                    add_spacing(name='##Spacing##'+attribute_name, count=3)

            # Add the verbocity attribute
            attr = 'Verbocity'
            attribute_name = attr + '##{}##{}'.format(self.operation.name, self.node_index)
            with simple.node_attribute(attribute_name, parent=self.operation.name + '##{}'.format(self.node_index),
                                       output=False, static=True):
                add_text('##' + attr + ' Name{}##{}'.format(self.operation.name, self.node_index),
                         default_value=attr)

                add_input_int('##{}'.format(attribute_name), default_value=0)
                simple.set_item_width('##{}'.format(attribute_name), width=100)

    def start_com_process(self):
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

        attribute_name = 'Verbocity##{}##{}'.format(self.operation.name, self.node_index)
        verbocity = str(get_value('##{}'.format(attribute_name)) > 0)
        arguments_list.append(verbocity)

        self.process = subprocess.Popen(arguments_list)

        # Wait until the worker sends a proof_of_life signal (i.e. it is up and running). Then update the parameters
        its_alive = 'No'
        while its_alive != 'POL':
            its_alive = gui_com.SOCKET_SUB_PROOF_OF_LIFE.recv_string()
            if its_alive.split('##')[-3] in self.name:
                its_alive = its_alive.split('##')[-1]
            cv2.waitKey(1)
        self.update_parameters()
        configure_item('##{}'.format(attribute_name), enabled=False)

    def stop_com_process(self):
        self.process.kill()
        self.process = None

        attribute_name = 'Verbocity##{}##{}'.format(self.operation.name, self.node_index)
        configure_item('##{}'.format(attribute_name), enabled=True)


