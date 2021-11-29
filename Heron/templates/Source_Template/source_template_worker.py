
# This is the code of the worker part of the Source Operation. Here the user needs to write most of the code in
# order to define the Operation's functionality.

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
from Heron.gui.visualisation import Visualisation
from Heron import general_utils as gu
# </editor-fold>


# <editor-fold desc="Global variables if required. Global variables operate obviously within the scope of the process
# that is running when this script is called so they pose no existential threats and are very useful in keeping state
# over different calls of the work function (see below).">
need_parameters = True
running = False
global_var_1: str
global_var_2: str
global_var_3: float
global_var_4: int

# The following global is useful if you need a updatable visualisation window in the Node
vis: Visualisation
# </editor-fold>


# The Source Operation behaves differently to the Transform and the Sink as to how the work_function is called and how
# the parameters initialisation takes place. The Source Operation calls the work_function only one time (in contrast
# to the Sink and Transform cases where th work_function is called every time the Node receives an input).
# The Source's work_function has then to run in an infinite loop and generate the data of the Operation.

# The initialise function is called when the worker process is fired up from the com process and it keeps getting called
# as long as it is returning False. It gets passed the worker_object which carries the
# parameters from the GUI so it is used to initialise the parameters values in the worker process (and of course for
# any other initialisation required, eg. initialising a driver or starting a thread).
def initialise(worker_object):
    global vis

    global global_var_1
    global global_var_2
    global global_var_3
    global global_var_4

    # Put the initialisation of the Node's parameter's in a try loop to take care of the time it takes for the GUI to
    # update the SinkWorker object.
    try:
        parameters = worker_object.parameters
        global_var_1 = parameters[1]
        global_var_2 = parameters[2]
        global_var_3 = parameters[3]
        global_var_1 = parameters[4]
    except:
        return False

    # The following lines are required if you want visualisation from the Node itself. If this Node doesn't have its
    # own visualisation then you do not need the vis object.
    # If you do not change the Visualisation object's visualisation_loop then the Visualisation will assume the data is
    # an image and use cv2 to try and display it. For examples of different visualisations see the Visualiser Node's
    # worker script.
    global need_parameters
    vis = Visualisation(worker_object.node_name, worker_object.node_index)
    vis.visualisation_init()

    # Do other initialisation stuff
    return True


#  The worker_function of the Source Operation has access to the SourceWorker worker_object
def work_function(worker_object):
    global need_parameters
    global running
    global vis
    global global_var_1
    global global_var_2
    global global_var_3
    global global_var_4

    # You can check if the parameters have been grabbed from the Node's GUI
    while need_parameters:
        if worker_object.initialised:
            need_parameters = False
            running = True
            gu.accurate_delay(10)

    '''
    # You can get the Node's parameters without an initialisation_function since the Source work_function has access
    # to the SourceWorker object.
    while need_parameters:
        try:
            parameters = worker_object.parameters
            global_var_1 = parameters[1]
            global_var_2 = parameters[2]
            global_var_3 = parameters[3]
            global_var_1 = parameters[4]
            
            vis = Visualisation(worker_object.node_name, worker_object.node_index)
            vis.visualisation_init()
    
            need_parameters = False
            running = True
        except:
            gu.accurate_delay(10)
            return False
    '''

    # This is the required infinite loop. It needs to be able to stop when the on_end_of_life function is called, so
    # control it with a global variable
    while running:

        # Update any parameters that need updating during the running of the Graph
        vis.visualisation_on = worker_object.parameters[0]
        global_var_1 = worker_object.parameters[1]

        # Do stuff
        result = np.random.random((100, 100))

        # Send whatever needs to be visualised to the visualisation object
        vis.visualised_data = result

        # This line doesn't exist in the Transform and Sink work_functions but is required here because, in the Source
        # case it is the work_function that needs to push the data to the com process.
        worker_object.socket_push_data.send_array(result, copy=False)

        gu.accurate_delay(100)


def on_end_of_life():
    global running
    global vis

    vis.kill()
    running = False


if __name__ == "__main__":
    gu.start_the_source_worker_process(work_function, on_end_of_life, initialise)