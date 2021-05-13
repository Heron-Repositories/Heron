
from simple_pyspin import Camera
import cv2 as cv2
from Heron import general_utils as gu
from Heron.Operations.Sources.Vision import spinnaker_camera_com


def run_spinnaker_camera(worker_object):
    with Camera() as cam:  # Acquire and initialize Camera
        cam.start()  # Start recording

        while True:
            worker_object.worker_result = cam.get_array()
            worker_object.socket_push_data.send_array(worker_object.worker_result, copy=False)

            try:
                worker_object.visualisation_on = worker_object.parameters[0]
            except:
                worker_object.visualisation_on = spinnaker_camera_com.ParametersDefaultValues[0]

            worker_object.visualisation_toggle()
            cv2.waitKey(1)


def on_end_of_life():
    pass


if __name__ == "__main__":
    gu.start_the_source_worker_process(run_spinnaker_camera, on_end_of_life)