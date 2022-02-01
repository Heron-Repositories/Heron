
# This is the code of the worker part of the Sink Operation. Here the user needs to write most of the code in order to
# define the Operation's functionality.

# <editor-fold desc="The following 6 lines of code are required to allow Heron to be able to see the Operation without
# package installation. Do not change.">
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
node_dir = current_dir
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))
# </editor-fold>

# <editor-fold desc="Extra imports if required">
import subprocess
import zmq
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
# </editor-fold>

# <editor-fold desc="Global variables.
unity_socket: zmq.Socket
unity_process: subprocess.Popen
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
    global unity_process

    try:
        parameters = _worker_object.parameters
        monitors = parameters[0]
        rotation = parameters[1]
        opacity = parameters[2]
    except Exception as e:
        print(e)
        return False

    try:
        unity_context = zmq.Context()
        unity_socket = unity_context.socket(zmq.PUB)
        unity_socket.bind("tcp://*:12346")
    except Exception as e:
        print(e)
        return False

    try:
        unity_exe = path.join(node_dir, '__Unity_TL_Task2_Screens_Project', 'Builds', 'TL_Task2_Screens_Unity.exe')
        unity_process = subprocess.Popen(unity_exe)

        screens_message_out = str('Screens:{}'.format(monitors))
        unity_socket.send_string(screens_message_out)
        movement_type_message_out = str('MovementType:{}'.format(rotation))
        unity_socket.send_string(movement_type_message_out)
    except Exception as e:
        print(e)
        return False

    return True


def work_function(data, parameters):
    global unity_socket

    topic = data[0]

    message_in = data[1:]
    message_in = Socket.reconstruct_array_from_bytes_message(message_in)[0]
    print(message_in)

    # Create message out to send to Unity
    message_out = 'Coordinates:{}'.format(message_in)
    unity_socket.send_string(message_out)


def on_end_of_life():
    global unity_process
    global unity_socket

    unity_process.kill()
    unity_socket.close(linger=1)


if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(work_function=work_function,
                                                     end_of_life_function=on_end_of_life,
                                                     initialisation_function=initialise)
    worker_object.start_ioloop()