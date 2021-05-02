
from simple_pyspin import Camera
import cv2 as cv2
import sys
from Heron import general_utils as gu
from Heron.communication.source_worker import SourceWorker
from Heron.Operations.Sources.Vision import spinnaker_camera_com

def worker_function(worker_object):

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


def start_the_worker_process():

    port, parameters_topic, _, verbose = gu.parse_arguments_to_worker(sys.argv)
    verbose = verbose == 'True'

    worker_object = SourceWorker(port=port, parameters_topic=parameters_topic, end_of_life_function=on_end_of_life, verbose=verbose)
    worker_object.connect_socket()
    worker_object.start_heartbeat_thread()
    worker_object.start_parameters_thread()
    worker_function(worker_object)


if __name__ == "__main__":
    start_the_worker_process()