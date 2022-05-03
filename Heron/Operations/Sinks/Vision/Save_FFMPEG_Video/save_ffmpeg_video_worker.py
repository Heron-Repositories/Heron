
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
write_proc: Popen


def initialise(worker_object):
    return True


def add_timestamp_to_filename():
    global file_name

    filename = file_name.split('.')
    date_time = '{}'.format(datetime.now()).replace(':', '-').replace(' ', '_').split('.')[0]
    file_name = '{}_{}.{}'.format(filename[0], date_time, filename[1])


def ffmpeg_write_process(out_filename, fps, pixel_format_in,  pixel_format_out, width, height):
    return(
        ffmpeg
        .input('pipe:', format='rawvideo', vcodec='rawvideo', hwaccel='auto', r=fps, pix_fmt=pixel_format_in,
                s='{}x{}'.format(width, height))
        .output(out_filename, vcodec='h264_nvenc', rc='vbr', preset='llhp',
                pix_fmt=pixel_format_out, r=fps,
                gpu=0, bitrate='50M', delay=0)
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )


def save_video(data, parameters):
    global worker_object
    global need_parameters
    global time_stamp
    global write_proc
    global file_name
    global pixel_format_out
    global pixel_format_in
    global fps
    start = time.perf_counter()
    # Once the parameters are received at the starting of the graph then they cannot be updated any more.
    if need_parameters:
        try:
            file_name = parameters[0]
            time_stamp = parameters[1]
            pixel_format_in = parameters[2]
            pixel_format_out = parameters[3]
            fps = parameters[4]
            if time_stamp:
                add_timestamp_to_filename()
            need_parameters = False

            worker_object.num_of_iters_to_update_relics_substate = -1
            worker_object.relic_create_parameters_df(file_name=file_name, time_stamp=time_stamp,
                                                     pixel_format_in=pixel_format_in, pixel_format_out=pixel_format_out,
                                                     fps=fps)
        except:
            return
    else:
        message = data[1:]  # data[0] is the topic
        image = Socket.reconstruct_array_from_bytes_message_cv2correction(message)
        size = image.shape
        try:
            write_proc.stdin.write(image.astype(np.uint8).tobytes())
        except Exception as e:
            write_proc = ffmpeg_write_process(file_name, fps, pixel_format_in, pixel_format_out, size[1], size[0])

        worker_object.relic_update_substate_df(image_size=size)

    end = time.perf_counter()
    #print('ooooTime of frame receive = {}, saved = {}, dif = {}'.format(start, end, end-start))


def on_end_of_life():
    global write_proc
    try:
        write_proc.stdin.close()
        write_proc.wait()
    except:
        pass


if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(initialisation_function=initialise,
                                                     work_function=save_video, end_of_life_function=on_end_of_life)
    worker_object.start_ioloop()
