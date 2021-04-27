
import os
import sys
import atexit
from Heron.communication.transform_com import TransformCom
from dearpygui.simple import *
from dearpygui.core import *
Exec = os.path.realpath(__file__)
import signal

# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new node's individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Canny'
NodeAttributeNames = ['Parameters', 'Frame In', 'Edges Out']
NodeAttributeType = ['Static', 'Input', 'Output']
ParameterNames = ['Min Value', 'Max Value']
ParameterTypes = ['int', 'int']
ParametersDefaultValues = [100, 200]

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
    global parameters_list

    args = sys.argv[1:]
    assert len(args) == 4, 'There should be 4 arguments passed to all Transform processes.' \
                            'The push port, the receiving topic, the sending topic and the state topic'
    push_port = args[0]
    receiving_topic = args[1]
    sending_topic = args[2]
    state_topic = args[3]

    worker_exec = os.path.join(os.path.dirname(Exec), 'canny_worker.py')

    canny_com = TransformCom(sending_topic=sending_topic, receiving_topic=receiving_topic, state_topic=state_topic,
                             push_port=push_port, worker_exec=worker_exec, verbose=False)
    canny_com.connect_sockets()
    canny_com.start_heartbeat_thread()
    canny_com.start_worker(None)
    canny_com.start_ioloop()


if __name__ == "__main__":
    start_the_communications_process()


# </editor-fold>
