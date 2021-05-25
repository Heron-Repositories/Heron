
import cv2
import numpy as np
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.Operations.Transforms.Vision import differencing_com

# Initialised in the start_the_worker_process function
worker_object = None


def differencing(data, parameters):
    global worker_object

    topic = data[0].decode('ascii')
    message = data[1:]
    try:
        worker_object.visualisation_on = parameters[0]
        frame2_minus_frame1 = parameters[1]
    except:
        worker_object.visualisation_on = differencing_com.ParametersDefaultValues[0]
        frame2_minus_frame1 = differencing_com.ParametersDefaultValues[1]

    image = Socket.reconstruct_array_from_bytes_message_cv2correction(message)
    for received_topic in worker_object.recv_topics_buffer:
        if topic in received_topic:
            worker_object.recv_topics_buffer[received_topic] = image
    all_topics = list(worker_object.recv_topics_buffer.keys())

    if np.shape(worker_object.recv_topics_buffer[all_topics[0]])[0] > 0 and np.shape(worker_object.recv_topics_buffer[all_topics[1]])[0] > 0:
        if worker_object.recv_topics_buffer[all_topics[0]].shape == worker_object.recv_topics_buffer[all_topics[1]].shape:
            temp = worker_object.recv_topics_buffer[all_topics[1]]
        elif len(worker_object.recv_topics_buffer) == 2:
            new_shape = tuple(worker_object.recv_topics_buffer[all_topics[0]].shape)
            if len(new_shape) == 2:
                new_shape = (new_shape[0], new_shape[1], 1)
            temp = np.zeros((new_shape[1], new_shape[0], new_shape[2]))
            for d in range(new_shape[2]):
                temp[:, :, d] = \
                    cv2.resize(src=worker_object.recv_topics_buffer[all_topics[1]][:, :, d], dsize=new_shape[:2])
            temp = np.transpose(temp, [1, 0, 2])
        worker_object.worker_result = worker_object.recv_topics_buffer[all_topics[0]] - temp
        if frame2_minus_frame1:
            worker_object.worker_result = temp - worker_object.recv_topics_buffer[all_topics[0]]
    else:
        worker_object.worker_result = np.random.random((100,100))
        print('Differencing {} failed. The frame buffer is empty'.format(worker_object.node_index))

    worker_object.visualisation_loop_init()

    return [worker_object.worker_result]


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(differencing, on_end_of_life)
    worker_object.start_ioloop()
