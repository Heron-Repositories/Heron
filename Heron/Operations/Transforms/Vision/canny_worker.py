
from Heron.communication.transform_worker import TransformWorker
from Heron.communication.socket_for_serialization import Socket
import sys
import cv2


def canny(data, arguments):
    min_val = arguments[0]
    max_val = arguments[1]
    image = Socket.reconstruct_array_from_bytes_message_cv2correction(data)
    edges = cv2.Canny(image, min_val, max_val)
    cv2.namedWindow("Canny", cv2.WINDOW_NORMAL)
    cv2.imshow('Canny', edges)
    cv2.waitKey(1)

    return edges


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
    args = sys.argv[1:]
    assert len(args) == 4, 'The Transform worker process needs 4 arguments, the push port, the pull port, the state ' \
                           'topic and the verbose value'
    push_port, pull_port, state_topic, verbose = sys.argv[1:]
    verbose = verbose == 'True'

    worker = TransformWorker(pull_port=pull_port, push_port=push_port, work_function=canny, state_topic=state_topic,
                             verbose=verbose)
    worker.connect_sockets()
    worker.start_ioloop()


if __name__ == "__main__":
    start_the_worker_process()
