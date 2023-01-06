
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
import serial
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
# </editor-fold>

# <editor-fold desc="Global variables if required. Global variables operate obviously within the scope of the process
# that is running when this script is called so they pose no existential threats and are very useful in keeping state
# over different calls of the work function (see below).">
com_port: str
baud_rate: int
vis: bool

arduino_serial: serial.Serial

# </editor-fold>


def initialise(_worker_object):
    global arduino_serial
    global vis

    try:
        parameters = _worker_object.parameters
        vis = parameters[0]
        com_port = parameters[1]
        baud_rate = parameters[2]

    except:
        return False

    try:
        arduino_serial = serial.Serial(port=com_port, baudrate=baud_rate, write_timeout=1)
    except Exception as e:
        print(e)

    return True


def work_function(data, parameters):
    global vis
    global arduino_serial

    try:
        vis = parameters[0]
    except:
        pass

    topic = data[0]

    message = data[1:]
    message = Socket.reconstruct_data_from_bytes_message(message)[0]

    if vis:
        print(message)

    try:
        arduino_serial.write(message.encode('utf-8'))
    except Exception as e:
        print(e)


def on_end_of_life():
    global arduino_serial
    arduino_serial.reset_input_buffer()
    arduino_serial.close()


# This needs to exist. The worker_function and the end_of_life function must be defined and passed. The initialisation_
# function is optional.
if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(work_function=work_function,
                                                     end_of_life_function=on_end_of_life,
                                                     initialisation_function=initialise)
    worker_object.start_ioloop()