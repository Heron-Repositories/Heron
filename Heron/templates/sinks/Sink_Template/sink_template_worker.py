
# This is the code of the worker part of the Sink Operation. Here the user needs to write most of the code in order to
# define the Operation's functionality.

# <editor-fold desc="The following 6 lines of code are required to allow Heron to be able to see the Operation without
# package installation. Do not change.">
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))
# </editor-fold>

# <editor-fold desc="Extra imports if required">
import numpy as np
from Heron.communication.socket_for_serialization import Socket
from Heron.communication.sink_worker import SinkWorker
from Heron import general_utils as gu
# </editor-fold>

# <editor-fold desc="Global variables if required. Global variables operate obviously within the scope of the process
# that is running when this script is called so they pose no existential threats and are very useful in keeping state
# over different calls of the work function (see below).">
need_parameters = True
global_var_1: str
global_var_2: str
global_var_3: float
global_var_4: int
# The following global is useful if you need a updatable visualisation window in the Node
vis: SinkWorker
# </editor-fold>

# The initialise function is called when the worker process is fired up from the com process and it gets called
# as long as it is returning False. It can read the worker_object which carries the parameters from the GUI so it is
# used to initialise the parameters values in the worker process (and of course for any other initialisation required,
# eg. initialising a driver or starting a thread).
def initialise(_worker_object):
    global global_var_1
    global global_var_2
    global global_var_3
    global global_var_4

    parameters = _worker_object.parameters

    try:
        # if the Node has a Visualisation parameter pass its value to _worker_object.visualisation_on
        _worker_object.visualisation_on = parameters[0]
        # if there is a visualisation then the _worker_object visualisation loop should be initialised
        _worker_object.visualisation_loop_update()

        global_var_1 = parameters[1]
        global_var_2 = parameters[2]
        global_var_3 = parameters[3]
        global_var_1 = parameters[4]

    except:
        return False

    # Do other initialisation stuff
    return True

# The worker function is called every time the com process receives a data packet (a numpy array) from the Node this
# Sink is connected to and passes it on to the worker process. The worker_function needs two parameters, the data and
# the Node's parameters.
# You can use the parameters parameter to get the Node's parameters during the first time the
# worker_function is called (if you do not use an initialisation function) and / or update the parameters during
# subsequent calls of the worker_function if you want to allow the user to update the Node's parameters while the
# Graph pipeline is running.
# The data is a list with two items. The first is the topic of the connection. If the Node has multiple Inputs then
# the topic will tell you which Input the data packet arrived from.
def worker_function(data, parameters):
    global need_parameters
    global global_var_1
    global global_var_2
    global global_var_3
    global global_var_4

    '''
    # This is a 2nd way to initialise the parameters if no initialisation function is used.
    if need_parameters:
        try:
            global_var_1 = parameters[1]
            global_var_2 = parameters[2]
            global_var_3 = parameters[3]
            global_var_1 = parameters[4]

            need_parameters = True
        except:
            pass
    
    else:
        # Do the rest of the code in here so that it doesn't run if the parameters are not set
    '''

    # If any parameters need to be updated during runtime then do that here, e.g.
    try:
        global_var_1 = parameters[1]

        # Also update the visualisation parameter (this allows to turn on and off the visualisation window during
        # run time
        _worker_object.visualisation_on = parameters[0]
    #
    topic = data[0]
    message = data[1:]
    message = Socket.reconstruct_array_from_bytes_message(message)[0]  # This is needed to reconstruct the message
    # that comes in into the numpy array that it is.

    # Now do stuff




def on_end_of_life():
    global need_parameters
    need_parameters = False

# This needs to exist. The worker_function and the end_of_life function must be defined and passed. The initialisation_
# function is optional.
if __name__ == "__main__":
    gu.start_the_source_worker_process(worker_function=worker_function,
                                       end_of_life_function=on_end_of_life,
                                       initialisation_function=initialise)