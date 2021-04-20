
import subprocess
import atexit
from dearpygui import simple
from dearpygui.core import *
from Heron.gui import operations_list as op
from Heron.general_utils import kill_child

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
        self.pull_port = None
        self.push_port = None
        self.num_of_inputs = 0
        self.num_of_outputs = 0

        self.get_corresponding_operation()
        self.get_input_and_output_numbers()
        self.generate_default_topics()
        self.get_node_index()

    def get_input_and_output_numbers(self):
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

    def add_topic_out(self, topic):
        for i, t in enumerate(self.topics_out):
            if t == 'NothingOut':
                self.topics_out[i] = topic

    def put_on_editor(self):
        with simple.node(name=self.name, parent='Node Editor##Editor', x_pos=100, y_pos=100):
            for i, attr in enumerate(self.operation.attributes):
                if self.operation.attribute_types[i] == 'Input':
                    output_type = False
                elif self.operation.attribute_types[i] == 'Output':
                    output_type = True
                with simple.node_attribute(attr + '##{}##{}'.format(self.operation.name, self.index),
                                           parent=self.operation.name + '##{}'.format(self.index), output=output_type):
                    add_text('##' + attr + ' Name{}##{}'.format(self.operation.name, self.index), default_value=attr)

    def start_exec(self):
        arguments_list = ['python', self.operation.executable, self.push_port]
        if 'Input' in self.operation.attribute_types and 'Output' in self.operation.attribute_types:
            arguments_list.append(self.pull_port)
        for topic_in in self.topics_in:
            arguments_list.append(topic_in)
        for topic_out in self.topics_out:
            arguments_list.append(topic_out)
        print(arguments_list)

        self.process_pid = subprocess.Popen(arguments_list)
        # creationflags=subprocess.DETACHED_PROCESS)
        atexit.register(kill_child, self.process_pid)

    def stop_exec(self):
        kill_child(self.process_pid)