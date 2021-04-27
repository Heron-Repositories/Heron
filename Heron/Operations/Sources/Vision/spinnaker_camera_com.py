
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
NodeAttributeNames = ['Parameters', 'Frame Out']
NodeAttributeType = ['Static', 'Output']
ParameterNames = ['Cam Index']
ParameterTypes = ['int']
ParametersDefaultValues = [0]

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
    global parameters_list

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
    spin_camera_com.start_heartbeat_thread()
    spin_camera_com.start_worker_process(None)
    spin_camera_com.start_ioloop()


if __name__ == "__main__":
    start_the_communications_process()