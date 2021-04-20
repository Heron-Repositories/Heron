
from Heron.communication.transform_worker import TransformWorker
from Heron.communication.socket_for_serialization import Socket
import sys
import cv2
import numpy as np

def canny(data, min_val=100, max_val=150):

    image = Socket.reconstruct_array_from_bytes_message_cv2correction(data)
    #edges = cv2.Canny(image, min_val, max_val)
    edges = np.ones((100,100))
    #cv2.namedWindow("Canny", cv2.WINDOW_NORMAL)
    #cv2.imshow('Canny', edges)
    #cv2.waitKey(1)

    return edges


def main():
    """
    The pull_port is the port that he canny_worker uses to pull data from the canny_com (the canny_com's push_port)
    The push_port is the port that he canny_worker uses to push data to the canny_com (the canny_com's pull_port)
    :return:
    """
    pull_port = '8000'
    push_port = '8001'
    verbose = True
    for i, arg in enumerate(sys.argv):
        if i == 1:
            push_port = arg
        elif i ==2:
            pull_port = arg
        elif i == 3:
            verbose = arg == 'True'

    worker = TransformWorker(pull_port=pull_port, push_port=push_port, work_function=canny, verbose=verbose)
    worker.connect_sockets()
    worker.start_ioloop()


if __name__ == "__main__":
    main()
