
from simple_pyspin import Camera
import cv2 as cv2
import sys
from Heron.communication.source_worker import SourceWorker


def show_preview(frame):
    cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)

    width = cv2.getWindowImageRect("Camera")[2]
    height = cv2.getWindowImageRect("Camera")[3]
    try:
        frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
    except:
        pass
    cv2.imshow('Camera', frame)

    cv2.waitKey(1)


def worker_function(worker):
    with Camera() as cam: # Acquire and initialize Camera
        cam.start() # Start recording
        #print(cam.PixelFormat)
        #if 'Bayer' in cam.PixelFormat:
        #    cam.PixelFormat = "RGB8"

        while True:
            image = cam.get_array()
            show_preview(image)
            worker.socket_push_data.send_array(image, copy=False)
            cv2.waitKey(1)


def start_the_worker_process():
    args = sys.argv[1:]
    assert len(args) == 3, 'The Source worker process needs 3 arguments, the port, the state topic and the verbose ' \
                           'value'
    port, state_topic, verbose = args
    verbose = verbose == 'True'

    worker = SourceWorker(port=port, state_topic=state_topic)
    worker.connect_socket()
    worker.start_parameters_thread()
    worker.start_heartbeat_thread()

    worker_function(worker)


if __name__ == "__main__":
    start_the_worker_process()