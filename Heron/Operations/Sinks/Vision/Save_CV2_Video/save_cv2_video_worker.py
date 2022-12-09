
import numpy as np
import time
import ffmpeg
from datetime import datetime
from subprocess import Popen
import cv2
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.communication.sink_worker import SinkWorker

need_parameters = True
worker_object: SinkWorker
file_name: str
time_stamp: bool
video_out: cv2.VideoWriter
start_timer: float
number_of_frames = 0

def initialise(worker_object):
    return True


def add_timestamp_to_filename():
    global file_name

    filename = file_name.split('.')
    date_time = '{}'.format(datetime.now()).replace(':', '-').replace(' ', '_').split('.')[0]
    file_name = '{}_{}.{}'.format(filename[0], date_time, filename[1])


def save_video(data, parameters):
    global worker_object
    global need_parameters
    global time_stamp
    global file_name
    global video_out
    global start_timer
    global end_timer
    global number_of_frames

    # Once the parameters are received at the starting of the graph then they cannot be updated any more.
    if need_parameters:
        try:
            file_name = parameters[0]
            time_stamp = parameters[1]
            fourcc_str = parameters[2]
            fps = parameters[3]
            if time_stamp:
                add_timestamp_to_filename()
            need_parameters = False

            worker_object.num_of_iters_to_update_savenodestate_substate = 3600 * 120  # Every hour
            worker_object.savenodestate_create_parameters_df(file_name=file_name, time_stamp=time_stamp,
                                                             fourcc=fourcc_str, fps=fps)
        except:
            return
    else:
        message = data[1:]  # data[0] is the topic
        image = Socket.reconstruct_array_from_bytes_message_cv2correction(message)
        size = image.shape
        try:
            video_out.write(image.astype(np.uint8))
        except Exception as e:
            fourcc_str = parameters[2]
            fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
            fps = parameters[3]
            w = size[1]
            h = size[0]
            c = False
            if len(size) > 2:
                c = True
            print('Starting saving a {}x{} video at {}'.format(w, h, fps))
            video_out = cv2.VideoWriter(file_name, fourcc, fps, (w, h), c)
            start_timer = time.perf_counter()

        worker_object.savenodestate_update_substate_df(image_size=size)


def on_end_of_life():
    global video_out
    global start_timer
    global number_of_frames

    end_timer = time.perf_counter()
    try:
        video_out.release()
        print('oooo CV2 saved at {} fps'.format((end_timer - start_timer) / number_of_frames))
    except:
        pass


if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(initialisation_function=initialise,
                                                     work_function=save_video, end_of_life_function=on_end_of_life)
    worker_object.start_ioloop()
