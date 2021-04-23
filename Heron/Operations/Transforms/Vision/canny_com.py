
import os
import sys
from Heron.communication.transform_com import TransformCom
from dearpygui.simple import *
from dearpygui.core import *
Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new node's individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Canny'
NodeAttributeNames = ['Frame In', 'Edges Out']
NodeAttributeType = ['Input', 'Output']

"""
Parameters of the generated Node. All parameters need to be in a list. This is a single list that is send to the 
single worker function of the worker. It is possible that it is updated by widgets of multiple node attributes.
"""
arguments_list = [100, 200]  # [Min Value, Max Value]


def node_extras(attribute_name):
    """
    Extra GUI element under the attribute_name attribute of the generated Node.
    This function is called for all attributes in the node, so it needs a multiple if statement
    to deal with any attribute that needs extra elements
    :param attribute_name: The name of the attribute that is the parent of the element(s) added there
    :return: Nothing
    """
    global arguments_list
    # Set up int inputs under the Edges Out attribute to define the Min and Max values for the canny algorithm
    if NodeAttributeNames[1] in attribute_name:
        add_input_int('Min Value##{}'.format(attribute_name), default_value=arguments_list[0], callback=on_min_val_change)
        set_item_width('Min Value##{}'.format(attribute_name), width=100)
        add_input_int('Max Value##{}'.format(attribute_name), default_value=arguments_list[1], callback=on_max_val_change)
        set_item_width('Max Value##{}'.format(attribute_name), width=100)


def on_min_val_change(sender, data):
    """
    Callback that make the gui's publish state socket send the changed min value to the workers subscribe state socket
    :param sender: The sender widget that calls the callback
    :param data: not used
    :return: Nothing
    """
    global arguments_list
    arguments_list[0] = get_value(sender)
    topic = BaseName + sender.split(BaseName)[1]
    TransformCom.publish_parameters_to_worker(topic, arguments_list)


def on_max_val_change(sender, data):
    """
        Callback that make the gui's publish state socket send the changed max value to the workers subscribe state socket
        :param sender: The sender widget that calls the callback
        :param data: not used
        :return: Nothing
        """
    global arguments_list
    arguments_list[1] = get_value(sender)
    topic = BaseName + sender.split(BaseName)[1]
    TransformCom.publish_parameters_to_worker(topic, arguments_list)

# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
def start_the_communications_process():
    """
    Creates a TransformCom object for the Canny transformation
    (i.e. initialises the canny_worker process and keeps the zmq communication between the worker
    and the forwarder)
    The pull_port is the port that the canny_com uses to pull data from the canny_worker
    The push_port is the port that the canny_com uses to push data to the canny_worker.
    It is called as a separate process.
    :return: Nothing (continuous loop)
    """
    global Exec
    global arguments_list

    args = sys.argv[1:]
    assert len(args) == 5, 'There should be 5 arguments passed to the Canny process.' \
                           'The sending_topic, the receiving_topic, the state_topic, the push_port and the pull_port'
    push_port = args[0]
    pull_port = args[1]
    receiving_topic = args[2]
    sending_topic = args[3]
    state_topic = args[4]

    worker_exec = os.path.join(os.path.dirname(Exec), 'canny_worker.py')

    canny_com = TransformCom(sending_topic=sending_topic, receiving_topic=receiving_topic, state_topic=state_topic,
                             push_port=push_port, pull_port=pull_port, worker_exec=worker_exec, verbose=False)
    canny_com.connect_sockets()
    canny_com.start_worker(arguments_list)
    canny_com.start_ioloop()


if __name__ == "__main__":
    start_the_communications_process()

# </editor-fold>
