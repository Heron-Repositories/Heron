
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import cv2 as cv2
from Heron import general_utils as gu
from Heron.Operations.Sources.Vision.Camera import camera_com

acquiring_on = False
capture = None


def run_camera(worker_object):
    global capture
    global acquiring_on

    if not recording_on:  # Get the parameters from the node
        while not recording_on:
            try:
                cam_index = worker_object.parameters[1]
                capture = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
                recording_on = True
                print('Got camera parameters. Starting capture')
            except:
                cv2.waitKey(1)

    while True:
        ret, worker_object.worker_result = capture.read()
        worker_object.socket_push_data.send_array(worker_object.worker_result, copy=False)
        try:
            worker_object.visualisation_on = worker_object.parameters[0]
        except:
            worker_object.visualisation_on = camera_com.ParametersDefaultValues[0]

        worker_object.visualisation_loop_init()


def on_end_of_life():
    global capture
    capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    gu.start_the_source_worker_process(run_camera, on_end_of_life)