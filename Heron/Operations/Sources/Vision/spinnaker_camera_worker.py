
from simple_pyspin import Camera
import cv2 as cv2
import sys
import threading
from Heron.communication.source_worker import SourceWorker

visualisation_on = False
image = []


def visualisation_loop():
    global image
    global visualisation_on

    while visualisation_on:
        cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)

        width = cv2.getWindowImageRect("Camera")[2]
        height = cv2.getWindowImageRect("Camera")[3]
        try:
            image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
            cv2.imshow('Camera', image)
            cv2.waitKey(1)
        except:
            pass



def worker_function(worker):
    global visualisation_on
    global image

    with Camera() as cam:  # Acquire and initialize Camera
        cam.start()  # Start recording

        while True:
            image = cam.get_array()
            worker.socket_push_data.send_array(image, copy=False)
            cv2.waitKey(1)


def on_end_of_life():
    pass


def start_the_worker_process():
    args = sys.argv[1:]
    assert len(args) == 3, 'The Source worker process needs 3 arguments, the port, the state topic and the verbose ' \
                           'value'
    port, state_topic, verbose = args
    verbose = verbose == 'True'

    worker = SourceWorker(port=port, state_topic=state_topic, end_of_life_function=on_end_of_life, verbose=verbose)
    worker.connect_socket()
    worker.start_heartbeat_thread()
    worker.start_parameters_thread()

    global visualisation_on
    visualisation_on = True
    visualisation_thread = threading.Thread(target=visualisation_loop, daemon=True)
    visualisation_thread.start()

    worker_function(worker)


if __name__ == "__main__":
    start_the_worker_process()