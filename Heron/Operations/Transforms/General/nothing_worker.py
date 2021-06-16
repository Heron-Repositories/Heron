
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.Operations.Transforms.General import nothing_com
from Heron.communication.transform_worker import TransformWorker

worker_object: TransformWorker


def nothing(data, parameters):
    global worker_object

    try:
        worker_object.visualisation_on = parameters[0]
    except:
        worker_object.visualisation_on = nothing_com.ParametersDefaultValues[0]

    message = data[1:]  # data[0] is the topic
    worker_object.worker_result  = Socket.reconstruct_array_from_bytes_message_cv2correction(message)

    worker_object.visualisation_loop_init()

    return [worker_object.worker_result]


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(nothing, on_end_of_life)
    worker_object.start_ioloop()
