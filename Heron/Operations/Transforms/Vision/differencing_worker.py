
import sys
import cv2
import numpy as np
import threading
from Heron.communication.transform_worker import TransformWorker
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.Operations.Transforms.Vision import differencing_com

# Initialised in the start_the_worker_process function
buffer = {}
visualisation_on = False
result = []
index = 0


def visualisation_loop():
    global result
    global visualisation_on
    global index

    cv2.namedWindow("Differencing {}".format(index), cv2.WINDOW_NORMAL)

    while visualisation_on:
        cv2.imshow("Differencing {}".format(index), result)
        visualisation_on = True
        cv2.waitKey(1)


def differencing(data, parameters):
    global buffer
    global visualisation_on
    global result

    topic = data[0].decode('ascii')
    message = data[1:]
    try:
        frame2_minus_frame1 = parameters[0]
    except:
        frame2_minus_frame1 = differencing_com.ParametersDefaultValues[0]

    image = Socket.reconstruct_array_from_bytes_message_cv2correction(message)
    for received_topic in buffer:
        if topic in received_topic:
            buffer[received_topic] = image
    all_topics = list(buffer.keys())

    if np.shape(buffer[all_topics[0]])[0] > 0 and np.shape(buffer[all_topics[1]])[0] > 0:
        if buffer[all_topics[0]].shape == buffer[all_topics[1]].shape:
            pass
        elif len(buffer) == 2:
            buffer[all_topics[1]] = cv2.resize(buffer[all_topics[1]], buffer[all_topics[0]].shape)
        result = buffer[all_topics[0]] - buffer[all_topics[1]]
        if frame2_minus_frame1:
            result = buffer[all_topics[1]] - buffer[all_topics[0]]

    else:
        result = np.random.random((100,100))
        print('Differencing failed. The frame buffer is empty')

    if not visualisation_on:
        visualisation_on = True
        visualisation_thread = threading.Thread(target=visualisation_loop, daemon=True)
        visualisation_thread.start()

    return [result]


def on_end_of_life():
    pass


WORK_FUNCTION = differencing
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
    global index

    pull_port, state_topic, receiving_topics, verbose = gu.parse_arguments_to_worker(sys.argv)
    verbose = verbose == 'True'

    for rt in receiving_topics:
        buffer[rt] = []
    index = state_topic.split('##')[-1]

    worker = TransformWorker(pull_port=pull_port, work_function=WORK_FUNCTION, end_of_life_function=END_OF_LIFE_FUNCTION,
                             state_topic=state_topic, verbose=verbose)
    worker.connect_sockets()
    worker.start_ioloop()


if __name__ == "__main__":
    start_the_worker_process()
