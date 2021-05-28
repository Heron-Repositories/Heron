

import zmq
from Heron.communication.socket_for_serialization import Socket
from Heron import constants as ct

# This is the context that the gui process should use.
GUI_CONTEXT = zmq.Context()

# This is the socket that sends to the parameters forwarder the parameters (parameters) of a worker_exec. All Transform_com objects
# use the same object but send messages with different topics
SOCKET_PUB_PARAMETERS = Socket(GUI_CONTEXT, zmq.PUB)
SOCKET_PUB_PARAMETERS.connect(r"tcp://127.0.0.1:{}".format(ct.PARAMETERS_FORWARDER_SUBMIT_PORT))
#SOCKET_PUB_PARAMETERS.set_hwm(1)

SOCKET_SUB_PROOF_OF_LIFE = GUI_CONTEXT.socket(zmq.SUB)
SOCKET_SUB_PROOF_OF_LIFE.connect(r"tcp://127.0.0.1:{}".format(ct.PROOF_OF_LIFE_FORWARDER_PUBLISH_PORT))
SOCKET_SUB_PROOF_OF_LIFE.subscribe("")