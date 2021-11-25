
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
import dearpygui.dearpygui as dpg
import nidaqmx
import cv2 as cv2
from Heron import general_utils as gu
from Heron.Operations.Sources.DAQ.NI_DaqMX_Analog_Input import nidaqmx_analog_volts_in_com
from Heron.communication.source_worker import SourceWorker

acquiring_on = False
buffer_size = 0
task: nidaqmx.Task
worker_object: SourceWorker
window_showing = False
channels: list
rate: int
sample_mode: int
dpg_ids = {}
visualisation_thread_on = False


def plot(data):
    global buffer_size
    global channels

    # updating plot data
    plot_datax = np.arange(buffer_size)
    plot_datay = np.array(data)
    try:
        for i, n in enumerate(channels):
            dpg.set_value(dpg_ids['Series {}'.format(n)], [plot_datax, list(plot_datay[i, :])])
    except Exception as e:
        print('Plotting exception: {}'.format(e))


def plot_callback():
    global worker_object
    global window_showing
    global channels
    global dpg_ids
    global buffer_size
    global visualisation_thread_on

    print('P1')
    print(worker_object.visualisation_on)
    if visualisation_thread_on:
        if worker_object.visualisation_on:
            print('P2')
            if not window_showing:
                print('P3')
                dpg.show_item(dpg_ids['Visualisation'])

                window_showing = True
                for n in channels:
                    dpg.show_item(dpg_ids["Plot {}".format(n)])
                    dpg_ids['Series {}'.format(n)] = dpg.add_line_series(np.arange(buffer_size), np.arange(buffer_size),
                                                                        parent=dpg_ids['Voltage of {} / Volts'.format(n)])

            if window_showing:
                try:
                    if len(channels) == 1:
                        plot([worker_object.worker_visualisable_result])
                    else:
                        plot(worker_object.worker_visualisable_result)
                except Exception as e:
                    print(e)

        if not worker_object.visualisation_on and visualisation_thread_on == True:
            print('P11')
            window_showing = False
            print('P12')
            dpg.minimize_viewport()
            print('P13')
            #dpg.stop_dearpygui()
            print('P14')


def start_plotting_thread():
    """
    The outside loop runs forever and blocks when the dpg.start_dearpygui() is called.
    When the plot_callback() calls dpg.stop_dearpygui() then it continues running forever until the
    worker_object.visualisation_on turns on at which point the start_dearpygui is called again and this blocks
    :return: Nothing
    """
    global channels
    global dpg_ids
    global worker_object
    global window_showing
    global visualisation_thread_on

    while True:
        if worker_object.visualisation_on:
            if not window_showing:
                dpg.create_context()
                dpg.create_viewport(title='Visualising NIDAQ', width=820, height=780)
                print('H1')
                with dpg.window(label="Visualisation", width=800, height=750, show=False) \
                        as dpg_ids['Visualisation']:
                    for n in channels:
                        dpg_ids["Plot {}".format(n)] = \
                            dpg.add_plot(label="Plot {}".format(n), height=int(700/len(channels)), width=800, show=False)
                        dpg_ids['Time points'] = \
                            dpg.add_plot_axis(dpg.mvXAxis, label='Time points', parent=dpg_ids["Plot {}".format(n)])
                        dpg_ids['Voltage of {} / Volts'.format(n)] = \
                            dpg.add_plot_axis(dpg.mvYAxis, label='Voltage {}'.format(n), parent=dpg_ids["Plot {}".format(n)])
                print('H2')
                dpg.set_viewport_resize_callback(on_resize_viewport)
                dpg.setup_dearpygui()
                dpg.show_viewport()
                visualisation_thread_on = True
                dpg.start_dearpygui()
                print('H3')
                dpg.destroy_context()


def on_resize_viewport():
    global channels
    num_of_channels = len(channels)

    width = dpg.get_viewport_width()
    height = dpg.get_viewport_height()

    dpg.set_item_width(dpg_ids['Visualisation'], width - 20)
    dpg.set_item_height(dpg_ids['Visualisation'], height-40)

    for n in channels:
        dpg.set_item_width(dpg_ids["Plot {}".format(n)], width - 20)
        dpg.set_item_height(dpg_ids["Plot {}".format(n)], int(height/num_of_channels) - int(80/num_of_channels))


def acquire(_worker_object):
    global acquiring_on
    global task
    global buffer_size
    global worker_object
    global channels
    global rate
    global sample_mode

    worker_object = _worker_object

    worker_object.set_new_visualisation_loop(start_plotting_thread)

    while not acquiring_on:
        try:
            channels = worker_object.parameters[1].split(' ')
            rate = int(worker_object.parameters[2])
            sample_mode = worker_object.parameters[3]
            buffer_size = int(worker_object.parameters[4])

            if sample_mode == 'CONTINUOUS':
                sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS
            elif sample_mode == 'FINITE':
                sample_mode = nidaqmx.constants.AcquisitionType.FINITE
            elif sample_mode == 'HW_TIMED_SINGLE_POINT':
                sample_mode = nidaqmx.constants.AcquisitionType.HW_TIMED_SINGLE_POINT

            acquiring_on = True
        except Exception as e:
            cv2.waitKey(10)

    task = nidaqmx.Task('Task {} {}'.format(worker_object.node_name, worker_object.node_index))
    for n in channels:
        task.ai_channels.add_ai_voltage_chan(n)
    task.timing.cfg_samp_clk_timing(rate=rate, sample_mode=sample_mode,
                                    samps_per_chan=buffer_size)
    task.start()

    while acquiring_on:
        worker_object.worker_visualisable_result = np.array(task.read(number_of_samples_per_channel=buffer_size))
        worker_object.socket_push_data.send_array(worker_object.worker_visualisable_result, copy=False)

        try:
            worker_object.visualisation_on = worker_object.parameters[0]
        except:
            worker_object.visualisation_on = nidaqmx_analog_volts_in_com.ParametersDefaultValues[0]

        worker_object.visualisation_loop_init()

        plot_callback()


def on_end_of_life():
    global task
    global figure
    global acquiring_on

    acquiring_on = False
    try:
        task.stop()
        task.close()
        del task
        dpg.stop_dearpygui()
        dpg.destroy_context()
        del dpg
    except Exception as e:
        print(e)


if __name__ == "__main__":
    gu.start_the_source_worker_process(acquire, on_end_of_life)