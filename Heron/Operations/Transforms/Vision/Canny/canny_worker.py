
import sys
from os import path
import cv2
import numpy as np

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.Operations.Transforms.Vision.Canny import canny_com
from Heron.gui.visualisation import Visualisation

vis: Visualisation


def initialise(worker_object):
    global vis

    try:
        min_val = worker_object.parameters[1]
        max_val = worker_object.parameters[2]
    except:
        return False

    vis = Visualisation(worker_object.node_name, worker_object.node_index)
    vis.visualisation_init()

    worker_object.relic_create_parameters_df(visualisation_on=vis.visualisation_on, min_val=min_val, max_val=max_val)
    return True


def canny(data, parameters):
    global vis

    try:
        vis.visualisation_on = parameters[0]
        min_val = parameters[1]
        max_val = parameters[2]
    except:
        vis.visualisation_on = canny_com.ParametersDefaultValues[0]
        min_val = canny_com.ParametersDefaultValues[1]
        max_val = canny_com.ParametersDefaultValues[2]

    message = data[1:]  # data[0] is the topic
    image = Socket.reconstruct_array_from_bytes_message_cv2correction(message)
    try:
        vis.visualised_data = cv2.Canny(image, min_val, max_val)
    except:
        vis.visualised_data = np.array((10, 10))
        print('Canny operation failed')

    return [vis.visualised_data]


def on_end_of_life():
    global vis
    vis.kill()


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(canny, on_end_of_life, initialise)
    worker_object.start_ioloop()
