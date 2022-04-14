
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import cv2 as cv2
from Heron import general_utils as gu
from Heron.Operations.Sources.Vision.Camera import camera_com
from Heron.gui.visualisation import Visualisation

acquiring_on = False
capture = None
vis: Visualisation


def run_camera(worker_object):
    global capture
    global acquiring_on
    global vis

    vis = Visualisation(worker_object.node_name, worker_object.node_index)
    vis.visualisation_init()

    if not acquiring_on:  # Get the parameters from the node

        while not acquiring_on:

            try:
                cam_index = worker_object.parameters[1]
                capture = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
                acquiring_on = True
                print('Got camera parameters. Starting capture')
            except:
                cv2.waitKey(1)

    worker_object.relic_create_parameters_df(visualisation_on=False,
                                             camera_index=cam_index)
    worker_object.initialised = True

    while acquiring_on:

        ret, vis.visualised_data = capture.read()
        worker_object.send_data_to_com(vis.visualised_data)
        try:
            vis.visualisation_on = worker_object.parameters[0]
        except:
            vis.visualisation_on = camera_com.ParametersDefaultValues[0]


def on_end_of_life():
    global capture
    global acquiring_on
    global vis

    acquiring_on = False
    try:
        capture.release()
        vis.kill()
    except:
        pass


if __name__ == "__main__":
    gu.start_the_source_worker_process(work_function=run_camera, end_of_life_function=on_end_of_life)