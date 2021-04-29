

import os
import sys
from Heron import general_utils as gu
from Heron.communication.transform_com import TransformCom
Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new node's individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Differencing'
NodeAttributeNames = ['Parameters', 'Frame 1 In', 'Frame 2 In', 'Difference Out']
NodeAttributeType = ['Static', 'Input', 'Input', 'Output']
ParameterNames = ['Time Offset']
ParameterTypes = ['int']
ParametersDefaultValues = [0]

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

    push_port, receiving_topics, sending_topics, state_topic = gu.parse_arguments_to_com(sys.argv)

    worker_exec = os.path.join(os.path.dirname(Exec), 'differencing_worker.py')

    differencing_com = TransformCom(sending_topics=sending_topics, receiving_topics=receiving_topics,
                                    state_topic=state_topic, push_port=push_port, worker_exec=worker_exec, verbose=False)
    differencing_com.connect_sockets()
    differencing_com.start_heartbeat_thread()
    differencing_com.start_worker()
    differencing_com.start_ioloop()


if __name__ == "__main__":
    start_the_communications_process()


# </editor-fold>