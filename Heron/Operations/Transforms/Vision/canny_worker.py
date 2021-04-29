
from Heron.communication.transform_worker import TransformWorker
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
import sys
import cv2
import numpy as np

buffer = {}


def canny(data, parameters):
    try:
        min_val = parameters[0]
        max_val = parameters[1]
        topic = data[0]
        message = data[1:]
        image = Socket.reconstruct_array_from_bytes_message_cv2correction(message)
        edges = cv2.Canny(image, min_val, max_val)
        cv2.namedWindow("Canny", cv2.WINDOW_NORMAL)
        cv2.imshow('Canny', edges)
        cv2.waitKey(1)
    except:
        edges = np.array([])
        print('Canny operation failed')

    return [edges]


WORK_FUNCTION = canny


def start_the_worker_process():
    """
    Starts the _worker process of the Transform that grabs data from the _com process, does something with them
    and sends them back to the _com process. It also grabs any updates of the parameters of the worker function
    The pull_port is the port that the worker uses to pull data from the _com process (the _com's push_port)
    The push_port is the port that the worker uses to push data to the _com process(the com's pull_port)
    The state_topic is the topic where the state (parameters of the worker function) will be received
    Verbose is the verbosity
    :return:
    """
    global buffer

    pull_port, state_topic, receiving_topics, verbose = gu.parse_arguments_to_worker(sys.argv)
    verbose = verbose == 'True'
    for rt in receiving_topics:
        buffer[rt] = []

    worker = TransformWorker(pull_port=pull_port, work_function=WORK_FUNCTION, state_topic=state_topic, verbose=verbose)
    worker.connect_sockets()
    worker.start_ioloop()


if __name__ == "__main__":
    start_the_worker_process()
