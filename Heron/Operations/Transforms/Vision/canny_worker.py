
import sys
import cv2
import numpy as np
import threading
import copy
from Heron.communication.transform_worker import TransformWorker
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.Operations.Transforms.Vision import canny_com

buffer = {}
result = []
visualisation_on = False
index = 0


def visualisation_loop():
    global result
    global visualisation_on
    global index

    cv2.namedWindow("Canny {}".format(index), cv2.WINDOW_NORMAL)

    while visualisation_on:
        try:
            cv2.imshow("Canny {}".format(index), result)
        except:
            pass
        cv2.waitKey(1)


def canny(data, parameters):
    global result
    global visualisation_on

    try:
        min_val = parameters[0]
        max_val = parameters[1]
    except:
        min_val = canny_com.ParametersDefaultValues[0]
        max_val = canny_com.ParametersDefaultValues[1]

    message = data[1:]  # data[0] is the topic
    image = Socket.reconstruct_array_from_bytes_message_cv2correction(message)
    try:
        result = cv2.Canny(image, min_val, max_val)
    except:
        result = np.array((10,10))
        print('Canny operation failed')

    return [result]


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
    The state_topic is the topic where the state (parameters of the worker function) will be received
    Verbose is the verbosity
    :return:
    """
    global buffer
    global visualisation_on
    global index

    pull_port, state_topic, receiving_topics, verbose = gu.parse_arguments_to_worker(sys.argv)
    verbose = verbose == 'True'
    for rt in receiving_topics:
        buffer[rt] = []
    index = state_topic.split('##')[-1]

    worker = TransformWorker(pull_port=pull_port, work_function=WORK_FUNCTION, end_of_life_function=END_OF_LIFE_FUNCTION,
                             state_topic=state_topic, verbose=verbose)
    worker.connect_sockets()

    visualisation_on = True
    visualisation_thread = threading.Thread(target=visualisation_loop, daemon=True)
    visualisation_thread.start()

    worker.start_ioloop()


if __name__ == "__main__":
    start_the_worker_process()
