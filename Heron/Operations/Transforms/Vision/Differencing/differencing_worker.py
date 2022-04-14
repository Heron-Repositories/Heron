
import sys
from os import path
import numpy as np

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.Operations.Transforms.Vision.Differencing import differencing_com
from Heron.gui.visualisation import Visualisation
from Heron.communication.transform_worker import TransformWorker

vis: Visualisation
worker_object: TransformWorker


def initialise(_worker_object):
    global worker_object
    global vis

    worker_object = _worker_object

    try:
        frame2_minus_frame1 = worker_object.parameters[1]
    except:
        return False

    vis = Visualisation(worker_object.node_name, worker_object.node_index)
    vis.visualisation_init()

    worker_object.relic_create_parameters_df(visualisation_on=vis.visualisation_on,
                                             frame2_minus_frame1=frame2_minus_frame1)

    return True


def differencing(data, parameters):
    global vis
    global worker_object

    topic = data[0].decode('ascii')
    message = data[1:]

    try:
        vis.visualisation_on = parameters[0]
        frame2_minus_frame1 = parameters[1]
    except:
        vis.visualisation_on = differencing_com.ParametersDefaultValues[0]
        frame2_minus_frame1 = differencing_com.ParametersDefaultValues[1]

    image = Socket.reconstruct_array_from_bytes_message_cv2correction(message)
    for received_topic in worker_object.recv_topics_buffer:
        if topic in received_topic:
            worker_object.recv_topics_buffer[received_topic] = image
    all_topics = list(worker_object.recv_topics_buffer.keys())

    if np.shape(worker_object.recv_topics_buffer[all_topics[0]])[0] > 0 and np.shape(worker_object.recv_topics_buffer[all_topics[1]])[0] > 0:
        if worker_object.recv_topics_buffer[all_topics[0]].shape == worker_object.recv_topics_buffer[all_topics[1]].shape:
            worker_object.worker_result = worker_object.recv_topics_buffer[all_topics[0]] -\
                                          worker_object.recv_topics_buffer[all_topics[1]]
        elif len(worker_object.recv_topics_buffer) == 2:
            if worker_object.verbose:
                print('Shapes of two arrays are not the same. Input 1 shape = {}, input 2 shape = {}. Passing through 1st input'.
                      format(np.shape(worker_object.recv_topics_buffer[all_topics[0]]),
                             np.shape(worker_object.recv_topics_buffer[all_topics[1]])))
            worker_object.worker_result = worker_object.recv_topics_buffer[all_topics[0]]

        if frame2_minus_frame1:
            worker_object.worker_result = worker_object.recv_topics_buffer[all_topics[1]] -\
                                          worker_object.recv_topics_buffer[all_topics[0]]
    else:
        worker_object.worker_result = np.random.random((100,100))
        print('Differencing {} failed. The frame buffer is empty.'.format(worker_object.node_index))

    vis.visualised_data = worker_object.worker_result

    return [worker_object.worker_result]


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(differencing, on_end_of_life, initialise)
    worker_object.start_ioloop()
