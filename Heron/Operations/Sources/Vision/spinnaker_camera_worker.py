
from simple_pyspin import Camera
import cv2 as cv2
import sys
from Heron.communication.source_worker import SourceWorker


def show_preview(frame):
    cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)

    windowWidth = cv2.getWindowImageRect("Camera")[2]
    windowHeight = cv2.getWindowImageRect("Camera")[3]
    try:
        frame = cv2.resize(frame, (windowWidth, windowHeight), interpolation=cv2.INTER_AREA)
    except:
        pass
    cv2.imshow('Camera', frame)

    cv2.waitKey(1)


def main():
    port = '7000'
    if sys.argv[1] is not None:
        port = sys.argv[1]

    worker = SourceWorker(port=port)
    worker.connect_socket()

    with Camera() as cam: # Acquire and initialize Camera
        cam.start() # Start recording
        #print(cam.PixelFormat)
        #if 'Bayer' in cam.PixelFormat:
        #    cam.PixelFormat = "RGB8"

        running = True
        while running:
            image = cam.get_array()
            show_preview(image)
            worker.socket_push_data.send_array(image, copy=False)
            cv2.waitKey(1)
'''

cam = cv2.VideoCapture(0)
running = True
while running:
    _, image = cam.read()
    socket_push_data.send_array(image, copy=False)
    cv2.waitKey(1)
'''

if __name__ == "__main__":
    main()