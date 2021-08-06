
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
import dearpygui.dearpygui as dpg
import cv2
import matplotlib.pyplot as plt
from scipy.ndimage import rotate
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu

need_parameters = True
screen_image = []
overlayed_image = []
image_height = 800
image_width = 1280
screen_texture_id: int
photodiode_on = False
overlay_image_pos = []
angle = 0.0


def screen_image_to_blue():
    global image_width
    global image_height
    global screen_image
    global screen_texture_id
    global photodiode_on

    screen_image = np.zeros((image_width, image_height, 4))
    screen_image[:, :, 2:] = 255 / 255
    screen_image = list(screen_image.flatten(order='C').astype(np.float16))

    dpg.set_value(screen_texture_id, screen_image)

    photodiode_on = True


def screen_image_to_black():
    global image_width
    global image_height
    global screen_image
    global screen_texture_id
    global photodiode_on

    screen_image = np.zeros((image_width, image_height, 4))
    screen_image[:, :, 3] = 255 / 255
    screen_image = list(screen_image.flatten(order='C').astype(np.float16))

    dpg.set_value(screen_texture_id, screen_image)

    photodiode_on = False


def overlay_image(angle):
    global overlayed_image
    global screen_image
    global overlay_image_pos
    global screen_texture_id

    oi_image_height, oi_image_width, oi_channels = overlayed_image.shape

    screen_image_to_blue()
    screen_image = np.reshape(screen_image, (image_width, image_height, 4)).astype(np.float16)

    rotated_overlayed_image = rotate(overlayed_image, angle, (0, 1), reshape=False).astype(np.float16) / overlayed_image.max()
    rotated_overlayed_image = np.flipud(rotated_overlayed_image)

    if screen_image.shape[0] < overlay_image_pos[0] + oi_image_width:
        print('Picture pos_x + size_x bigger than screen size_x')
    if screen_image.shape[1] < overlay_image_pos[1] + oi_image_height:
        print('Picture pos_y + size_y bigger than screen size_y')

    try:
        screen_image[overlay_image_pos[0]:overlay_image_pos[0] + oi_image_width,
                     overlay_image_pos[1]:overlay_image_pos[1] + oi_image_height, :] = rotated_overlayed_image
    except Exception as e:
        print(e)
    screen_image = np.moveaxis(screen_image, 1, 0)

    screen_image = list(screen_image.flatten(order='C').astype(np.float16))
    dpg.set_value(screen_texture_id, screen_image)


def start_dpg_thread():
    global image_width
    global image_height
    global screen_image
    global screen_texture_id

    screen_image = np.zeros((image_width, image_height, 4))
    screen_image[:, :, 3] = 255 / 255
    screen_image = list(screen_image.flatten(order='C').astype(np.float16))

    with dpg.texture_registry():
        screen_texture_id = dpg.add_dynamic_texture(width=image_width, height=image_height, default_value=screen_image)

    with dpg.window(label="Tutorial", no_title_bar=True, width=image_width + 10, height=image_height + 20,
                    no_background=True):
        dpg.add_image(screen_texture_id, width=image_width, height=image_height)

    dpg.setup_viewport()
    dpg.set_viewport_title(title='Custom Title')
    dpg.set_viewport_width(image_width + 20)
    dpg.set_viewport_height(image_height + 20)
    dpg.set_viewport_pos([1980, 0])
    dpg.set_viewport_decorated(False)

    dpg.start_dearpygui()


def update_output(data, parameters):
    global need_parameters
    global overlayed_image
    global overlay_image_pos

    # Once the parameters are received at the starting of the graph then they cannot be updated any more.
    if need_parameters:
        try:
            overlay_image_file_name = parameters[0]
            overlay_image_pos = [parameters[1], parameters[2]]
            overlayed_image = cv2.imread(overlay_image_file_name).astype(np.float16)/255
            oi_image_height, oi_image_width, oi_channels = overlayed_image.shape
            if oi_channels == 3:
                overlayed_image = np.dstack((overlayed_image[:, :, 2], overlayed_image[:, :, 1],
                                             overlayed_image[:, :, 0], np.ones((oi_image_height, oi_image_width))))
            if oi_channels == 1:
                overlayed_image = np.dstack(
                    (overlayed_image, overlayed_image, overlayed_image, np.ones((oi_image_height, oi_image_width))))

            need_parameters = False
        except Exception as e:
            print(e)
            return

    topic = data[0].decode('utf-8')
    message = Socket.reconstruct_array_from_bytes_message(data[1:])

    if 'Trigger_Photodiode' in topic:
        if not photodiode_on:
            screen_image_to_blue()
        else:
            screen_image_to_black()

    if 'Angle_of_Pic' in topic:
        if photodiode_on:
            message = message[0]
            if type(message) == np.int32 or type(message) == np.float32:
                overlay_image(message + 90)


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(update_output, on_end_of_life)
    worker_object.set_new_visualisation_loop(start_dpg_thread)
    worker_object.visualisation_on = True
    worker_object.visualisation_loop_init()
    worker_object.start_ioloop()
