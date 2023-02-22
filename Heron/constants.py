
import logging
import os
from pathlib import Path

heron_path = Path(os.path.dirname(os.path.realpath(__file__)))
logging.basicConfig(filename=os.path.join(heron_path, 'heron.log'), level=logging.DEBUG,
                    format='%(asctime)s %(message)s', datefmt='%H:%M:%S')


DATA_FORWARDER_SUBMIT_PORT = '5560'
DATA_FORWARDER_PUBLISH_PORT = '5561'
DATA_FORWARDER_CAPTURE_PORT = '5562'

PARAMETERS_FORWARDER_SUBMIT_PORT = '5563'
PARAMETERS_FORWARDER_PUBLISH_PORT = '5564'
PARAMETERS_FORWARDER_CAPTURE_PORT = '5565'

HEARTBEAT_FORWARDER_SUBMIT_PORT = '5566'
HEARTBEAT_FORWARDER_PUBLISH_PORT = '5567'
HEARTBEAT_FORWARDER_CAPTURE_PORT = '5568'

PROOF_OF_LIFE_FORWARDER_SUBMIT_PORT = '5569'
PROOF_OF_LIFE_FORWARDER_PUBLISH_PORT = '5570'
PROOF_OF_LIFE_FORWARDER_CAPTURE_PORT = '5571'

HEARTBEAT_RATE = 1  # in seconds
HEARTBEATS_TO_DEATH = 10

MAXIMUM_RESERVED_SOCKETS_PER_NODE = 20

NUMBER_OF_INITIAL_PARAMETERS_UPDATES = 20

IGNORE = 'Ignore'

NUMBER_OF_ITTERATIONS_BEFORE_SAVENODESTATE_SUBSTATE_SAVE = 1000

# Use this delay in order to allow multiple output, multiple links per output Nodes to function. 0.2ms is the smallest
# delay to allow any number of outputs and links to the next Node to function.
# For saving time and if there are no Nodes that have multiple outputs then set it to 0
DELAY_BETWEEN_SENDING_DATA_TO_NEXT_NODE_MILLISECONDS = 0.2


