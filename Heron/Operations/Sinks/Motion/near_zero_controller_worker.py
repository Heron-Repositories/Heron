
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

worker_object: SinkWorker
need_parameters = True
use_pylibi2c = False
motor_controller = None
motor = None
pos_or_rot = None
value = None
current = None


def initialise_near_zero_controller(i2c_address):
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
    # Once the parameters are received at the starting of the graph then they cannot be updated any more.
    if need_parameters:
        try:
            use_pylibi2c = parameters[0]
            i2c_address = int(parameters[1], base=16)
            motor = parameters[2]
            pos_or_rot = parameters[3]
            if pos_or_rot == 'r':
                pos_or_rot == 'v'
            value = parameters[4]
            current = parameters[5]
            if use_pylibi2c:
                import pylibi2c
                motor_controller = initialise_near_zero_controller(i2c_address)

            need_parameters = False
        except:
            return
    if not need_parameters:
        message = data[1:]  # data[0] is the topic
        message = Socket.reconstruct_array_from_bytes_message_cv2correction(message)[0]
        if int(message):
            command = '{}{}+{}c{}'.format(motor, pos_or_rot, value, current)
            if use_pylibi2c:
                motor_controller.write(0x0, command)
            print('Moving with command {}'.format(command))

    end = time.perf_counter()
    #print('ooooTime of frame receive = {}, saved = {}, dif = {}'.format(start, end, end-start))


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(move_motor, on_end_of_life)
    worker_object.start_ioloop()
