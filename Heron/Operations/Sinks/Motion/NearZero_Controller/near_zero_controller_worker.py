
import time
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.communication.sink_worker import SinkWorker
from Heron.Operations.Sinks.Motion.NearZero_Controller import near_zero_controller_com

worker_object: SinkWorker
need_parameters = True
use_pylibi2c = False
motor_controller = None
motor = None
pos_or_rot = None
value = None
current = None


def initialise_near_zero_controller(i2c_address):
    import pylibi2c
    motor_controller = pylibi2c.I2CDevice('/dev/i2c-1', i2c_address)
    motor_controller.delay = 10
    motor_controller.page_bytes = 16
    motor_controller.flags = pylibi2c.I2C_M_IGNORE_NAK

    return motor_controller


def move_motor(data, parameters):
    global worker_object
    global need_parameters
    global use_pylibi2c
    global motor_controller
    global motor
    global pos_or_rot
    global value
    global current

    start = time.perf_counter()
    try:
        use_pylibi2c = parameters[0]
        i2c_address = int(parameters[1], base=16)
        motor = parameters[2]
        pos_or_rot = parameters[3]
        value = parameters[4]
        current = parameters[5]
    except:
        use_pylibi2c = near_zero_controller_com.ParametersDefaultValues[0]
        i2c_address = int(near_zero_controller_com.ParametersDefaultValues[1], base=16)
        motor = near_zero_controller_com.ParametersDefaultValues[2]
        pos_or_rot = near_zero_controller_com.ParametersDefaultValues[3]
        value = near_zero_controller_com.ParametersDefaultValues[4]
        current = near_zero_controller_com.ParametersDefaultValues[5]
    if pos_or_rot == 'r':
        pos_or_rot = 'v'
    if use_pylibi2c:
        motor_controller = initialise_near_zero_controller(i2c_address)

    message = data[1:]  # data[0] is the topic
    message = Socket.reconstruct_array_from_bytes_message_cv2correction(message)[0]
    if int(message):
        command = '{}{}+{}c{}'.format(motor, pos_or_rot, value, current)
        if use_pylibi2c:
            motor_controller.write(0x0, command)
        print('Moving controller {} with command {}'.format(worker_object.node_index, command))

    end = time.perf_counter()
    #print('ooooTime of frame receive = {}, saved = {}, dif = {}'.format(start, end, end-start))


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(move_motor, on_end_of_life)
    worker_object.start_ioloop()
