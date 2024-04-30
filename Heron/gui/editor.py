import platform
import signal
import time
import subprocess
import os
from os.path import dirname, join
from pathlib import Path
import numpy as np
import json
import copy
import sys
import ctypes
import threading

sys.path.insert(0, dirname(dirname(dirname(os.path.realpath(__file__)))))
import Heron.general_utils as gu
from Heron.gui import operations_list as op_list
from Heron.gui.node import Node
from Heron.gui.fdialog import FileDialog
from Heron import constants as ct
from Heron.gui import ssh_info_editor, create_new_node, settings
import dearpygui.dearpygui as dpg

operations_list = op_list.generate_operations_list()
heron_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
last_used_port = 6050
nodes_list = []
links_dict = {}
panel_coordinates = [0, 0]
mouse_dragging_deltas = [0, 0]
forwarders: subprocess.Popen
node_selector: int
italic_font: int
port_generator = gu.get_next_available_port_group(last_used_port, ct.MAXIMUM_RESERVED_SOCKETS_PER_NODE)
last_visited_directory = os.path.expanduser('~')

node_editor = None
start_graph_button_id = None
end_graph_button_id = None
node_editor_window = None


def generate_node_tree():
    """
        The function that looks into the Heron/Operations path and creates a list of tuples of
        directories where the first element in the tuple is a dir and the second is
        its parent dir. All names for the dirs are generated (using ## to separate the different
        parts of the node_name) in such a way that can be used by dearpygui (i.e. they are
        unique and the first part before the first ## - which is the one that shows on a widget - is
        descriptive of the dir or the file).
        So one tuple would be ('Transforms##Operations##', 'Vision##Transforms##Operations##') which
        would mean that a dir called Vision (with real node_name Vision##Transforms##Operations##) has as
        its parent dir a dir called Transforms (with real node_name Transforms##Operations##). The list does not include
        the directories that house the actual code (each operation must have its own directory into which any
        python files must exist).
        The returned list can be used in a tree_node widget.
        :return: The list of tuples (parent dir, dir)
        """
    path_to_nodes = os.path.join(heron_path, 'Operations')
    node_dirs = []
    dir_ids = {}
    dir_id = 100000
    for d in os.walk(path_to_nodes):
        if len(d[1]) > 0:
            temp = d[0].split(os.path.sep)
            i = -1
            parent = ''
            while temp[i] != 'Heron':
                parent = parent + temp[i] + '##'
                if not dir_ids:
                    parent_int = 100000
                else:
                    try:
                        parent_int = dir_ids[parent]
                    except:
                        pass
                i = i - 1
            if len(d[1]) > 0 and '__top__' not in d[1]:
                if '__' not in d[0]:
                    for dir in d[1]:
                        if '__' not in dir:
                            dir_name = dir + '##' + parent
                            dir_id += 1
                            dir_ids[dir_name] = dir_id
                            node_dirs.append((parent_int, parent, dir_id, dir_name))
    return node_dirs


def on_add_node(sender, data):
    """
    The callback that creates a Heron.gui.node.Node in the node editor for the operation defined by the button
    calling the callback.
    :param sender: The button's node_name
    :param data: Not used
    :return: Nothing
    """
    global node_editor

    sender_name = dpg.get_item_label(sender)
    # Get corresponding operation
    operation = None
    for op in operations_list:
        if op.name == sender_name:
            operation = op
            break

    # Find how many other nodes there are already on the editor for the same operation
    num_of_same_nodes = 0
    all_nodes = dpg.get_item_children(node_editor)[1]

    for n in all_nodes:
        name = dpg.get_item_label(n)
        if operation.name in name:
            num_of_same_nodes = num_of_same_nodes + 1

    # Create the Node
    name = operation.name + '##{}'.format(num_of_same_nodes)
    n = Node(name=name, parent=node_editor)
    n.spawn_node_on_editor(dpg.get_item_pos(node_editor_window))
    n.starting_port = next(port_generator)
    nodes_list.append(n)


def on_link(sender, link):
    """
    When a link is created it is stored as a topic_out in the node with the output and as a topic_in in the
    node with the input
    :param sender: The node editor (not used)
    :param link: The link list
    :return: Nothing
    """
    global links_dict

    link0_name = dpg.get_item_label(link[0])
    link1_name = dpg.get_item_label(link[1])

    if link0_name in links_dict:
        inputs = links_dict[link0_name]
        if link1_name not in links_dict[link0_name]:
            inputs.append(link1_name)
    else:
        inputs = [link1_name]

    link_id = dpg.add_node_link(link[0], link[1], parent=sender, user_data={})

    links_dict[link0_name] = inputs

    output_node_label = dpg.get_item_label(link[0])
    input_node_label = dpg.get_item_label(link[1])
    output_node = output_node_label.split('##')[-2] + '##' + output_node_label.split('##')[-1]
    input_node = input_node_label.split('##')[-2] + '##' + input_node_label.split('##')[-1]
    for n in nodes_list:
        if output_node == n.name:
            topic_out = '{}->{}'.format(output_node_label, input_node_label)
            n.add_topic_out(topic_out)
            n.links_list.append(link_id)
            user_data = dpg.get_item_user_data(link_id)
            user_data['topic_out'] = topic_out
            user_data['node_id_out'] = n.id
            dpg.set_item_user_data(link_id, user_data)
        if input_node == n.name:
            topic_in = '{}->{}'.format(output_node_label, input_node_label)
            n.add_topic_in(topic_in)
            n.links_list.append(link_id)
            user_data = dpg.get_item_user_data(link_id)
            user_data['topic_in'] = topic_in
            user_data['node_id_in'] = n.id
            dpg.set_item_user_data(link_id, user_data)


def delete_link(sender, link):
    """
    Deletes a link and removes the topics (in and out) it represents from the corresponding nodes
    :param sender: Not used
    :param link: The id of the link item
    :return: Nothing
    """
    global links_dict
    link_conf = dpg.get_item_configuration(link)
    output_node = link_conf['user_data']['node_id_out']
    input_node = link_conf['user_data']['node_id_in']
    topic_out = link_conf['user_data']['topic_out']
    topic_in = link_conf['user_data']['topic_in'].replace(' ', '_')

    del links_dict[topic_out.split('-')[0]]
    topic_out = topic_out.replace(' ', '_')

    for n in nodes_list:
        if output_node == n.id:
            n.remove_topic_out(topic_out)
            n.links_list.remove(link)
        if input_node == n.id:
            n.remove_topic_in(topic_in)
            n.links_list.remove(link)
    dpg.delete_item(link)


def start_forwarders_process(path_to_com):
    """
    This initialises the two processes that run the two forwarders connecting the link flow between com and worker_exec
    processes and the parameters flow between the same processes
    :param path_to_com: The path that the two python files that define the processes are
    :return: Nothing
    """
    global forwarders

    kwargs = {'start_new_session': True} if os.name == 'posix' else \
        {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
    forwarders = subprocess.Popen(['python', os.path.join(path_to_com, 'forwarders.py'), 'False', 'False', 'False'],
                                  **kwargs)

    print('Main loop PID = {}'.format(os.getpid()))
    print('Forwarders PID = {}'.format(forwarders.pid))


def on_start_graph(sender, data):
    """
    The callback of the Start Graph button. It reads all the connections between the nodes and starts all the
    required processes assigning the correct topics and ports to each one of them so that the resulting
    communication between the processes resembles the node graph in the editor.
    :param sender: Not used
    :param data: Not used
    :return: Nothing
    """

    if nodes_list:

        path_to_com = Path(os.path.dirname(os.path.realpath(__file__)))
        path_to_com = os.path.join(path_to_com.parent, 'communication')

        start_forwarders_process(path_to_com)
        for n in nodes_list:
            n.start_com_process()
        update_control_graph_buttons(True)


def on_end_graph(sender, data):
    """
    Kill all running processes (except the one running the gui). Also shows a progress bar while waiting for processes
    to die. They need a HEARTBEAT_RATE * HEARTBEATS_TO_DEATH seconds to die.
    :param sender: Not used
    :param data: Not used
    :return: Nothing
    """
    global forwarders
    heartbeat_rate = settings.settings_dict['Operation']['HEARTBEAT_RATE']
    heartbeats_to_death = settings.settings_dict['Operation']['HEARTBEATS_TO_DEATH']

    for n in nodes_list:
        n.stop_com_process()

    if platform.system() == 'Windows':
        forwarders.send_signal(signal.CTRL_BREAK_EVENT)
    elif platform.system() == 'Linux':
        forwarders.terminate()

    with dpg.window(label='Progress bar', pos=[500, 400], width=440, height=40, no_collapse=True,
                    no_close=True) as progress_bar:
        killing_proc_bar = dpg.add_progress_bar(label='Killing processes', parent=progress_bar, width=400, height=40,
                                                overlay='Closing worker_exec processes', indent=10)
        t = 0
        while t < heartbeat_rate * heartbeats_to_death:
            dpg.set_value(killing_proc_bar, t / (heartbeat_rate * heartbeats_to_death))
            t = t + 0.1
            time.sleep(0.1)
        dpg.delete_item(killing_proc_bar)
    update_control_graph_buttons(False)
    dpg.delete_item(progress_bar)

    forwarders.kill()
    del forwarders


def on_del_pressed(sender, key_value):
    global node_editor

    indices_to_remove = []
    for node in dpg.get_selected_nodes(node_editor=node_editor):
        node_name = dpg.get_item_label(node)
        for i in np.arange(len(nodes_list) - 1, -1, -1):
            if nodes_list[i].name == node_name:
                indices_to_remove.append(i)

    delete_node(indices_to_remove)


def check_for_del_press_on_node():
    while True:
        indices_to_remove = []
        for i, n in enumerate(nodes_list):
            if n.to_be_deleted:
                indices_to_remove.append(i)

        if len(indices_to_remove) > 0:
            delete_node(indices_to_remove)

        time.sleep(0.2)


def delete_node(indices_to_remove):
    for i in indices_to_remove:
        links_to_be_deleted = copy.copy(nodes_list[i].links_list)
        for link in links_to_be_deleted:
            delete_link(None, link)
        nodes_list[i].remove_from_editor()
        nodes_list[i] = None
        del nodes_list[i]

    for link in dpg.get_selected_links(node_editor=node_editor):
        delete_link(None, link)


def update_control_graph_buttons(is_graph_running):
    """
    Used to enable and disable (grey out) the Start Graph or the End Graph according to whether the Graph is running or
    not
    :param is_graph_running: Is the graph running bool
    :return: Nothing
    """
    global start_graph_button_id
    global end_graph_button_id

    with dpg.theme() as theme_active:
        with dpg.theme_component(0):
            dpg.add_theme_color(dpg.mvThemeCol_Button, [50, 50, 180, 255], category=dpg.mvThemeCat_Core)

    with dpg.theme() as theme_non_active:
        with dpg.theme_component(0):
            dpg.add_theme_color(dpg.mvThemeCol_Button, [150, 150, 150, 255], category=dpg.mvThemeCat_Core)

    if is_graph_running:
        dpg.configure_item(start_graph_button_id, enabled=False)
        dpg.bind_item_theme(start_graph_button_id, theme_non_active)
        dpg.configure_item(end_graph_button_id, enabled=True)
        dpg.bind_item_theme(end_graph_button_id, theme_active)
    else:
        dpg.configure_item(start_graph_button_id, enabled=True)
        dpg.bind_item_theme(start_graph_button_id, theme_active)
        dpg.configure_item(end_graph_button_id, enabled=False)
        dpg.bind_item_theme(end_graph_button_id, theme_non_active)


def on_save_file_selected(selected_files):
    global links_dict
    global last_visited_directory

    save_to = selected_files[0]
    last_visited_directory = dirname(save_to)
    node_dict = {}
    for n in nodes_list:
        n.socket_pub_parameters = None
        n.socket_sub_proof_of_life = None
        n.context = None
        try:
            n.operations_list = None  # This line is in a try to make saves before Heron 0.5.5 work
        except:
            pass
        n = copy.deepcopy(n)
        node_dict[n.name] = n.__dict__
        node_dict[n.name]['operation'] = node_dict[n.name]['operation'].__dict__

    node_dict['links'] = links_dict

    with open(save_to, 'w+') as file:
        json.dump(node_dict, file, indent=4)


def save_graph():
    """
    Saves the current graph
    :return: Nothing
    """
    global last_visited_directory

    file_dialog = FileDialog(show_dir_size=False, modal=False, allow_drag=False, file_filter='.json',
                             show_hidden_files=True, multi_selection=False, tag='file_dialog',
                             default_path=last_visited_directory, dirs_only=False, callback=on_save_file_selected)
    file_dialog.show_file_dialog()


def get_attribute_id_from_label(label):
    global node_editor

    all_editors_children = dpg.get_item_children(node_editor, 1)
    for node_id in all_editors_children:
        all_nodes_childern = dpg.get_item_children(node_id, slot=1)
        for child_id in all_nodes_childern:
            child_label = dpg.get_item_label(child_id)
            if child_label == label:
                return child_id


def do_the_loading_of_json_file(selected_files):
    global nodes_list
    global last_used_port
    global port_generator
    global links_dict
    global node_editor
    global last_visited_directory

    load_file = selected_files[0]
    last_visited_directory = dirname(load_file)

    with open(load_file, 'r') as file:
        raw_dict = json.load(file)
        nodes_list = []

        for key in raw_dict.keys():
            if key != 'links':
                value = raw_dict[key]
                n = Node(name=value['name'], parent=node_editor)
                op_dict = value['operation']
                if 'tooltip' not in op_dict.keys():
                    not_available_text = 'Documentation not available'
                    num_of_params = len(op_dict['parameters'])
                    num_of_inputs_outputs = len([i for i in op_dict['attribute_types'] if i != 'Static'])
                    op_dict['tooltip'] = not_available_text,
                    op_dict['parameter_tooltips'] = [not_available_text] * num_of_params
                    op_dict['attribute_tooltips'] = [not_available_text] * num_of_inputs_outputs
                n.operation = op_list.create_operation_from_dictionary(op_dict)
                n.node_index = value['node_index']
                n.process = value['process']
                n.topics_out = value['topics_out']
                n.topics_in = value['topics_in']
                n.starting_port = value['starting_port']
                n.num_of_inputs = value['num_of_inputs']
                n.num_of_outputs = value['num_of_outputs']
                n.coordinates = value['coordinates']
                n.node_parameters = value['node_parameters']
                n.node_parameters_combos_items = value['node_parameters_combos_items']
                n.ssh_local_server = value['ssh_local_server']
                n.ssh_remote_server = value['ssh_remote_server']
                try:
                    n.savenodestate_verbosity = value['savenodestate_verbosity']
                    n.com_verbosity = value['com_verbosity']
                    n.verbose = '{}||{}'.format(n.com_verbosity, n.savenodestate_verbosity)
                    n.cpu_to_pin = value['cpu_to_pin']
                except:
                    n.verbose = value['verbose']
                n.context = value['context']
                n.socket_pub_parameters = value['socket_pub_parameters']
                n.socket_sub_proof_of_life = value['socket_sub_proof_of_life']
                n.worker_executable = value['worker_executable']
                n.spawn_node_on_editor(dpg.get_item_pos(node_editor_window))

                nodes_list.append(n)

                if int(n.starting_port) > last_used_port:
                    last_used_port = int(n.starting_port)

            elif key == 'links':
                links_dict = raw_dict[key]

                for l1_name in links_dict:
                    l1 = get_attribute_id_from_label(l1_name)
                    for l2_name in copy.copy(links_dict[l1_name]):
                        l2 = get_attribute_id_from_label(l2_name)
                        on_link(node_editor, [l1, l2])

    last_used_port = last_used_port + ct.MAXIMUM_RESERVED_SOCKETS_PER_NODE
    port_generator = gu.get_next_available_port_group(last_used_port, ct.MAXIMUM_RESERVED_SOCKETS_PER_NODE)


def load_graph():
    """
    Loads a saved graph
    :return: Nothing
    """
    global last_visited_directory

    clear_editor()

    file_dialog = FileDialog(show_dir_size=False, modal=False, allow_drag=False, file_filter='.json',
                             show_hidden_files=True, multi_selection=False, tag='file_dialog',
                             default_path=last_visited_directory, dirs_only=False, callback=do_the_loading_of_json_file)
    file_dialog.show_file_dialog()


# TODO: Add a UI asking the user if they are sure (and that all link will be lost)
def clear_editor():
    """
    Clear the editor of all nodes and links
    :return: Nothing
    """
    global nodes_list
    global node_editor

    if dpg.get_item_children(node_editor, slot=1):
        for n in dpg.get_item_children(node_editor, slot=1):
            dpg.delete_item(n)
        for a in dpg.get_aliases():
            dpg.remove_alias(a)
    nodes_list = []


def add_new_symbolic_link_node_folder(sender, app_data, user_data=None):
    global last_visited_directory

    def delete_error_popup_aliases():
        if dpg.does_alias_exist('modal_error_id'):
            dpg.delete_item('modal_error_id')
        if dpg.does_alias_exist("modal_id_credentials"):
            dpg.delete_item("modal_id_credentials")
            print('killed creds window')
        if dpg.does_alias_exist("modal_id_folders_not_found"):
            dpg.delete_item("modal_id_folders_not_found")
            print('killed wrong folder window')
            
    def create_error_window(error_text, spacer):
        with dpg.window(label="Error Window", modal=True, show=True, id="modal_error_id",
                        no_title_bar=True, popup=True, pos=[500, 300]):
            dpg.add_text(error_text)
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=spacer)
                dpg.add_button(label="OK", width=75, callback=delete_error_popup_aliases)

    # Check if in Windows and running as an Admin
    if os.name == 'nt' and ctypes.windll.shell32.IsUserAnAdmin() == 0:
        error_text = 'In Windows you need to run the python that runs Heron\n' \
                     'with elevated credentials in order to create a symbolic link.\n' \
                     'Restart Heron with a python that has started with "Run as Administrator".'
        spacer = 160
        create_error_window(error_text, spacer)
        return False

    delete_error_popup_aliases()

    def on_folder_select(selected_files):
        global node_selector
        global operations_list
        global last_visited_directory

        main_folders = ['Sources', 'Transforms', 'Sinks']
        operations_directory = selected_files[0]
        last_visited_directory = dirname(operations_directory)

        def add_symlink(target, link):
            try:
                os.symlink(target, link)
                return True
            except Exception as e:
                if 'Cannot create a file when that file already exists' in str(e):
                    if os.path.islink(link):
                        os.unlink(link)
                        os.symlink(target, link)
                        return True
                    else:
                        error_text = f'There is a folder {link}\n' \
                                     'in the Heron Operations dir that has the same name\n' \
                                     f'as the source folder {target} \n' \
                                     'but is not a symbolic link. No symbolic link can be created overriding it.'
                        spacer = 160
                        create_error_window(error_text, spacer)
                        return False
                else:
                    error_text = str(e)
                    spacer = 300
                    create_error_window(error_text, spacer)
                    return False

        folders_exist = False
        for f in main_folders:
            if os.path.isdir(os.path.join(operations_directory, f)):
                folders_exist = True
                for d in os.listdir(os.path.join(operations_directory, f)):
                    target = os.path.join(operations_directory, f, d)
                    link = os.path.join(heron_path, 'Operations', f, d)
                    if not os.path.isdir(link):
                        os.mkdir(link)

                    for inner_dir in os.listdir(target):
                        link_inner = os.path.join(link, inner_dir)
                        inner_target = os.path.join(target, inner_dir)
                        if not add_symlink(inner_target, link_inner):
                            if '__top__' in inner_dir:
                                pass
                            else:
                                return

        if not folders_exist:
            error_text = "The selected Directory {} \n" \
                         "doesn't have at least one of the\n" \
                         "Sources, Transforms or Sinks folders in it, so it cannot\n" \
                         "be Heron Node code. Please select another directory.".format(operations_directory)
            create_error_window(error_text, 120)
        else:
            dpg.delete_item(node_selector)
            operations_list = op_list.generate_operations_list()
            Node.operations_list = operations_list
            node_selector = create_node_selector_window()

    if user_data is None:
        file_dialog = FileDialog(show_dir_size=False, modal=False, allow_drag=False,
                                 show_hidden_files=False, multi_selection=False, tag='file_dialog',
                                 default_path=last_visited_directory, dirs_only=True, callback=on_folder_select)
        file_dialog.show_file_dialog()
    else:
        on_folder_select(user_data)


def view_operations_repos():
    pass


def on_drag(sender, data, user_data):
    """
    When mouse is dragged and a node is selected then update that node's coordinates
    When mouse is dragged on the canvas with no node selected then move all nodes by the mouse movement and
    update their coordinates
    :param sender: Not used (the editor window)
    :param data: The mouse drag amount in x and y
    :param user_data: Not used
    :return: Nothing
    """
    global panel_coordinates
    global mouse_dragging_deltas
    global node_editor
    global node_editor_window

    data = np.array(data)

    # If resizing the node_editor_window then resize the node_editor itself
    height = dpg.get_item_height(node_editor_window)
    width = dpg.get_item_width(node_editor_window)
    dpg.set_item_height(node_editor, height - 40)
    dpg.set_item_width(node_editor, width - 20)

    # If moving a selected node, update the node's stores coordinates
    if np.sum(np.abs(data)) > 0 and len(nodes_list) > 0:
        for sel in dpg.get_selected_nodes(node_editor=node_editor):
            for n in nodes_list:
                if n.id == sel:
                    n.coordinates = dpg.get_item_pos(sel)

    # If dragging on the canvas with Ctrl pressed then move all nodes and update their stored coordinates
    if len(dpg.get_selected_nodes(node_editor=node_editor)) == 0 and dpg.is_key_down(17):
        move = [data[1] - mouse_dragging_deltas[0], data[2] - mouse_dragging_deltas[1]]
        panel_coordinates = [0, 0]
        panel_coordinates[0] = panel_coordinates[0] + move[0]
        panel_coordinates[1] = panel_coordinates[1] + move[1]
        mouse_dragging_deltas = [data[1], data[2]]

        for n in nodes_list:
            dpg.set_item_pos(n.id, [n.coordinates[0] + int(move[0]), n.coordinates[1] + int(move[1])])
            n.coordinates = dpg.get_item_pos(n.id)


def on_mouse_release(sender, app_data, user_data):
    global mouse_dragging_deltas

    mouse_dragging_deltas = [0, 0]


def create_node_selector_window():
    global node_selector

    with dpg.child_window(pos=[5, 65], width=270, height=-1, parent='main_window', no_scrollbar=True) \
            as node_selector_holder:
        title = dpg.add_text(default_value='Node Tree', indent=75)
        dpg.add_separator()

        with dpg.child_window(label='Node Selector', height=-1, parent=node_selector_holder) \
                as node_selector:
            # Create the window of the Node selector
            node_tree = generate_node_tree()
            base_id = node_tree[0][0]
            base_name = node_tree[0][1]
            with dpg.tree_node(parent=node_selector, default_open=True, id=base_id, open_on_arrow=True,
                               selectable=False, bullet=True, pos=[-20, -20]):

                # Read what *_com files exist in the Heron/Operations dir and sub dirs and create the correct
                # tree_node widget
                for parent_id, parent, node_id, node in node_tree:
                    with dpg.tree_node(label=node, parent=parent_id, default_open=True, id=node_id, bullet=True):
                        for op in operations_list:
                            if node == op.parent_dir:
                                colour = gu.choose_color_according_to_operations_type(node)
                                button = dpg.add_selectable(label=op.name, width=200, height=30, indent=10,
                                                            callback=on_add_node)
                                with dpg.theme() as theme_id:
                                    with dpg.theme_component(0):
                                        dpg.add_theme_color(dpg.mvThemeCol_Text, colour, category=dpg.mvThemeCat_Core)
                                        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)

                                dpg.bind_item_theme(button, theme_id)

    with dpg.theme() as node_selector_theme_id:
        with dpg.theme_component(0):
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 0, category=dpg.mvThemeCat_Core)
    dpg.bind_item_theme(node_selector, node_selector_theme_id)

    dpg.bind_item_font(title, 'bold_font_large')

    return node_selector


def known_hosts_file_setup_check():
    """
    On launch checks if there is a known_hosts file where it is expected to be. If not it gives the user the option
    to either create a new empty one where it is expected or choose another one.
    :return: Nothing
    """
    known_hosts_file_path = settings.settings_dict['Operation']['KNOWN_HOSTS_FILE']
    if known_hosts_file_path == '/.ssh/known_hosts':
        known_hosts_file_path = os.path.expanduser('~') + known_hosts_file_path
        settings.settings_dict['Operation']['KNOWN_HOSTS_FILE'] = known_hosts_file_path
        settings.save_settings()

    def on_press_known_hosts_buttons(sender, app_data, user_data):
        dpg.delete_item('known_hosts_window')
        if user_data:
            with open(known_hosts_file_path, 'w') as f:
                f.write('')
        else:
            def on_file_dialog_return(selected_files):
                knownhost_filepath = selected_files[0]
                settings.settings_dict['Operation']['KNOWN_HOSTS_FILE'] = knownhost_filepath
                settings.save_settings()
                dpg.delete_item('known_hosts_window')

            file_dialog = FileDialog(show_dir_size=False, modal=False, allow_drag=False,
                                     show_hidden_files=True, multi_selection=False, tag='file_dialog',
                                     default_path=last_visited_directory, dirs_only=False,
                                     callback=on_file_dialog_return)
            file_dialog.show_file_dialog()

    try:
        with open(known_hosts_file_path):
            pass
    except FileNotFoundError:
        with dpg.window(label='WARNING: SSH known_hosts file not found!', tag='known_hosts_window', width=500, height=200,
                        pos=[500, 200]):
            dpg.add_text('No known_hosts file {} \n has been found.\n '.format(known_hosts_file_path) +
                         'Either create a new empty known_hosts file in this folder\n'
                         'or select another file.')

            dpg.add_spacer(height=20)
            dpg.add_separator()
            dpg.add_spacer(height=20)

            with dpg.group(horizontal=True, indent=30):
                dpg.add_button(label='Add empty known_hosts file', user_data=True, callback=on_press_known_hosts_buttons)
                dpg.add_button(label='Select a known_hosts file', user_data=False, callback=on_press_known_hosts_buttons)


def graphically_create_new_node(sender, data):
    create_new_node.start(add_new_symbolic_link_node_folder)


def run(load_json_file=None):
    global node_editor
    global start_graph_button_id
    global end_graph_button_id
    global node_editor_window
    global file_dialog
    global italic_font

    dpg.create_context()
    dpg.create_viewport(title='Heron', width=1620, height=1000, x_pos=350, y_pos=0)

    with dpg.font_registry():
        default_font = dpg.add_font(os.path.join(heron_path, 'resources', 'fonts', 'SFProText-Regular.ttf'), 18)
        italic_font = dpg.add_font(os.path.join(heron_path, 'resources', 'fonts', 'SFProText-LightItalic.ttf'), 18)
        bold_font_large = dpg.add_font(os.path.join(heron_path, 'resources', 'fonts', 'SFProText-Semibold.ttf'), 22,
                                       tag='bold_font_large')

    dpg.bind_font(default_font)
    create_new_node.italic_font = italic_font

    with dpg.theme() as main_theme_id:
        with dpg.theme_component(0):
            dpg.add_theme_color(dpg.mvNodeCol_GridBackground, [1, 48, 63, 0], category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_style(dpg.mvNodeStyleVar_PinCircleRadius, 8, category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 12, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 12, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 8, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_PopupBorderSize, 2, category=dpg.mvThemeCat_Core)

            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, [20, 20, 20, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, [20, 20, 20, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvNodeCol_Pin, [172, 124, 41, 255], category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_Link, [172, 124, 41, 255], category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_GridLine, [51, 51, 51, 255], category=dpg.mvThemeCat_Nodes)

    dpg.bind_theme(main_theme_id)

    with dpg.window(width=1620, height=1000, pos=[0, 0], tag='main_window') as main_window:
        dpg.set_primary_window(main_window, True)

        with dpg.group(horizontal=True):
            start_graph_button_id = dpg.add_button(label="Start Graph", width=125, height=30, callback=on_start_graph)
            end_graph_button_id = dpg.add_button(label="End Graph", width=125, height=30, callback=on_end_graph)
            dpg.bind_item_font(start_graph_button_id, bold_font_large)
            dpg.bind_item_font(end_graph_button_id, bold_font_large)
        update_control_graph_buttons(False)

        with dpg.menu_bar(label='Menu Bar'):
            with dpg.menu(label='File'):
                dpg.add_menu_item(label='New', callback=clear_editor)
                dpg.add_menu_item(label='Save', callback=save_graph)
                dpg.add_menu_item(label='Load', callback=load_graph)
            with dpg.menu(label='Edit') as menu:
                ssh_info_editor.set_parent_id(menu)
                dpg.add_menu_item(label='Edit IPs/ports', callback=ssh_info_editor.edit_ssh_info)
                dpg.add_menu_item(label='Settings', callback=settings.start)
            with dpg.menu(label='Nodes'):
                dpg.add_menu_item(label='Add new Operations Folder (as Symbolic Link from Existing Repo)',
                                  callback=add_new_symbolic_link_node_folder, user_data=None)
                dpg.add_menu_item(label='Download Nodes from the Heron-Repositories page',
                                  callback=view_operations_repos)
                dpg.add_menu_item(label='Create new Node', callback=graphically_create_new_node)

    _ = create_node_selector_window()

    with dpg.child_window(parent=main_window,  width=-1, height=-1)as node_editor_window:
        editor_title = dpg.add_text(default_value='Editor')
        # The node editor
        with dpg.node_editor(label='Node Editor##Editor', callback=on_link, delink_callback=delete_link,
                             width=-1, height=-1, parent=node_editor_window, minimap=True,
                             minimap_location=dpg.mvNodeMiniMap_Location_BottomRight) as node_editor:
            dpg.set_item_pos(item=node_editor_window, pos=[275, 30])

        dpg.bind_item_font(editor_title, bold_font_large)

    # For Debugging purposes
    # dpg.show_debug()
    # dpg.show_logger()
    # dpg.show_documentation()
    # dpg.show_style_editor()
    # dpg.show_font_manager()

    # Button and mouse callback registers
    with dpg.handler_registry():
        dpg.add_key_press_handler(key=46, callback=on_del_pressed)
        dpg.add_mouse_drag_handler(callback=on_drag)
        dpg.add_mouse_release_handler(callback=on_mouse_release)

    #  At start the editor checks if the known_hosts file can be found and if not warns the user
    known_hosts_file_setup_check()

    # Start a thread that checks if a Node is to be deleted (when a user presses the Del button on the Node)
    test = threading.Thread(group=None, target=check_for_del_press_on_node)
    test.start()

    dpg.setup_dearpygui()
    dpg.show_viewport()

    if load_json_file is not None:
        do_the_loading_of_json_file(load_json_file)

    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    args = sys.argv
    json_file_to_load = None
    if len(args) > 1:
        json_file_to_load = args[1]

    run(load_json_file=json_file_to_load)
