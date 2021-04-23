

import zmq
from Heron.communication.socket_for_serialization import Socket
from Heron import constants as ct

# This is the context that the gui process should use.
GUI_CONTEXT = zmq.Context()

# This is the socket that sends to the state forwarder the state (parameters) of a worker. All Transform_com objects
# use the same object but send messages with different topics
SOCKET_PUB_STATE = Socket(GUI_CONTEXT, zmq.PUB)
SOCKET_PUB_STATE.connect(r"tcp://127.0.0.1:{}".format(ct.STATE_FORWARDER_SUBMIT_PORT))