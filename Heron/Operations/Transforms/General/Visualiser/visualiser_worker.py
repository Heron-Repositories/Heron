
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
import dearpygui.dearpygui as dpg
import cv2
import threading
import pprint as pp
from Heron.communication.socket_for_serialization import Socket
from Heron.communication.transform_worker import TransformWorker
from Heron import general_utils as gu

visualisation_on: bool
is_dearpygui_running: bool
visualisation_type: str
buffer: int
window_name: str
visualiser_showing = False
data = None
worker_object: TransformWorker
dpg_ids = {}
data_shape = None
dpg_thread: threading.Thread
visualisation_checking_thread_is_on = False
initialised_plots = False


def get_vis_type_parameter(_worker_object):
    global visualisation_type
    global visualisation_on
    global is_dearpygui_running
    global dpg_thread
    global buffer
    global worker_object

    worker_object = _worker_object

    visualisation_on = worker_object.parameters[0]
    visualisation_type = worker_object.parameters[1]
    buffer = worker_object.parameters[2]

    if visualisation_type != 'Image':
        is_dearpygui_running = False
        dpg_thread = threading.Thread(target=dpg_visualisation_thread, daemon=True)
        dpg_thread.start()

    return True


def show_image():
    global visualisation_on
    global data
    global visualiser_showing
    global window_name

    if visualisation_on:
        if not visualiser_showing:
            window_name = 'Visualiser'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            try:
                cv2.imshow(window_name, data)
            except Exception as e:
                print(e)
            cv2.waitKey(1)
            visualiser_showing = True
        if visualiser_showing:
            width = cv2.getWindowImageRect(window_name)[2]
            height = cv2.getWindowImageRect(window_name)[3]
            try:
                image = cv2.resize(data, (width, height), interpolation=cv2.INTER_AREA)
                cv2.imshow(window_name, image)
                cv2.waitKey(1)
            except Exception as e:
                print(e)
    else:
        cv2.destroyAllWindows()
        visualiser_showing = False
        cv2.waitKey(1)


def show_text_value():
    global data
    global buffer
    global dpg_ids

    if len(data) == 1:
        data_to_show = data[0]
        data_to_show = str(data_to_show)
        splitter = '\n'
    else:
        data_to_show = pp.pformat(data)
        splitter = '||\n'

    previous_txt_data = dpg.get_value(dpg_ids['Text'])

    previous_list_data = previous_txt_data.split(splitter)
    if len(previous_list_data) == buffer:
        previous_list_data.pop(0)

    new_txt_data = ''
    for i in previous_list_data:
        if i != '__start__':
            new_txt_data = new_txt_data + i + splitter
    new_txt_data = new_txt_data + data_to_show

    dpg.set_value(dpg_ids['Text'], new_txt_data)


def show_1d_plot():
    global data
    global buffer
    global dpg_ids
    global initialised_plots

    if buffer == -1:
        length_to_show = data.shape[-1]
    else:
        length_to_show = buffer

    number_of_lines = 1
    if len(data.shape) > 1:
        number_of_lines = data.shape[0]

    if not initialised_plots:
        for n in np.arange(0, number_of_lines):
            dpg_ids['Plot line {}'.format(n)] = dpg.add_line_series(np.arange(length_to_show), data[n:length_to_show],
                                                                       parent=dpg_ids['y_axis'])
        initialised_plots = True

    if number_of_lines > 1:
        for n in np.arange(number_of_lines):
            dpg.set_value(dpg_ids['Plot line {}'.format(n)], [np.arange(length_to_show), data[n:length_to_show]])
    else:
        dpg.set_value(dpg_ids['Plot line {}'.format(0)], [np.arange(length_to_show), data[:length_to_show]])
    dpg.fit_axis_data(dpg_ids['x_axis'])


def show_2d_plot():
    global data
    global buffer
    global dpg_ids
    global initialised_plots

    if buffer == -1:
        length_to_show = data.shape[-1]
    else:
        length_to_show = buffer

    assert len(data.shape) > 1, ('The Data provided to a Multi Pane Plot must be 2D')
    number_of_lines = data.shape[0]

    if not initialised_plots:
        for n in np.arange(number_of_lines):
            dpg_ids["Plot {}".format(n)] = \
                dpg.add_plot(label="Plot {}".format(n), height=int(800 / data.shape[0]), width=1030, show=True,
                             parent=dpg_ids['Visualisation'])
            dpg_ids['x_axis {}'.format(n)] = \
                dpg.add_plot_axis(dpg.mvXAxis, label='Data index', parent=dpg_ids["Plot {}".format(n)])
            dpg_ids['y_axis {}'.format(n)] = \
                dpg.add_plot_axis(dpg.mvYAxis, label='Data[{}]'.format(n), parent=dpg_ids["Plot {}".format(n)])
            dpg_ids['Plot line {}'.format(n)] = dpg.add_line_series(np.arange(length_to_show),
                                                                                data[n:length_to_show],
                                                                                parent=dpg_ids['y_axis {}'.format(n)])
        initialised_plots = True

    for n in np.arange(number_of_lines):
        dpg.set_value(dpg_ids['Plot line {}'.format(n)], [np.arange(length_to_show), data[n, :length_to_show]])


def update_dpg_gui():
    global visualiser_showing
    global visualisation_type
    global dpg_ids

    if visualiser_showing:
        try:
            if visualisation_type == 'Value':
                show_text_value()
            if visualisation_type == 'Single Pane Plot':
                show_1d_plot()
            if visualisation_type == 'Multi Pane Plot':
                show_2d_plot()
        except Exception as e:
            print(e)


def start_dpg():
    """
    The outside loop runs forever and blocks when the dpg.start_dearpygui() is called.
    When the plot_callback() calls dpg.stop_dearpygui() then it continues running forever until the
    visualisation_on turns on at which point the start_dearpygui is called again and this blocks
    :return: Nothing
    """
    global visualisation_type
    global visualiser_showing
    global is_dearpygui_running
    global dpg_ids
    global initialised_plots

    is_dearpygui_running = True
    initialised_plots = False

    dpg.create_context()
    dpg.create_viewport(title='Visualising', width=330, height=280)

    with dpg.window(label="Visualisation", show=True) as dpg_ids['Visualisation']:
        if visualisation_type == 'Value':
            dpg_ids['Text'] = dpg.add_text(default_value='__start__', label='Value')
            dpg.set_item_width(dpg_ids['Visualisation'], 300)
            dpg.set_item_height(dpg_ids['Visualisation'], 250)
        elif visualisation_type == 'Single Pane Plot':
            dpg.set_viewport_width(1050)
            dpg.set_viewport_height(770)
            dpg.set_item_width(dpg_ids['Visualisation'], 1050)
            dpg.set_item_height(dpg_ids['Visualisation'], 770)
            with dpg.plot(label="Plot", height=700, width=1000, show=True, pan_button=True,
                          fit_button=True) as dpg_ids['Plot 0']:
                dpg_ids['x_axis'] = dpg.add_plot_axis(dpg.mvXAxis, label="Data index")
                dpg_ids['y_axis'] = dpg.add_plot_axis(dpg.mvYAxis, label="Data")

        elif visualisation_type == 'Multi Pane Plot':
            dpg.set_viewport_width(1050)
            dpg.set_viewport_height(850)
            dpg.set_item_width(dpg_ids['Visualisation'], 1050)
            dpg.set_item_height(dpg_ids['Visualisation'], 820)

    dpg.set_viewport_resize_callback(on_resize_viewport)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    visualiser_showing = True
    if data is not None:
        update_dpg_gui()

    dpg.start_dearpygui()
    dpg.destroy_context()


def stop_dpg():
    global visualiser_showing
    global is_dearpygui_running

    dpg.stop_dearpygui()
    visualiser_showing = False
    is_dearpygui_running = False

print('hello')

def dpg_visualisation_thread():
    global visualisation_checking_thread_is_on
    global visualisation_on
    global is_dearpygui_running
    global worker_object

    visualisation_checking_thread_is_on = True

    while visualisation_checking_thread_is_on:
        visualisation_on = worker_object.parameters[0]

        if visualisation_on and not is_dearpygui_running:

            start_dpg_thread = threading.Thread(group=None, target=start_dpg, daemon=True)
            start_dpg_thread.start()

        if not visualisation_on and is_dearpygui_running:
            stop_dpg()

        gu.accurate_delay(10)

    stop_dpg()


def on_resize_viewport():

    width = dpg.get_viewport_width()
    height = dpg.get_viewport_height()

    dpg.set_item_width(dpg_ids['Visualisation'], width - 20)
    dpg.set_item_height(dpg_ids['Visualisation'], height - 40)

    series = 1
    if data is not None and len(data.shape) > 1 and visualisation_type == 'Multi Pane Plot':
        series = data.shape[0]

    height_divisor = 1
    if visualisation_type == 'Multi Pane Plot':
        height_divisor = series

    try:
        for n in np.arange(series):
            dpg.set_item_width(dpg_ids["Plot {}".format(n)], width - 40)
            dpg.set_item_height(dpg_ids["Plot {}".format(n)], int(height/height_divisor) - int(80/height_divisor))
    except:
        pass


def visualise(msg, parameters):
    global visualisation_type
    global visualisation_on
    global data

    message = msg[1:]  # data[0] is the topic
    data = Socket.reconstruct_array_from_bytes_message(message)

    if parameters is not None:
        visualisation_on = parameters[0]

        try:
            if visualisation_type == 'Image':
                show_image()

            elif visualisation_type == 'Value':
                update_dpg_gui()

            elif visualisation_type == 'Single Pane Plot':
                update_dpg_gui()

            elif visualisation_type == 'Multi Pane Plot':
                update_dpg_gui()

            elif visualisation_type == 'Histogram':
                pass

        except Exception as e:
            print(e)

    return [data]


def on_end_of_life():
    global visualisation_checking_thread_is_on

    visualisation_checking_thread_is_on = False


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(initialisation_function=get_vis_type_parameter,
                                                          work_function=visualise,
                                                          end_of_life_function=on_end_of_life)
    worker_object.start_ioloop()