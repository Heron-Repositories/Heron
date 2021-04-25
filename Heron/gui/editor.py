
import time
import subprocess
import os
from pathlib import Path
import atexit
import numpy as np
from Heron.general_utils import kill_child, choose_color_according_to_operations_type
from Heron.gui import operations_list as op
from Heron.gui.node import Node
from Heron import constants as ct
from dearpygui import simple
from dearpygui.core import *
import default_style

operations_list = op.operations_list  # This generates all of the Operation dataclass instances currently
# in the Heron/Operations directory
heron_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
last_used_port = 5999
nodes_list = []
forwarders_list = []


def generate_node_tree():
    """
    The function that looks into the Heron/Operations path and creates a list of tuples of
    directories where the first element in the tuple is a dir and the second is
    its parent dir. All names for the dirs are generated (using ## to separate the different
    parts of the name) in such a way that can be used by dearpygui (i.e. they are
    unique and the first part before the first ## - which is the one that shows on a widget - is
    descriptive of the dir or the file).
    So one tuple would be ('Transforms##Operations##', 'Vision##Transforms##Operations##') which
    would mean that a dir called Vision (with real name Vision##Transforms##Operations##) has as
    its parent dir a dir called Transforms (with real name Transforms##Operations##).
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


def on_add_node(sender, data):
    """
    The callback that creates a Heron.gui.node.Node in the node editor for the operation defined by the button
    calling the callback.
    :param sender: The button's name
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
    n.put_on_editor()
    n.starting_port = next(port_generator)
    nodes_list.append(n)


def on_link(sender, data):
    output_node = data[0].split('##')[-2] + '##' +data[0].split('##')[-1]
    input_node = data[1].split('##')[-2] + '##' + data[1].split('##')[-1]
    for n in nodes_list:
        if output_node == n.name:
            n.add_topic_out(data[0])
        if input_node == n.name:
            n.add_topic_in(data[0])


def on_delink():
    pass


def start_forwarder_processes(path_to_com):
    """
    This initialises the two processes that run the two forwarders connecting the data flow between com and worker
    processes and the state flow between the same processes
    :param path_to_com: The path that the two python files that define the processes are
    :return: Nothing
    """
    forwarder_for_data = subprocess.Popen(['python', os.path.join(path_to_com, 'forwarder_for_data.py')])
    # creationflags=subprocess.DETACHED_PROCESS)
    atexit.register(kill_child, forwarder_for_data.pid)

    forwarder_for_state = subprocess.Popen(['python', os.path.join(path_to_com, 'forwarder_for_state.py')])
    # creationflags=subprocess.DETACHED_PROCESS)
    atexit.register(kill_child, forwarder_for_state.pid)

    print('Main loop PID = {}'.format(os.getpid()))
    print('Forwarder for Data PID = {}'.format(forwarder_for_data.pid))
    print('Forwarder for State PID = {}'.format(forwarder_for_state.pid))

    forwarders_list.append(forwarder_for_data)
    forwarders_list.append(forwarder_for_state)


def get_links_dictionary():
    links = np.array(get_links("Node Editor##Editor"))
    links_dict = {}
    for l in range(len(links[:, 0])):
        out = links[l, 0]
        print(out)
        try:
            inputs = links_dict[out]
        except:
            inputs = []
        inputs.append(links[l, 1])
        links_dict[out] = inputs

    return links_dict


def get_operation_from_attribute_name(attr_name):
    op_name = attr_name.split('##')[1]
    for op in operations_list:
        if op.name == op_name:
            return op


def get_next_available_port_group():
    global last_used_port
    while True:
        yield str(last_used_port)
        last_used_port = last_used_port + 3


port_generator = get_next_available_port_group()


def on_start_graph(sender, data):
    """
    The callback of the Start Graph button. It reads all the connections between the nodes and starts all the
    required processes assigning the correct topics and ports to each one of them so that the resulting
    communication between the processes resembles the node graph in the editor.
    :param sender: Not used
    :param data: Not used
    :return: Nothing
    """
    global graph_running

    if nodes_list:

        path_to_com = Path(os.path.dirname(os.path.realpath(__file__)))
        path_to_com = os.path.join(path_to_com.parent, 'communication')

        start_forwarder_processes(path_to_com)

        for n in nodes_list:
            n.start_exec()

        update_control_graph_buttons(True)


def on_end_graph(sender, data):
    global graph_running

    for n in nodes_list:
        n.stop_exec()

    for forwarder in forwarders_list:
        forwarder.kill()

    time.sleep(ct.HEARTBEAT_RATE * 1.2)
    update_control_graph_buttons(False)


def update_control_graph_buttons(graph_running):
    if graph_running:
        configure_item('Start Graph', enabled=False)
        configure_item('End Graph', enabled=True)
    else:
        configure_item('Start Graph', enabled=True)
        configure_item('End Graph', enabled=False)


with simple.window("Main Window"):
    set_main_window_title("Heron")
    set_main_window_size(1700, 1000)
    set_main_window_pos(350, 0)
    # The Start Graph button that starts all processes
    add_button("Start Graph", callback=on_start_graph)
    add_same_line()
    add_button("End Graph", callback=on_end_graph)
    update_control_graph_buttons(False)

    with simple.window('Node Selector'):
        # Create the window of the Node selector
        simple.set_window_pos('Node Selector', 10, 50)
        simple.set_item_width('Node Selector', 300)
        simple.set_item_height('Node Selector', 900)

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
            simple.set_item_height('Node Editor', int(get_main_window_size()[1] - 50))
            simple.set_window_pos('Node Editor', 370, 0)
            #set_mouse_click_callback(on_right_click)

#simple.show_debug()
#simple.show_logger()
#simple.show_documentation()
#simple.show_style_editor()

default_style.set_style(heron_path)
start_dearpygui(primary_window="Main Window")
