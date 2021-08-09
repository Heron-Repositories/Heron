
import sys
import os
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
from datetime import datetime
import time
import cv2 as cv2
import logging
from Heron import general_utils as gu
from Heron.Operations.Sources.Vision.Arducam_Quadrascopic_Camera.arducam_utilities import ArducamUtils

acquiring_on = False
capture: cv2.VideoCapture
output_video: cv2.VideoWriter
width: int
height: int
counter: int
frame_count: int
arducam_utils: ArducamUtils
save_file: str
get_subcamera_index: int
sub_camera_scale: float
total_frame_time: int


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


def add_timestamp_to_filename():
    global save_file

    filename = save_file.split('.')
    date_time = '{}'.format(datetime.now()).replace(':', '-').replace(' ', '_').split('.')[0]
    save_file = '{}_{}.{}'.format(filename[0], date_time, filename[1])


def change_camera_parameters(worker_object):
    exposure = worker_object.parameters[2]
    gain = worker_object.parameters[3]
    trigger_mode = worker_object.parameters[4]

    result = []
    if exposure != -1:
        result.append(os.system('v4l2-ctl -c exposure={}'.format(exposure)))
        time.sleep(0.2)
    if gain != -1:
        result.append(os.system('v4l2-ctl -c gain={}'.format(gain)))
        time.sleep(0.2)
    if trigger_mode:
        result.append(os.system('v4l2-ctl -c trigger_mode=1'))
        time.sleep(0.2)
        result.append(os.system('v4l2-ctl -c disable_frame_timeout={}'.format(1)))
        time.sleep(0.2)
    else:
        result.append(os.system('v4l2-ctl -c trigger_mode=0'))
        time.sleep(0.2)
    return result


def run_camera(worker_object):
    global capture
    global output_video
    global acquiring_on
    global width
    global height
    global counter
    global frame_count
    global arducam_utils
    global save_file
    global get_subcamera_index
    global sub_camera_scale
    global total_frame_time

    if not acquiring_on:  # Get the parameters from the node
        while not acquiring_on:
            try:
                cam_index = worker_object.parameters[0]
                codec = worker_object.parameters[1]
                # parameters 2 to 4 are used in the change_camera_parameters()
                get_subcamera_index = worker_object.parameters[5]
                sub_camera_scale = worker_object.parameters[6]
                save_file = worker_object.parameters[7]
                add_time_stamp = worker_object.parameters[8]
                file_fps = worker_object.parameters[9]

                acquiring_on = True
                logging.debug('Got arducam parameters. Starting capture')
                print('Got arducam parameters. Starting capture')
            except:
                logging.debug('Waiting to get parameters for Arducam')
                cv2.waitKey(100)

        capture = cv2.VideoCapture(cam_index, cv2.CAP_V4L2)

        # set pixel format
        if not capture.set(cv2.CAP_PROP_FOURCC, pixelformat(codec)):
            logging.debug("Failed to set pixel format.")

        arducam_utils = ArducamUtils(cam_index)
        show_info(arducam_utils)

        # turn off RGB conversion
        if arducam_utils.convert2rgb == 0:
            capture.set(cv2.CAP_PROP_CONVERT_RGB, arducam_utils.convert2rgb)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if len(save_file) > 1:
            if add_time_stamp:
                add_timestamp_to_filename()

            gst_out = "appsrc ! video/x-raw, format=GRAY8 ! nvvidconv ! video/x-raw(memory:NVMM) ! \
                       omxh264enc ! h264parse ! matroskamux ! filesink location={}".format(save_file)
            #gst_out = "appsrc ! video/x-raw, format=GRAY8 ! queue ! nvvidconv ! omxh264enc ! h264parse ! qtmux ! filesink location={} ".format(file_name)
            output_video = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, 0, file_fps, (width, height), False)

        # Before changing the v4l2 driver parameters first capture a frame (otherwise the changes do not stick)
        got_frame, frame = capture.read()
        if got_frame:
            change_camera_parameters(worker_object)
            os.system('v4l2-ctl -l')  # send the camera parameters to the stdout
        else:
            logging.error("Arducam didn't acquire the first frame correctly. Aborting")
            print("Arducam didn't acquire the first frame correctly. Aborting")
            return

    counter = 0
    total_frame_time = 0
    while acquiring_on:
        start = datetime.now()
        got_frame, frame = capture.read()
        if got_frame:

            counter += 1

            frame = arducam_utils.convert(frame)

            if len(save_file) > 1:
                output_video.write(frame.astype('uint8'))

            if get_subcamera_index != '0':
                sub_cam = int(get_subcamera_index)
                new_width = int(width / 4)
                start_pixel = new_width * (sub_cam - 1)
                end_pixel = start_pixel + new_width
                frame = np.ascontiguousarray(frame[:, start_pixel:end_pixel])

                if sub_camera_scale != 1.0:
                    dst_width = sub_camera_scale * new_width
                    frame = resize(frame, dst_width)

            worker_object.worker_result = frame
            worker_object.socket_push_data.send_array(worker_object.worker_result, copy=False)

            total_frame_time = total_frame_time + (datetime.now() - start).total_seconds()


def on_end_of_life():
    global capture
    global output_video
    global total_frame_time
    global counter
    global acquiring_on

    avgtime = total_frame_time / counter
    logging.debug("Average time between frames: " + str(avgtime))
    logging.debug("Average FPS: " + str(1 / avgtime))

    acquiring_on = False
    time.sleep(0.5)

    capture.release()
    try:
        output_video.release()
    except:
        pass


if __name__ == "__main__":
    gu.start_the_source_worker_process(run_camera, on_end_of_life)