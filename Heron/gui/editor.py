import platform
import signal
import time
import subprocess
import os
from os.path import dirname
from pathlib import Path
import numpy as np
import json
import copy
import sys

sys.path.insert(0, dirname(dirname(dirname(os.path.realpath(__file__)))))
import Heron.general_utils as gu
from Heron.gui import operations_list as op_list
from Heron.gui.node import Node
from Heron import constants as ct
from Heron.gui import ssh_info_editor
import dearpygui.dearpygui as dpg

operations_list = op_list.generate_operations_list() #operations_list  # This generates all of the Operation dataclass instances currently
# in the Heron/Operations directory

heron_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
last_used_port = 6050
nodes_list = []
links_dict = {}
panel_coordinates = [0, 0]
mouse_dragging_deltas = [0, 0]
forwarders: subprocess.Popen
node_selector: int
port_generator = gu.get_next_available_port_group(last_used_port, ct.MAXIMUM_RESERVED_SOCKETS_PER_NODE)

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
            if len(d[1]) > 1 and '__top__' not in d[1]:
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
    n.spawn_node_on_editor()
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
    to die. They need a ct.HEARTBEAT_RATE * ct.HEARTBEATS_TO_DEATH seconds to die.
    :param sender: Not used
    :param data: Not used
    :return: Nothing
    """
    global forwarders

    for n in nodes_list:
        n.stop_com_process()

    if platform.system() == 'Windows':
        forwarders.send_signal(signal.CTRL_BREAK_EVENT)
    elif platform.system() == 'Linux':
        forwarders.terminate()

    with dpg.window(label='Progress bar', pos=[500, 400], width=400, height=80) as progress_bar:
        killing_proc_bar = dpg.add_progress_bar(label='Killing processes', parent=progress_bar, width=400, height=40,
                                                overlay='Closing worker_exec processes')
        t = 0
        while t < ct.HEARTBEAT_RATE * ct.HEARTBEATS_TO_DEATH:
            dpg.set_value(killing_proc_bar, t / (ct.HEARTBEAT_RATE * ct.HEARTBEATS_TO_DEATH))
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

    for i in indices_to_remove:
        node = nodes_list[i]
        for link in node.links_list:
            delete_link(None, link)
        nodes_list[i].remove_from_editor()
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


def save_graph():
    """
    Saves the current graph
    :return: Nothing
    """

    def on_file_select(sender, app_data, user_data):
        global links_dict

        def removekey(d, key):
            r = copy.deepcopy(d)
            del r[key]
            return r

        save_to = app_data['file_path_name']
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

        try:
            node_dict = removekey(node_dict, 'links')
        except:
            pass

        node_dict['links'] = links_dict

        with open(save_to, 'w+') as file:
            json.dump(node_dict, file, indent=4)

    file_dialog = dpg.add_file_dialog(callback=on_file_select, height=500)
    dpg.add_file_extension(".json", color=[255, 255, 255, 255], parent=file_dialog)


def get_attribute_id_from_label(label):
    global node_editor

    all_editors_children = dpg.get_item_children(node_editor, 1)
    for node_id in all_editors_children:
        all_nodes_childern = dpg.get_item_children(node_id, slot=1)
        for child_id in all_nodes_childern:
            child_label = dpg.get_item_label(child_id)
            if child_label == label:
                return child_id


def do_the_loading_of_json_file(sender, app_data, user_data):
    global nodes_list
    global last_used_port
    global port_generator
    global links_dict
    global node_editor

    load_file = app_data['file_path_name']

    with open(load_file, 'r') as file:
        raw_dict = json.load(file)
        nodes_list = []

        for key in raw_dict.keys():
            if key != 'links':
                value = raw_dict[key]
                n = Node(name=value['name'], parent=node_editor)
                op_dict = value['operation']
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
                n.spawn_node_on_editor()

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
                        #dpg.add_node_link(l1, l2, parent=node_editor)

    last_used_port = last_used_port + ct.MAXIMUM_RESERVED_SOCKETS_PER_NODE
    port_generator = gu.get_next_available_port_group(last_used_port, ct.MAXIMUM_RESERVED_SOCKETS_PER_NODE)


def load_graph():
    """
    Loads a saved graph
    :return: Nothing
    """

    clear_editor()

    file_dialog = dpg.add_file_dialog(callback=do_the_loading_of_json_file, directory_selector=False, height=500)
    dpg.add_file_extension(".json", color=[255, 255, 255, 255], parent=file_dialog)


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


def add_new_symbolic_link_node_folder():

    def delete_error_popup_aliases():
        if dpg.does_alias_exist('modal_error_id'):
            dpg.delete_item('modal_error_id')
        if dpg.does_alias_exist("modal_id_credentials"):
            dpg.delete_item("modal_id_credentials")
            print('killed creds window')
        if dpg.does_alias_exist("modal_id_folders_not_found"):
            dpg.delete_item("modal_id_folders_not_found")
            print('killed wrong folder window')

    delete_error_popup_aliases()

    def on_folder_select(sender, app_data, user_data):
        global node_selector
        global operations_list

        main_folders = ['Sources', 'Transforms', 'Sinks']
        operations_directory = app_data['file_path_name']

        def create_error_window(error_text, spacer):
            with dpg.window(label="Error Window", modal=True, show=True, id="modal_error_id",
                            no_title_bar=True, popup=True):
                dpg.add_text(error_text)
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=spacer)
                    dpg.add_button(label="OK", width=75, callback=delete_error_popup_aliases)

        def add_symlink(target, link):
            result = True
            try:
                os.symlink(target, link)
            except Exception as e:
                if 'privilege' in str(e):
                    error_text = 'If you are running Windows you need to run the python that runs Heron\n' \
                                 'with elevated credentials in order to create a symbolic link.\n' \
                                 'Restart Heron with a python that has started with "Run as Administrator".'
                    spacer = 160
                elif 'Cannot create a file when that file already exists' in str(e):
                    error_text = 'You are trying to add a set of Nodes that already exist.'
                    spacer = 130
                else:
                    error_text = str(e)
                    spacer = 300
                create_error_window(error_text, spacer)
                result = False

            return result

        folders_exist = False
        for f in main_folders:
            if os.path.isdir(os.path.join(operations_directory, f)):
                folders_exist = True
                for d in os.listdir(os.path.join(operations_directory, f)):
                    target = os.path.join(operations_directory, f, d)
                    link = os.path.join(heron_path, 'Operations', f, d)
                    if not os.path.isdir(link):
                        if not add_symlink(target, link):
                            return
                    else:
                        for inner_dir in os.listdir(target):
                            link_inner = os.path.join(link, inner_dir)
                            inner_target = os.path.join(target, inner_dir)
                            if not add_symlink(inner_target, link_inner):
                                return

        if not folders_exist:
            error_text = "The selected Directory {} \n" \
                         "doesn't have at least one of the\n" \
                         "Sources, Transforms or Sinks folders in it, so it cannot\n" \
                         "be a Heron Node code. Please select another directory.".format(operations_directory)
            create_error_window(error_text, 120)
        else:
            dpg.delete_item(node_selector)
            operations_list = op_list.generate_operations_list()
            Node.operations_list = operations_list
            node_selector = create_node_selector_window()

    file_dialog = dpg.add_file_dialog(callback=on_folder_select, directory_selector=True, height=500)


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

    with dpg.window(label='Node Selector', pos=[10, 60], width=300, height=890) as node_selector:
        # Create the window of the Node selector

        node_tree = generate_node_tree()
        base_id = node_tree[0][0]
        base_name = node_tree[0][1]
        with dpg.tree_node(label=base_name, parent=node_selector, default_open=True, id=base_id, open_on_arrow=True):

            # Read what *_com files exist in the Heron/Operations dir and sub dirs and create the correct
            # tree_node widget
            for parent_id, parent, node_id, node in node_tree:
                with dpg.tree_node(label=node, parent=parent_id, default_open=True, id=node_id):
                    for op in operations_list:
                        if node == op.parent_dir:
                            colour = gu.choose_color_according_to_operations_type(node)
                            button = dpg.add_button(label=op.name, width=200, height=30, callback=on_add_node)
                            with dpg.theme() as theme_id:
                                with dpg.theme_component(0):
                                    dpg.add_theme_color(dpg.mvThemeCol_Button, colour, category=dpg.mvThemeCat_Core)
                                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)

                            dpg.bind_item_theme(button, theme_id)
        return node_selector


def run(load_json_file=None):
    global node_editor
    global start_graph_button_id
    global end_graph_button_id
    global node_editor_window

    dpg.create_context()
    dpg.create_viewport(title='Heron', width=1620, height=1000, x_pos=350, y_pos=0)

    with dpg.font_registry():
        # add font (set as default for entire app)
        default_font = dpg.add_font(os.path.join(heron_path, 'resources', 'fonts', 'SF-Pro-Rounded-Regular.ttf'), 18)

    with dpg.window(width=1620, height=1000, pos=[0, 0]) as main_window:
        dpg.set_primary_window(main_window, True)
        # The Start Graph button that starts all processes
        with dpg.group(horizontal=True):
            start_graph_button_id = dpg.add_button(label="Start Graph", callback=on_start_graph)
            end_graph_button_id = dpg.add_button(label="End Graph", callback=on_end_graph)
        update_control_graph_buttons(False)

        dpg.bind_font(default_font)

        with dpg.menu_bar(label='Menu Bar'):
            with dpg.menu(label='File'):
                dpg.add_menu_item(label='New', callback=clear_editor)
                dpg.add_menu_item(label='Save', callback=save_graph)
                dpg.add_menu_item(label='Load', callback=load_graph)
            with dpg.menu(label='Local Network') as menu:
                ssh_info_editor.set_parent_id(menu)
                dpg.add_menu_item(label='Edit IPs/ports', callback=ssh_info_editor.edit_ssh_info)
            with dpg.menu(label='Operations'):
                dpg.add_menu_item(label='Add new Operations Folder (as Symbolic Link from Existing Repo)',
                                  callback=add_new_symbolic_link_node_folder)
                dpg.add_menu_item(label='Download Operations from the Heron-Repositories page',
                                  callback=view_operations_repos)

    _ = create_node_selector_window()

    with dpg.window(label="Node Editor", pos=[dpg.get_item_width(main_window) - 1000, 0], )as node_editor_window:
        # The node editor
        with dpg.node_editor(label='Node Editor##Editor', callback=on_link, delink_callback=delete_link,
                             width=1220, height=dpg.get_item_height(main_window) - 100) as node_editor:
            dpg.set_item_pos(item=node_editor_window, pos=[370, 30])

    # dpg.show_debug()
    # dpg.show_logger()
    # dpg.show_documentation()
    # dpg.show_style_editor()

    # Button and mouse callback registers
    with dpg.handler_registry():
        dpg.add_key_press_handler(key=46, callback=on_del_pressed)
        dpg.add_mouse_drag_handler(callback=on_drag)
        dpg.add_mouse_release_handler(callback=on_mouse_release)

    dpg.setup_dearpygui()
    dpg.show_viewport()

    if load_json_file is not None:
        app_data = {'file_path_name': load_json_file}
        do_the_loading_of_json_file(sender=None, app_data=app_data, user_data=None)

    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    args = sys.argv
    json_file_to_load = None
    if len(args) > 1:
        json_file_to_load = args[1]

    run(load_json_file=json_file_to_load)
