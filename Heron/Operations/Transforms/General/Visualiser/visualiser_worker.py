
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
import dearpygui.dearpygui as dpg
import cv2
import threading
import pprint as pp
from Heron.communication.socket_for_serialization import Socket
from Heron.communication.transform_worker import TransformWorker
from Heron.gui.visualisation_dpg import VisualisationDPG
from Heron import general_utils as gu

visualisation_dpg: VisualisationDPG


def get_vis_type_parameter(_worker_object):
    global worker_object
    global visualisation_dpg

    worker_object = _worker_object

    visualisation_on = worker_object.parameters[0]
    visualisation_type = worker_object.parameters[1]
    buffer = worker_object.parameters[2]

    visualisation_dpg = VisualisationDPG(_visualisation_type=visualisation_type,
                                         _buffer=buffer)

    worker_object.relic_create_parameters_df(visualisation_on=visualisation_on,
                                              visualisation_type=visualisation_type,
                                              buffer=buffer)
    return True



def visualise(msg, parameters):
    global visualisation_dpg

    message = msg[1:]  # data[0] is the topic
    data = Socket.reconstruct_array_from_bytes_message(message)

    if parameters is not None:
        visualisation_on = parameters[0]
        visualisation_dpg.visualisation_on = visualisation_on

        try:
            visualisation_dpg.visualise(data)

        except Exception as e:
            print(e)

    return [data]


def on_end_of_life():
    global visualisation_dpg

    visualisation_dpg.end_of_life()


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(initialisation_function=get_vis_type_parameter,
                                                          work_function=visualise,
                                                          end_of_life_function=on_end_of_life)
    worker_object.start_ioloop()