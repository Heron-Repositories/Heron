
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
import zmq
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
# </editor-fold>

# <editor-fold desc="Global variables.
unity_socket: zmq.Socket
monitors: str
sprites: dict
rotation: bool
opacity: int
screen_colour: int
main_screen_x_size = 2561 + 1280
sprite_screens_x_size = 1980

# </editor-fold>


def initialise(_worker_object):
    global monitors
    global rotation
    global opacity
    global pg_thread_running
    global unity_socket

    try:
        parameters = _worker_object.parameters
        monitors = parameters[0]
        rotation = parameters[1]
        opacity = parameters[2]
    except Exception as e:
        print(e)
        return False

    try:
        context = zmq.Context()
        unity_socket = context.socket(zmq.PUB)
        unity_socket.bind("tcp://*:12346")
    except Exception as e:
        print(e)
        return False

    return True


def work_function(data, parameters):


    topic = data[0]

    message_in = data[1:]
    message_in = Socket.reconstruct_array_from_bytes_message(message_in)[0]

    '''
    # Create message out to send to Unity
    print(message)
    socket.send_string(message)
    '''


# The on_end_of_life function must exist even if it is just a pass
def on_end_of_life():
    pass


# This needs to exist. The worker_function and the end_of_life function must be defined and passed. The initialisation_
# function is optional.
if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(work_function=work_function,
                                                     end_of_life_function=on_end_of_life,
                                                     initialisation_function=initialise)
    worker_object.start_ioloop()