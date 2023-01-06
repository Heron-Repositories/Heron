
# This is the code of the worker part of the Transform Operation. Here the user needs to write most of the code in
# order to define the Operation's functionality.

# <editor-fold desc="The following 6 lines of code are required to allow Heron to be able to see the Operation without
# package installation. Do not change.">
import sys
from os import path
import numpy as np

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))
# </editor-fold>

# <editor-fold desc="Extra imports if required">
import importlib as ilb
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu, constants as ct
# </editor-fold>

# <editor-fold desc="Global variables if required. Global variables operate obviously within the scope of the process
# that is running when this script is called so they pose no existential threats and are very useful in keeping state
# over different calls of the work function (see below).">
need_parameters = True
functions_path: str
function = None
# </editor-fold>


def initialise(worker_object):
    global need_parameters
    global functions_path
    global function

    try:
        parameters = worker_object.parameters
        functions_path = parameters[0]
        need_parameters = False

        functions_dir = path.dirname(path.abspath(functions_path))
        functions_name = path.basename(path.abspath(functions_path)).split('.')[0]
        sys.path.insert(0, functions_dir)
        module = ilb.import_module(functions_name)
        function = getattr(module, 'function')
    except:
        return False

    worker_object.savenodestate_create_parameters_df(functions_path=functions_path)

    return True


def work_function(data, parameters):
    global function

    topic = data[0].decode('utf-8')

    message = data[1:]  # data[0] is the topic
    input_data = Socket.reconstruct_data_from_bytes_message(message)

    result = function(topic, input_data)

    if type(result) == np.ndarray:
        result = [result]
    elif type(result) == list:
        if type(result[0]) == np.ndarray:
            return result
        else:
            result = [np.array(result)]
    else:
        result = [np.array([result])]

    return result


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(work_function=work_function,
                                                          end_of_life_function=on_end_of_life,
                                                          initialisation_function=initialise)
    worker_object.start_ioloop()
