
import os
import sys
from Heron.communication.source_com import SourceCom
from dearpygui.simple import *
from dearpygui.core import *
Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new nodes individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Spinnaker Camera'
NodeAttributeNames = ['Frame Out']
NodeAttributeType = ['Output']

"""
Parameters of the generated Node. All parameters need to be in a list. This is a single list that is send to the 
single worker function of the worker. It is possible that it is updated by widgets of multiple node attributes.
"""
arguments_list = [0]  # [Camera Index]


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
    if NodeAttributeNames[0] in attribute_name:
        add_input_int('Camera Index##{}'.format(attribute_name), default_value=arguments_list[0],
                      callback=on_cam_index_change)
        set_item_width('Camera Index##{}'.format(attribute_name), width=100)


def on_cam_index_change(sender, data):
    """
    Callback that make the gui's publish state socket send the changed min value to the workers subscribe state socket
    :param sender: The sender widget that calls the callback
    :param data: not used
    :return: Nothing
    """
    global arguments_list
    arguments_list[0] = get_value(sender)
    topic = BaseName + sender.split(BaseName)[1]
    SourceCom.publish_parameters_to_worker(topic, arguments_list)

# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
def start_the_communications_process():
    """
    Creates a SourceCom object for a Spinnaker based camera
    (i.e. initialises the spinnaker_camera_worker process and keeps the zmq communication between the worker
    and the forwarders)
    :return: Nothing (continuous loop)
    """
    global Exec
    global arguments_list

    args = sys.argv[1:]
    assert len(args) == 3, 'There should be 3 arguments passed to the Spinnaker camera process. ' \
                           'The sending_topic, the state_topic and the push_port'
    push_port = args[0]
    sending_topic = args[1]
    state_topic = args[2]

    worker_exec = os.path.join(os.path.dirname(Exec), 'spinnaker_camera_worker.py')

    spin_camera_com = SourceCom(sending_topic=sending_topic, state_topic=state_topic, port=push_port,
                                worker_exec=worker_exec, verbose=False)

    spin_camera_com.connect_sockets()
    spin_camera_com.start_worker(arguments_list)
    spin_camera_com.start_ioloop()


if __name__ == "__main__":
    start_the_communications_process()