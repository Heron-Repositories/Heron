
import sys
import cv2
import numpy as np
from Heron.communication.transform_worker import TransformWorker
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.Operations.Transforms.Vision import canny_com

worker_object = None


def canny(data, parameters):
    global worker_object

    try:
        worker_object.visualisation_on = parameters[0]
        min_val = parameters[0]
        max_val = parameters[1]
    except:
        worker_object.visualisation_on = canny_com.ParametersDefaultValues[0]
        min_val = canny_com.ParametersDefaultValues[1]
        max_val = canny_com.ParametersDefaultValues[2]

    message = data[1:]  # data[0] is the topic
    image = Socket.reconstruct_array_from_bytes_message_cv2correction(message)
    try:
        worker_object.worker_result = cv2.Canny(image, min_val, max_val)
    except:
        worker_object.worker_result = np.array((10, 10))
        print('Canny {} operation failed'.format(worker_object.index))

    worker_object.visualisation_toggle()

    return [worker_object.worker_result]


def on_end_of_life():
    pass


WORK_FUNCTION = canny
END_OF_LIFE_FUNCTION = on_end_of_life


def start_the_worker_process():
    """
    Starts the _worker process of the Transform that grabs data from the _com process, does something with them
    and sends them back to the _com process. It also grabs any updates of the parameters of the worker function
    The pull_port is the port that the worker uses to pull data from the _com process (the _com's push_port)
    The push_port is the port that the worker uses to push data to the _com process(the com's pull_port)
    The parameters_topic is the topic where the parameters (parameters of the worker function) will be received
    Verbose is the verbosity
    :return:
    """
    global worker_object

    pull_port, parameters_topic, receiving_topics, verbose = gu.parse_arguments_to_worker(sys.argv)
    verbose = verbose == 'True'

    buffer = {}
    for rt in receiving_topics:
        buffer[rt] = []

    worker_object = TransformWorker(recv_topics_buffer=buffer, pull_port=pull_port, work_function=WORK_FUNCTION,
                                    end_of_life_function=END_OF_LIFE_FUNCTION, parameters_topic=parameters_topic, verbose=verbose)
    worker_object.connect_sockets()

    worker_object.start_ioloop()


if __name__ == "__main__":
    start_the_worker_process()
