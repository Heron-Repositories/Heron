
import threading
import platform
import signal
import os
import subprocess
import zmq
import copy
import psutil
import dearpygui.dearpygui as dpg
from Heron.gui import operations_list as op
from Heron.general_utils import choose_color_according_to_operations_type
from Heron.communication.socket_for_serialization import Socket
from Heron import constants as ct, general_utils as gu


class Node:
    def __init__(self, name, parent):
        self.id = None
        self.name = name
        self.parent = parent
        self.operation = None
        self.node_index = None
        self.process = None
        self.topics_out = []
        self.topics_in = []
        self.links_list = []
        self.starting_port = None
        self.num_of_inputs = 0
        self.num_of_outputs = 0
        self.coordinates = [100, 100]
        self.node_parameters = None
        self.node_parameters_combos_items = []
        self.parameter_inputs_ids = {}
        self.com_verbosity = ''
        self.savenodestate_verbosity = ''
        self.verbose = ''
        self.context = None
        self.socket_pub_parameters = None
        self.socket_sub_proof_of_life = None
        self.theme_id = None
        self.extra_window_id = None
        self.possible_cpus_to_pin = ['Any']
        self.cpu_to_pin = 'Any'
        self.operations_list = op.operations_list

        self.get_corresponding_operation()
        self.get_node_index()
        self.assign_default_parameters()
        self.get_numbers_of_inputs_and_outputs()
        self.generate_cpus_to_pin_list()

        self.ssh_server_id_and_names = None
        self.get_ssh_server_names_and_ids()
        self.ssh_local_server = self.ssh_server_id_and_names[0]
        self.ssh_remote_server = self.ssh_server_id_and_names[0]
        self.worker_executable = self.operation.worker_exec

    def generate_cpus_to_pin_list(self):
        n_cpus = psutil.cpu_count()
        for cpu in range(n_cpus):
            self.possible_cpus_to_pin.append(str(cpu))

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
        dpg.remove_alias('verb#{}#{}'.format(self.operation.name, self.node_index))
        if dpg.does_alias_exist('savenodestate#{}#{}'.format(self.operation.name, self.node_index)):
            dpg.remove_alias('savenodestate#{}#{}'.format(self.operation.name, self.node_index))
        dpg.delete_item(self.id)

    def get_numbers_of_inputs_and_outputs(self):
        for at in self.operation.attribute_types:
            if 'Input' in at:
                self.num_of_inputs = self.num_of_inputs + 1
            if 'Output' in at:
                self.num_of_outputs = self.num_of_outputs + 1

    def get_corresponding_operation(self):
        name = self.name.split('##')[0]
        for op in self.operations_list:
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

    def add_topic_in(self, topic):
        topic = topic.replace(' ', '_')
        for t in self.topics_in:
            if t == topic:
                return
        self.topics_in.append(topic)

    def add_topic_out(self, topic):
        topic = topic.replace(' ', '_')
        for t in self.topics_out:
            if topic == t:
                return
        self.topics_out.append(topic)

    def remove_topic_in(self, topic):
        if len(self.topics_in) == 1:
            if self.topics_in[0] == topic:
                self.topics_in[0] = 'NothingIn'
        else:
            for i, t in enumerate(self.topics_in):
                if t == topic:
                    # self.topics_in[i] = ''
                    del self.topics_in[i]
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
            self.node_parameters[i] = dpg.get_value(self.parameter_inputs_ids[parameter])
        topic = self.operation.name + '##' + self.node_index
        topic = topic.replace(' ', '_')
        self.socket_pub_parameters.send_string(topic, flags=zmq.SNDMORE)
        self.socket_pub_parameters.send_pyobj(self.node_parameters)

    def spawn_node_on_editor(self):
        self.context = zmq.Context()
        self.initialise_parameters_socket()

        with dpg.node(label=self.name, parent=self.parent, pos=[self.coordinates[0], self.coordinates[1]]) as self.id:
            colour = choose_color_according_to_operations_type(self.operation.parent_dir)
            with dpg.theme() as self.theme_id:
                with dpg.theme_component(0):
                    dpg.add_theme_color(dpg.mvNodeCol_TitleBar, colour, category=dpg.mvThemeCat_Nodes)
                    dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, colour, category=dpg.mvThemeCat_Nodes)
                    dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, colour, category=dpg.mvThemeCat_Nodes)
                    dpg.add_theme_color(dpg.mvNodeCol_NodeBackgroundSelected, [120, 120, 120, 255],
                                        category=dpg.mvThemeCat_Nodes)
                    dpg.add_theme_color(dpg.mvNodeCol_NodeBackground, [70, 70, 70, 255],
                                        category=dpg.mvThemeCat_Nodes)
                    dpg.add_theme_color(dpg.mvNodeCol_NodeBackgroundHovered, [80, 80, 80, 255],
                                        category=dpg.mvThemeCat_Nodes)
                    dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, [50, 50, 50, 255], category=dpg.mvThemeCat_Nodes)
                    dpg.add_theme_style(dpg.mvNodeStyleVar_NodeBorderThickness, x=4, category=dpg.mvThemeCat_Nodes)
            dpg.bind_item_theme(self.id, self.theme_id)

            # Loop through all the attributes defined in the operation (as seen in the *_com.py file) and put them on
            # the node
            same_line_widget_ids = []
            for i, attr in enumerate(self.operation.attributes):

                if 'Input' in self.operation.attribute_types[i]:
                    attribute_type = dpg.mvNode_Attr_Input
                elif 'Output' in self.operation.attribute_types[i]:
                    attribute_type = dpg.mvNode_Attr_Output
                elif self.operation.attribute_types[i] == 'Static':
                    attribute_type = dpg.mvNode_Attr_Static

                attribute_name = attr + '##{}##{}'.format(self.operation.name, self.node_index)

                with dpg.node_attribute(label=attribute_name, parent=self.id, attribute_type=attribute_type):
                    if attribute_type == 1:
                        dpg.add_spacer()
                    colour = [255, 255, 255, 255]
                    if 'Dict' in self.operation.attributes[i]:
                        colour = [0, 255, 0, 255]
                    dpg.add_text(label='##' + attr + ' Name{}##{}'.format(self.operation.name, self.node_index),
                                 default_value=attr, color=colour)

                    if 'Parameters' in attr:
                        for k, parameter in enumerate(self.operation.parameters):
                            if self.operation.parameter_types[k] == 'int':
                                id = dpg.add_input_int(label='{}##{}'.format(parameter, attribute_name),
                                                       default_value=self.node_parameters[k],
                                                       callback=self.update_parameters, width=100,
                                                       min_clamped=False, max_clamped=False,
                                                       min_value=int(-1e8), max_value=int(1e8), on_enter=True)
                            elif self.operation.parameter_types[k] == 'str':
                                id = dpg.add_input_text(label='{}##{}'.format(parameter, attribute_name),
                                                        default_value=self.node_parameters[k],
                                                        callback=self.update_parameters, width=100, on_enter=True)
                            elif self.operation.parameter_types[k] == 'float':
                                id = dpg.add_input_float(label='{}##{}'.format(parameter, attribute_name),
                                                         default_value=self.node_parameters[k],
                                                         callback=self.update_parameters, width=100,
                                                         min_clamped=False, max_clamped=False,
                                                         min_value=-1e10, max_value=1e10, on_enter=True)
                            elif self.operation.parameter_types[k] == 'bool':
                                id = dpg.add_checkbox(label='{}##{}'.format(parameter, attribute_name),
                                                      default_value=self.node_parameters[k],
                                                      callback=self.update_parameters)
                            elif self.operation.parameter_types[k] == 'list':
                                default_value = self.node_parameters[k][0]
                                if type(self.node_parameters[k]) == str:
                                    default_value = self.node_parameters[k]
                                id = dpg.add_combo(label='{}##{}'.format(parameter, attribute_name),
                                                   items=self.node_parameters_combos_items[k],
                                                   default_value=default_value,
                                                   callback=self.update_parameters, width=100)

                            self.parameter_inputs_ids[parameter] = id

                    dpg.add_spacer(label='##Spacing##'+attribute_name, indent =3)

            # Add the extra input button with its popup window for extra inputs like ssh and verbosity
            self.extra_input_window()

    def extra_input_window(self):
        attr = 'Extra_Input'
        attribute_name = attr + '##{}##{}'.format(self.operation.name, self.node_index)
        with dpg.node_attribute(label=attribute_name, parent=self.id, attribute_type=dpg.mvNode_Attr_Static) as attr_id:

            image_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir, 'resources',
                                      'Blue_glass_button_square_34x34.png')
            
            width, height, channels, data = dpg.load_image(image_file)

            with dpg.texture_registry():
                texture_id = dpg.add_static_texture(width, height, data)

            image_button = dpg.add_image_button(texture_tag =texture_id,
                                                label='##' + attr + ' Name{}##{}'.format(self.operation.name,
                                                                                         self.node_index),
                                                callback=self.update_ssh_combo_boxes)

            with dpg.window(label='##Window#Extra input##{}##{}'.format(self.operation.name, self.node_index),
                            width=550, height=250, pos=[self.coordinates[0] + 400, self.coordinates[1] + 200],
                            show=False, popup=True) as self.extra_window_id:

                # Add the local ssh input
                dpg.add_spacer(height=10)

                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_text('SSH local server')
                    dpg.add_spacer(width=80)
                    dpg.add_text('SSH remote server')

                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    id = dpg.add_combo(label='##SSH local server##Extra input##{}##{}'.format(self.operation.name, self.node_index),
                              items=self.ssh_server_id_and_names,  width=140, default_value=self.ssh_local_server,
                              callback=self.assign_local_server)
                    self.parameter_inputs_ids['SSH local server'] = id
                    dpg.add_spacer(width=40)
                    id = dpg.add_combo(
                        label='##SSH remote server ##Extra input##{}##{}'.format(self.operation.name, self.node_index),
                        items=self.ssh_server_id_and_names,  width=140, default_value=self.ssh_remote_server,
                        callback=self.assign_remote_server)
                    self.parameter_inputs_ids['SSH remote server'] = id

                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_text('Python script of worker process OR Python.exe and script:')

                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_input_text(
                        label='##Worker executable##Extra input##{}##{}'.format(self.operation.name, self.node_index),
                        width=400, default_value=self.worker_executable, callback=self.assign_worker_executable)

                # Add the verbocity input
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    attr = 'Log file or Verbosity level:'
                    attribute_name = attr + '##{}##{}'.format(self.operation.name, self.node_index)
                    self.verbosity_id = dpg.add_text(label='##' + attr + ' Name{}##{}'.format(self.operation.name, self.node_index),
                                                     default_value=attr)

                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_input_text(label='##{}'.format(attribute_name), default_value=self.com_verbosity,
                                       callback=self.update_verbosity, width=400,
                                       hint='Log file name or verbosity level integer.',
                                       tag='verb#{}#{}'.format(self.operation.name, self.node_index))

                # Create the savenodestate input
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_text(default_value='Save the Node State to directory:')

                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_input_text(default_value=self.savenodestate_verbosity, callback=self.update_verbosity,
                                       hint='The path where the Node State for this worker process will be saved',
                                       tag='savenodestate#{}#{}'.format(self.operation.name, self.node_index))

                # Create the pin to CPU input
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_text(default_value='Choose a specific CPU to pin the Com and Worker Processes')

                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_combo(items=self.possible_cpus_to_pin,  width=140, default_value=self.cpu_to_pin,
                                  tag='cpu_pin_combo#{}#{}'.format(self.operation.name, self.node_index),
                                  callback=self.update_cpu_to_pin)

    def update_verbosity(self, sender, data):
        self.com_verbosity = ''
        self.savenodestate_verbosity = ''
        self.savenodestate_verbosity = dpg.get_value('savenodestate#{}#{}'.format(self.operation.name, self.node_index))
        self.com_verbosity = dpg.get_value('verb#{}#{}'.format(self.operation.name, self.node_index))
        self.verbose = '{}||{}'.format(self.com_verbosity, self.savenodestate_verbosity)

    def update_cpu_to_pin(self):
        self.cpu_to_pin = dpg.get_value('cpu_pin_combo#{}#{}'.format(self.operation.name, self.node_index))

    def get_ssh_server_names_and_ids(self):
        ssh_info = gu.get_ssh_info_file()

        self.ssh_server_id_and_names = ['None']
        for id in ssh_info:
            self.ssh_server_id_and_names.append(id + ' ' + ssh_info[id]['Name'])

    def update_ssh_combo_boxes(self):
        dpg.configure_item(self.extra_window_id, show=True)
        self.get_ssh_server_names_and_ids()
        if dpg.does_item_exist(self.parameter_inputs_ids['SSH local server']):
            dpg.configure_item(self.parameter_inputs_ids['SSH local server'], items=self.ssh_server_id_and_names)
        if dpg.does_item_exist(self.parameter_inputs_ids['SSH remote server']):
            dpg.configure_item(self.parameter_inputs_ids['SSH remote server'], items=self.ssh_server_id_and_names)

    def assign_local_server(self, sender, data):
        self.ssh_local_server = dpg.get_value(sender)

    def assign_remote_server(self, sender, data):
        self.ssh_remote_server = dpg.get_value(sender)

    def assign_worker_executable(self, sender, data):
        self.worker_executable = dpg.get_value(sender)

    def start_com_process(self):

        self.initialise_proof_of_life_socket()

        arguments_list = ['python', self.operation.executable, self.starting_port]

        num_of_inputs = len(self.topics_in)
        num_of_outputs = len(self.topics_out)

        arguments_list.append(str(num_of_inputs))
        if 'Input' in self.operation.attribute_types:
            for topic_in in self.topics_in:
                arguments_list.append(topic_in)
        arguments_list.append(str(num_of_outputs))
        if 'Output' in self.operation.attribute_types:
            for topic_out in self.topics_out:
                arguments_list.append(topic_out)
        arguments_list.append(self.name.replace(" ", "_"))

        self.update_verbosity(None, None)   # This is required to make the debugger work because in debug this callback
                                            # is never called
        arguments_list.append(str(self.verbose))
        arguments_list.append(self.ssh_local_server.split(' ')[0])  # pass only the ID part of the 'ID name' string
        arguments_list.append(self.ssh_remote_server.split(' ')[0])
        arguments_list.append(self.worker_executable)
        arguments_list.append(self.cpu_to_pin)

        kwargs = {'start_new_session': True} if os.name == 'posix' else \
        {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}

        self.process = subprocess.Popen(arguments_list, **kwargs)

        print('Started COM {} process with PID = {}'.format(self.name, self.process.pid))
        # Wait until the worker_exec sends a proof_of_life signal (i.e. it is up and running).
        self.wait_for_proof_of_life()

        # Then update the parameters
        self.update_parameters()

        self.start_thread_to_send_parameters_multiple_times()

        with dpg.theme_component(0, parent=self.theme_id):
            dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, [255, 255, 255, 255], category=dpg.mvThemeCat_Nodes)

    def sending_parameters_multiple_times(self):
        for i in range(ct.NUMBER_OF_INITIAL_PARAMETERS_UPDATES):
            self.update_parameters()
            gu.accurate_delay(500)

    def start_thread_to_send_parameters_multiple_times(self):
        thread_parameters = threading.Thread(target=self.sending_parameters_multiple_times, daemon=True)
        thread_parameters.start()

    def wait_for_proof_of_life(self):
        self.socket_sub_proof_of_life.recv()
        self.socket_sub_proof_of_life.recv_string()

    def stop_com_process(self):
        try:
            self.socket_sub_proof_of_life.disconnect(r"tcp://127.0.0.1:{}".format(ct.PROOF_OF_LIFE_FORWARDER_PUBLISH_PORT))
            self.socket_sub_proof_of_life.close()
        except:
            pass

        if platform.system() == 'Windows':
            self.process.send_signal(signal.CTRL_BREAK_EVENT)
        elif platform.system() == 'Linux':
            self.process.terminate()
        gu.accurate_delay(500)
        self.process.kill()
        self.process = None

        with dpg.theme_component(0, parent=self.theme_id):
            dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, [50, 50, 50, 255], category=dpg.mvThemeCat_Nodes)







