
import time
import subprocess
import os
from pathlib import Path
import atexit
import numpy as np
import json
import copy
import sys
sys.path.insert(0, '../../')
from Heron.general_utils import kill_child, choose_color_according_to_operations_type, get_next_available_port_group
from Heron.gui import operations_list as op_list
from Heron.gui.node import Node
from Heron import constants as ct
from Heron.gui import ssh_info_editor
from dearpygui import simple
from dearpygui.core import *
import default_style

operations_list = op_list.operations_list  # This generates all of the Operation dataclass instances currently
# in the Heron/Operations directory
heron_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
last_used_port = 6000
nodes_list = []
panel_coordinates = [0, 0]
forwarders: subprocess.Popen


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
    its parent dir a dir called Transforms (with real node_name Transforms##Operations##).
    The returned list can be used in a tree_node widget
    :return: The list of tuples (parent dir, dir)
    """
    path_to_nodes = os.path.join(heron_path, 'Operations')
    node_dirs = []
    for d in os.walk(path_to_nodes):
        if len(d[1]) > 0 and '__pycache__' not in d[1]:
            temp = d[0].split('\\')
            i = -1
            parent = ''
            while temp[i] != 'Heron':
                parent = parent + temp[i] + '##'
                i = i - 1
            for dir in d[1]:
                dir_name = dir + '##' + parent
                node_dirs.append((parent, dir_name))
    return node_dirs


port_generator = get_next_available_port_group(last_used_port, ct.MAXIMUM_RESERVED_SOCKETS_PER_NODE)


def on_add_node(sender, data):
    """
    The callback that creates a Heron.gui.node.Node in the node editor for the operation defined by the button
    calling the callback.
    :param sender: The button's node_name
    :param data: Not used
    :return: Nothing
    """
    # Get corresponding operation
    operation = None
    for op in operations_list:
        if op.name == sender:
            operation = op
            break

    # Find how many other nodes there are already on the editor for the same operation
    num_of_same_nodes = 0
    all_nodes = get_item_children("Node Editor##Editor")
    if all_nodes is not None:
        for n in all_nodes:
            if operation.name in n:
                num_of_same_nodes = num_of_same_nodes+1

    # Create the Node
    name = operation.name + '##{}'.format(num_of_same_nodes)
    n = Node(name=name)
    n.spawn_node_on_editor()
    n.starting_port = next(port_generator)
    nodes_list.append(n)


def on_link(sender, link):
    """
    When a link is created its out part is stored as a topic_out in the node with the output and as a topic_in in the
    node with the input
    :param sender: The node editor (not used)
    :param link: The link list
    :return: Nothing
    """
    output_node = link[0].split('##')[-2] + '##' + link[0].split('##')[-1]
    input_node = link[1].split('##')[-2] + '##' + link[1].split('##')[-1]
    for n in nodes_list:
        if output_node == n.name:
            n.add_topic_out(link[0])
        if input_node == n.name:
            n.add_topic_in(link[0])


# TODO: Define what happens when user deletes a link
def on_delink(sender, link):
    print(link)
    output_node = link[0].split('##')[-2] + '##' + link[0].split('##')[-1]
    input_node = link[1].split('##')[-2] + '##' + link[1].split('##')[-1]
    for n in nodes_list:
        #print(n.name)
        #print(n.topics_in)
        #print(n.topics_out)
        #print('-------')
        if output_node == n.name:
            n.remove_topic_out(link[0])
        if input_node == n.name:
            n.remove_topic_in(link[0])
        #print(n.topics_in)
        #print(n.topics_out)
        #print('-------')
        #print('-------')


def start_forwarders_process(path_to_com):
    """
    This initialises the two processes that run the two forwarders connecting the link flow between com and worker
    processes and the parameters flow between the same processes
    :param path_to_com: The path that the two python files that define the processes are
    :return: Nothing
    """
    global forwarders

    forwarders = subprocess.Popen(['python', os.path.join(path_to_com, 'forwarders.py'), 'False', 'False', 'False'])
    atexit.register(kill_child, forwarders.pid)

    print('Main loop PID = {}'.format(os.getpid()))
    print('Forwarders PID = {}'.format(forwarders.pid))


def get_links_dictionary():
    """
    Returns the links in dictionary form (the key is the out and the value is the list of all the ins connected to it)
    :return: The links dictionary
    """
    links = np.array(get_links("Node Editor##Editor"))
    links_dict = {}
    if len(links) > 0:
        for l in range(len(links[:, 0])):
            out = links[l, 0]
            try:
                inputs = links_dict[out]
            except:
                inputs = []
            inputs.append(links[l, 1])
            links_dict[out] = inputs

    return links_dict


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

    forwarders.kill()

    with simple.window('Progress bar', x_pos=500, y_pos=400, width=400, height=80):
        add_progress_bar('Killing processes', parent='Progress bar', width=400, height=40,
                         overlay='Closing worker processes')
        t = 0
        while t < ct.HEARTBEAT_RATE * ct.HEARTBEATS_TO_DEATH:
            set_value('Killing processes', t/(ct.HEARTBEAT_RATE * ct.HEARTBEATS_TO_DEATH))
            t = t + 0.1
            time.sleep(0.1)
        delete_item('Killing processes')
    update_control_graph_buttons(False)
    delete_item('Progress bar')


def on_keys_pressed(sender, key_value):
    if key_value == 46:  # Pressed the Delete key
        indices_to_remove = []
        for node in get_selected_nodes("Node Editor##Editor"):
            for i in np.arange(len(nodes_list)-1, -1, -1):
                if nodes_list[i].name == node:
                    nodes_list[i].remove_from_editor()
                    indices_to_remove.append(i)
        for i in indices_to_remove:
            del nodes_list[i]

        for link in get_selected_links("Node Editor##Editor"):
            delete_node_link("Node Editor##Editor", link[0], link[1])


def update_control_graph_buttons(is_graph_running):
    """
    Used to enable and disable (grey out) the Start Graph or the End Graph according to whether the Graph is running or
    not
    :param is_graph_running: Is the graph running bool
    :return: Nothing
    """
    if is_graph_running:
        configure_item('Start Graph', enabled=False)
        configure_item('End Graph', enabled=True)
    else:
        configure_item('Start Graph', enabled=True)
        configure_item('End Graph', enabled=False)


def save_graph():
    """
    Saves the current graph
    :return: Nothing
    """
    def on_file_select(sender, data):
        save_to = os.path.join(data[0], data[1])
        node_dict = {}
        for n in nodes_list:
            n = copy.deepcopy(n)
            node_dict[n.name] = n.__dict__
            node_dict[n.name]['operation'] = node_dict[n.name]['operation'].__dict__

        node_dict['links'] = get_links_dictionary()
        with open(save_to, 'w+') as file:
            json.dump(node_dict, file)

    open_file_dialog(callback=on_file_select)


def load_graph():
    """
    Loads a saved graph
    :return: Nothing
    """
    clear_editor()

    def on_file_select(sender, data):
        global nodes_list
        load_file = os.path.join(data[0], data[1])
        
        with open(load_file, 'r') as file:
            raw_dict = json.load(file)
            nodes_list = []

            for key in raw_dict.keys():
                if key != 'links':
                    value = raw_dict[key]
                    n = Node(name=value['name'])
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
                    n.ssh_local_server = value['ssh_local_server']
                    n.ssh_remote_server = value['ssh_remote_server']
                    n.spawn_node_on_editor()

                    nodes_list.append(n)

                elif key == 'links':
                    links_dict = raw_dict[key]
                    for l1 in links_dict:
                        for l2 in links_dict[l1]:
                            add_node_link('Node Editor##Editor', l1, l2)
    
    open_file_dialog(callback=on_file_select)


# TODO: Add a UI asking the user if they are sure (and that all link will be lost)
def clear_editor():
    """
    Clear the editor of all nodes and links
    :return: Nothing
    """
    global nodes_list
    if get_item_children('Node Editor##Editor'):
        for n in get_item_children('Node Editor##Editor'):
            delete_item(n)
    if get_links('Node Editor##Editor'):
        for l in get_links('Node Editor##Editor'):
            delete_node_link('Node Editor##Editor', l[0], l[1])
    nodes_list = []


def on_drag(sender, data):
    """
    When mouse is dragged and a node is selected then update that node's coordinates
    When mouse is dragged on the canvas with no node selected then move all nodes by the mouse movement and
    update their coordinates
    :param sender: Not used (the editor window)
    :param data: The mouse drag amount in x and y
    :return: Nothing
    """
    global panel_coordinates
    data = np.array(data)

    # If moving a selected node, update the node's stores coordinates
    if np.sum(np.abs(data)) > 0 and len(nodes_list) > 0:
        for sel in get_selected_nodes('Node Editor##Editor'):
            for n in nodes_list:
                if n.name in sel:
                    n.coordinates = [get_item_configuration(sel)['x_pos'], get_item_configuration(sel)['y_pos']]

    # If dragging on the canvas with Ctrl pressed then move all nodes and update their stored coordinates
    if len(get_selected_nodes('Node Editor##Editor')) == 0 and is_key_down(17):
        panel_coordinates = [0, 0]
        panel_coordinates[0] = panel_coordinates[0] + data[1]
        panel_coordinates[1] = panel_coordinates[1] + data[2]
        for n in nodes_list:
            simple.set_window_pos(n.name, n.coordinates[0] + int(data[1]),
                                  n.coordinates[1] + int(data[2]))
            n.coordinates = [get_item_configuration(n.name)['x_pos'], get_item_configuration(n.name)['y_pos']]


with simple.window("Main Window"):
    set_main_window_title("Heron")
    set_main_window_size(1700, 1000)
    set_main_window_pos(350, 0)
    # The Start Graph button that starts all processes
    add_button("Start Graph", callback=on_start_graph)
    add_same_line()
    add_button("End Graph", callback=on_end_graph)
    update_control_graph_buttons(False)

    with simple.menu_bar('Menu Bar'):
        with simple.menu('File'):
            add_menu_item('New', callback=clear_editor)
            add_menu_item('Save', callback=save_graph)
            add_menu_item('Load', callback=load_graph)
        with simple.menu('SSH'):
            add_menu_item('Edit ssh info', callback=ssh_info_editor.edit_ssh_info)
            add_menu_item('Clear ssh info')

with simple.window('Node Selector'):
    # Create the window of the Node selector
    simple.set_window_pos('Node Selector', 10, 60)
    simple.set_item_width('Node Selector', 300)
    simple.set_item_height('Node Selector', 890)

    node_tree = generate_node_tree()
    base_name = node_tree[0][0]

    with simple.tree_node(base_name, default_open=True):
        # Read what *_com files exist in the Heron/Operations dir and sub dirs and create the correct
        # tree_node widget
        for parent, node in node_tree:
            with simple.tree_node(node, parent=parent, default_open=True):
                for op in operations_list:
                    if node == op.parent_dir:
                        colour = choose_color_according_to_operations_type(node)
                        add_button(op.name, width=150, height=30, callback=on_add_node)
                        set_item_color(op.name, style=mvGuiCol_Button, color=colour)

with simple.window("Node Editor", x_pos=int(get_main_window_size()[0]) - 1000, y_pos=0):
    # The node editor
    with simple.node_editor('Node Editor##Editor', link_callback=on_link, delink_callback=on_delink):

        simple.set_item_width('Node Editor', 1300)
        simple.set_item_height('Node Editor', int(get_main_window_size()[1] - 80))
        simple.set_window_pos('Node Editor', 370, 30)

#simple.show_debug()
#simple.show_logger()
#simple.show_documentation()
#simple.show_style_editor()

# Button and mouse callback registers
set_mouse_drag_callback(callback=on_drag, threshold=0.1)
set_key_press_callback(callback=on_keys_pressed)

default_style.set_style(heron_path)
start_dearpygui(primary_window="Main Window")
