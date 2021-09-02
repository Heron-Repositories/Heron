
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
from Heron import general_utils as gu
from Heron.communication.transform_worker import TransformWorker

worker_object: TransformWorker
visualisation_on: bool
visualisation_type: str
buffer: int
window_name: str
visualiser_showing = False
data = None
dpg_ids = {}
channels: list
dpg_thread: threading.Thread


def get_vis_type_parameter(worker_object):
    global visualisation_type
    global visualisation_on
    global dpg_thread
    global buffer

    visualisation_on = worker_object.parameters[0]
    visualisation_type = worker_object.parameters[1]
    buffer = worker_object.parameters[2]

    if visualisation_type == 'Value':
        dpg_thread = threading.Thread(target=start_plotting_thread, daemon=True)
        dpg_thread.start()

    return True


def show_image():
    global visualisation_on
    global data
    global visualiser_showing
    global window_name

    if visualisation_on:
        if not visualiser_showing:
            window_name = 'Vis'
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


def plot():
    global buffer
    global channels
    global data

    # updating plot data
    plot_datax = np.arange(buffer)
    plot_datay = np.array(data)
    try:
        for i, n in enumerate(channels):
            dpg.set_value(dpg_ids['Series {}'.format(n)], [plot_datax, list(plot_datay[i, :])])
    except Exception as e:
        print('Plotting exception: {}'.format(e))


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


def update_dpg_gui():
    global visualisation_on
    global visualiser_showing
    global visualisation_type
    global dpg_ids

    if visualisation_on:
        if not visualiser_showing:

            dpg.show_item(dpg_ids['Visualisation'])

            visualiser_showing = True
            #for n in channels:
            #    dpg.show_item(dpg_ids["Plot {}".format(n)])
             #   dpg_ids['Series {}'.format(n)] = dpg.add_line_series(np.arange(buffer_size), np.arange(buffer_size),
              #                                                      parent=dpg_ids['Voltage of {} / Volts'.format(n)])

        if visualiser_showing:
            try:
                if visualisation_type == 'Value':
                    show_text_value()
                #if len(channels) == 1:
                #    plot([worker_object.worker_visualisable_result])
                #else:
                #   plot(worker_object.worker_visualisable_result)
            except Exception as e:
                print(e)

    if not visualisation_on:
        visualiser_showing = False
        dpg.stop_dearpygui()


def start_plotting_thread():
    """
    The outside loop runs forever and blocks when the dpg.start_dearpygui() is called.
    When the plot_callback() calls dpg.stop_dearpygui() then it continues running forever until the
    visualisation_on turns on at which point the start_dearpygui is called again and this blocks
    :return: Nothing
    """
    global visualisation_type
    global dpg_ids
    global visualiser_showing
    global visualisation_on

    while True:
        if visualisation_on:
            if not visualiser_showing:
                dpg_ids['Viewport'] = dpg.create_viewport(title='Visualising', width=330,
                                                          height=280)

                with dpg.window(label="Visualisation", width=300, height=250, show=False) \
                        as dpg_ids['Visualisation']:

                    if visualisation_type == 'Value':
                        dpg_ids['Text'] = dpg.add_text(default_value='__start__', label='Value')
                    elif visualisation_type == '1D Plot':
                        dpg.set_viewport_width(750)
                        dpg.set_viewport_height(850)
                        dpg.set_item_width(dpg_ids['Visualisation'], 730)
                        dpg.set_item_height(dpg_ids['Visualisation'], 820)
                        dpg_ids["Plot"] = \
                            dpg.add_plot(label="Plot", height=int(700), width=800, show=False)
                    elif visualisation_type == '2D Plot':
                        dpg.set_viewport_width(750)
                        dpg.set_viewport_height(850)
                        dpg.set_item_width(dpg_ids['Visualisation'], 730)
                        dpg.set_item_height(dpg_ids['Visualisation'], 820)
                        for n in channels:
                            dpg_ids["Plot {}".format(n)] = \
                                dpg.add_plot(label="Plot {}".format(n), height=int(700/len(channels)), width=800, show=False)
                            dpg_ids['Time points'] = \
                                dpg.add_plot_axis(dpg.mvXAxis, label='Time points', parent=dpg_ids["Plot {}".format(n)])
                            dpg_ids['Voltage of {} / Volts'.format(n)] = \
                                dpg.add_plot_axis(dpg.mvYAxis, label='Voltage {}'.format(n), parent=dpg_ids["Plot {}".format(n)])

                dpg.set_viewport_resize_callback(on_resize_viewport)
                dpg.setup_dearpygui(viewport=dpg_ids['Viewport'])
                dpg.show_viewport(dpg_ids['Viewport'])
                dpg.start_dearpygui()


def on_resize_viewport():
    #global channels
    #num_of_channels = len(channels)

    width = dpg.get_viewport_width()
    height = dpg.get_viewport_height()

    dpg.set_item_width(dpg_ids['Visualisation'], width - 20)
    dpg.set_item_height(dpg_ids['Visualisation'], height-40)

    #for n in channels:
        #dpg.set_item_width(dpg_ids["Plot {}".format(n)], width - 20)
        #dpg.set_item_height(dpg_ids["Plot {}".format(n)], int(height/num_of_channels) - int(80/num_of_channels))


def visualise(msg, parameters):
    global worker_object
    global visualisation_type
    global visualisation_on
    global data

    message = msg[1:]  # data[0] is the topic
    data = Socket.reconstruct_array_from_bytes_message_cv2correction(message)

    if parameters is not None:
        visualisation_on = parameters[0]

        try:
            if visualisation_type == 'Image':
                show_image()

            elif visualisation_type == 'Value':
                update_dpg_gui()

        except Exception as e:
            print(e)

    return [data]


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(initialisation_function=get_vis_type_parameter,
                                                          work_function=visualise,
                                                          end_of_life_function=on_end_of_life)
    worker_object.start_ioloop()
