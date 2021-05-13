
import cv2
import numpy as np
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.Operations.Transforms.Vision import canny_com
from Heron.communication.transform_worker import TransformWorker

worker_object: TransformWorker


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


    message = data[1:]  # link[0] is the topic
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


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(canny, on_end_of_life)
    worker_object.start_ioloop()
