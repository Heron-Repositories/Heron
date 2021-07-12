
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from datetime import datetime
import time
import cv2 as cv2
import logging
from Heron import general_utils as gu
from Arducam_Quadrascopic_Camera import arducam_quadrascopic_camera_com
from arducam_utilities import ArducamUtils

recording_on = False
capture: cv2.VideoCapture
width: int
height: int
counter: int
start_time: datetime.datetime
frame_count: int
start: float
arducam_utils: ArducamUtils


def resize(frame, dst_width):
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    scale = dst_width * 1.0 / frame_width
    return cv2.resize(frame, (int(scale * frame_width), int(scale * frame_height)))


def fourcc(a, b, c, d):
    return ord(a) | (ord(b) << 8) | (ord(c) << 16) | (ord(d) << 24)


def pixelformat(string):
    if len(string) != 3 and len(string) != 4:
        logging.error("{} is not a pixel format".format(string))
    if len(string) == 3:
        return fourcc(string[0], string[1], string[2], ' ')
    else:
        return fourcc(string[0], string[1], string[2], string[3])


def show_info(arducam_utils):
    _, firmware_version = arducam_utils.read_dev(ArducamUtils.FIRMWARE_VERSION_REG)
    _, sensor_id = arducam_utils.read_dev(ArducamUtils.FIRMWARE_SENSOR_ID_REG)
    _, serial_number = arducam_utils.read_dev(ArducamUtils.SERIAL_NUMBER_REG)
    logging.debug("Firmware Version: {}".format(firmware_version))
    logging.debug("Sensor ID: 0x{:04X}".format(sensor_id))
    logging.debug("Serial Number: 0x{:08X}".format(serial_number))


def run_camera(worker_object):
    global capture
    global recording_on
    global width
    global height
    global counter
    global start_time
    global frame_count
    global start
    global arducam_utils

    if not recording_on:  # Get the parameters from the node
        while not recording_on:
            try:
                cam_index = worker_object.parameters[0]
                codec = worker_object.parameters[1]

                capture = cv2.VideoCapture(cam_index, cv2.CAP_V4L2)

                # set pixel format
                if not capture.set(cv2.CAP_PROP_FOURCC, pixelformat(codec)):
                    logging.debug("Failed to set pixel format.")

                arducam_utils = ArducamUtils(cam_index)

                show_info(arducam_utils)
                # turn off RGB conversion
                if arducam_utils.convert2rgb == 0:
                    capture.set(cv2.CAP_PROP_CONVERT_RGB, arducam_utils.convert2rgb)
                    width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

                counter = 0
                start_time = datetime.now()
                frame_count = 0
                start = time.time()

                recording_on = True
                logging.debug('Got arducam parameters. Starting capture')
                print('Got arducam parameters. Starting capture')
            except:
                logging.debug('Waiting to get parameters for Arducam')
                cv2.waitKey(1)

    while True:
        ret, frame = capture.read()
        counter += 1
        frame_count += 1

        if arducam_utils.convert2rgb == 0:
            frame = frame.reshape(int(height), int(width))

        frame = arducam_utils.convert(frame)
        worker_object.worker_result = frame
        worker_object.socket_push_data.send_array(worker_object.worker_result, copy=False)


def on_end_of_life():
    global capture
    global start_time
    global counter

    end_time = datetime.now()
    elapsed_time = end_time - start_time
    avgtime = elapsed_time.total_seconds() / counter
    logging.debug("Average time between frames: " + str(avgtime))
    logging.debug("Average FPS: " + str(1 / avgtime))

    capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    gu.start_the_source_worker_process(run_camera, on_end_of_life)