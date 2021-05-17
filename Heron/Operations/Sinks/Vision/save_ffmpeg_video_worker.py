
import numpy as np
import time
import ffmpeg
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.communication.sink_worker import SinkWorker

worker_object: SinkWorker
need_parameters = True
output = None
write_proc = None


def ffmpeg_write_process(out_filename, fps, pixel_format_in,  pixel_format_out, width, height):
    return(
        ffmpeg
        .input('pipe:', format='rawvideo', vcodec='rawvideo', r=fps, pix_fmt=pixel_format_in,
                s='{}x{}'.format(width, height))
        .output(out_filename, vcodec='h264_nvenc', pix_fmt=pixel_format_out, r=fps, preset='medium', bitrate='50M')
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )


def save_video(data, parameters):
    global worker_object
    global need_parameters
    global output
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
            pixel_format_in = parameters[1]
            pixel_format_out = parameters[2]
            fps = parameters[3]
            need_parameters = False
            print('Starting video saving')
        except:
            return
    else:
        message = data[1:]  # data[0] is the topic
        image = Socket.reconstruct_array_from_bytes_message_cv2correction(message)
        size = image.shape

        if write_proc is None:
            write_proc = ffmpeg_write_process(file_name, fps, pixel_format_in, pixel_format_out, size[1], size[0])

        write_proc.stdin.write(image.astype(np.uint8).tobytes())

    end = time.perf_counter()
    #print('ooooTime of frame receive = {}, saved = {}, dif = {}'.format(start, end, end-start))


def on_end_of_life():
    #global output
    #output.release()
    global write_proc
    try:
        write_proc.stdin.close()
        write_proc.wait()
    except:
        pass


if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(save_video, on_end_of_life)
    worker_object.start_ioloop()
