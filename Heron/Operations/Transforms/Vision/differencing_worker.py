
import sys
import cv2
import numpy as np
from Heron.communication.transform_worker import TransformWorker
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu

# Initialised in the start_the_worker_process function
buffer = {}


def differencing(data, parameters):
    global buffer

    topic = data[0].decode('ascii')
    message = data[1:]

    #time_offset = parameters[0]
    
    image = Socket.reconstruct_array_from_bytes_message_cv2correction(message)
    for received_topic in buffer:
        if topic in received_topic:
            buffer[received_topic] = image
    all_topics = list(buffer.keys())

    if np.shape(buffer[all_topics[0]])[0] > 0 and np.shape(buffer[all_topics[1]])[0] > 0:
        if buffer[all_topics[0]].shape == buffer[all_topics[1]].shape:
            result = buffer[all_topics[0]] - buffer[all_topics[1]]
        elif len(buffer) == 2:
            buffer[all_topics[1]] = cv2.resize(buffer[all_topics[1]], buffer[all_topics[0]].shape)
            result = buffer[all_topics[0]] - buffer[all_topics[1]]
    else:
        result = np.random.random((100,100))
        print('Differencing failed. The frame buffer is empty')
    cv2.namedWindow("Differencing", cv2.WINDOW_NORMAL)
    cv2.imshow('Differencing', result)
    cv2.waitKey(1)

    return [result]


WORK_FUNCTION = differencing


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
