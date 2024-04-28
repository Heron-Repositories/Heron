
import logging
import os
from pathlib import Path

heron_path = Path(os.path.dirname(os.path.realpath(__file__)))
logging.basicConfig(filename=os.path.join(heron_path, 'heron.log'), level=logging.ERROR,
                    format='%(asctime)s %(message)s', datefmt='%H:%M:%S')
logging.logThreads = False
logging.logProcesses = False
logging.logMultiprocessing = False
logging.logAsyncioTasks = False


DATA_FORWARDER_SUBMIT_PORT = '6560'
DATA_FORWARDER_PUBLISH_PORT = '6561'
DATA_FORWARDER_CAPTURE_PORT = '6562'

PARAMETERS_FORWARDER_SUBMIT_PORT = '6563'
PARAMETERS_FORWARDER_PUBLISH_PORT = '6564'
PARAMETERS_FORWARDER_CAPTURE_PORT = '6565'

HEARTBEAT_FORWARDER_SUBMIT_PORT = '6566'
HEARTBEAT_FORWARDER_PUBLISH_PORT = '6567'
HEARTBEAT_FORWARDER_CAPTURE_PORT = '6568'

PROOF_OF_LIFE_FORWARDER_SUBMIT_PORT = '6569'
PROOF_OF_LIFE_FORWARDER_PUBLISH_PORT = '6570'
PROOF_OF_LIFE_FORWARDER_CAPTURE_PORT = '6571'

MAXIMUM_RESERVED_SOCKETS_PER_NODE = 20

IGNORE = 'Ignore'

# Possible python executables. If some of your systems/environments use other executable for python add them to this list
PYTHON_EXES = ['python.exe ', 'python ', 'python3 ', 'py ']

# Moved to Settings
#HEARTBEAT_RATE = 1  # in seconds
#HEARTBEATS_TO_DEATH = 10
#NUMBER_OF_INITIAL_PARAMETERS_UPDATES = 20
#NUMBER_OF_ITTERATIONS_BEFORE_SAVENODESTATE_SUBSTATE_SAVE = 1000
#KNOWN_HOSTS_FILE = os.path.expanduser('~') + '/.ssh/known_hosts'
# Use this delay in order to allow multiple output, multiple links per output Nodes to function. 0.2ms is the smallest
# delay to allow any number of outputs and links to the next Node to function.
# For saving time and if there are no Nodes that have multiple outputs then set it to 0
#DELAY_BETWEEN_SENDING_DATA_TO_NEXT_NODE_MILLISECONDS = 0.2