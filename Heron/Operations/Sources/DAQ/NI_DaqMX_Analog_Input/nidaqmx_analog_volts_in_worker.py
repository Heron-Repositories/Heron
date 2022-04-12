
# TODO: Waiting for dpg to correct the issue with closing down dpg in a thread (kills the process) to get this to work
# properly

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
import threading
from Heron import general_utils as gu
from Heron.Operations.Sources.DAQ.NI_DaqMX_Analog_Input import nidaqmx_analog_volts_in_com
from Heron.gui.visualisation import Visualisation
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
vis: Visualisation
dpg_is_running = False


def on_resize_viewport():
    """
    What happens when the user resizes the dpg plot when the visualisation parameter is on
    :return: Nothing
    """
    global channels
    num_of_channels = len(channels)

    width = dpg.get_viewport_width()
    height = dpg.get_viewport_height()

    dpg.set_item_width(dpg_ids['Visualisation'], width - 20)
    dpg.set_item_height(dpg_ids['Visualisation'], height-40)

    for n in channels:
        dpg.set_item_width(dpg_ids["Plot {}".format(n)], width - 20)
        dpg.set_item_height(dpg_ids["Plot {}".format(n)], int(height/num_of_channels) - int(80/num_of_channels))


def plot(data):
    """
    Plotting the new data on the visualisation dpg plot
    :param data: The data to be plotted
    :return: Nothing
    """
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


def check_to_plot():
    """
    This is called by the acquire function at every step of the infinite loop and plots the just acquired data
    if the Visualisation.visualisation_on switch is true
    :return: Nothing
    """
    global worker_object
    global vis
    global window_showing
    global channels
    global dpg_ids
    global buffer_size
    global visualisation_thread_on

    if visualisation_thread_on:
        if vis.visualisation_on and dpg_is_running:
            if not vis.window_showing:
                dpg.show_item(dpg_ids['Visualisation'])

                vis.window_showing = True
                for n in channels:
                    dpg.show_item(dpg_ids["Plot {}".format(n)])
                    dpg_ids['Series {}'.format(n)] = dpg.add_line_series(np.arange(buffer_size), np.arange(buffer_size),
                                                                        parent=dpg_ids['Voltage of {} / Volts'.format(n)])

            if vis.window_showing:
                try:
                    if len(channels) == 1:
                        plot([vis.visualised_data])
                    else:
                        plot(vis.visualised_data)
                except Exception as e:
                    print(e)


def check_to_kill_dpg():
    """
    This is called by the acquire function at every step of the infinite loop and checks is the
    Visualisation.visualisation_on switch has been turned off and then kills the dpg thread
    :return: Nothing
    """
    global visglobal
    global dpg_is_running

    if not vis.visualisation_on and dpg_is_running:
        vis.window_showing = False
        dpg.stop_dearpygui()
        dpg_is_running = False


def start_plotting_thread():
    """
    This is the dearpygui thread that creates the dpg windows.
    :return: Nothing
    """
    global channels
    global dpg_ids
    global worker_object
    global window_showing
    global visualisation_thread_on
    global dpg_is_running
    global vis

    if vis.visualisation_on:
        if not vis.window_showing:
            dpg.create_context()
            dpg.create_viewport(title='Visualising NIDAQ', width=820, height=780)
            with dpg.window(label="Visualisation", width=800, height=750, show=False) \
                    as dpg_ids['Visualisation']:
                for n in channels:
                    dpg_ids["Plot {}".format(n)] = \
                        dpg.add_plot(label="Plot {}".format(n), height=int(700/len(channels)), width=800, show=False)
                    dpg_ids['Time points'] = \
                        dpg.add_plot_axis(dpg.mvXAxis, label='Time points', parent=dpg_ids["Plot {}".format(n)])
                    dpg_ids['Voltage of {} / Volts'.format(n)] = \
                        dpg.add_plot_axis(dpg.mvYAxis, label='Voltage {}'.format(n), parent=dpg_ids["Plot {}".format(n)])
            dpg.set_viewport_resize_callback(on_resize_viewport)
            dpg.setup_dearpygui()
            dpg.show_viewport()
            visualisation_thread_on = True
            dpg_is_running = True
            dpg.start_dearpygui()
            dpg.destroy_context()


def start_visualisation_thread(vis_object):
    """
    This is the continuous loop that checks if it should start a dpg thread (start_plotting_thread())
    :param vis_object: The Visualisation object passed from the Visualisation class
    :return: Nothing
    """
    global channels
    global dpg_ids
    global worker_object
    global window_showing
    global visualisation_thread_on
    global dpg_is_running

    while True:
        if vis_object.visualisation_on and not dpg_is_running:
            plotting_thread = threading.Thread(group=None, target=start_plotting_thread)
            plotting_thread.start()
            while not dpg_is_running:
                gu.accurate_delay(10)
        else:
            gu.accurate_delay(10)


def acquire(_worker_object):
    """
    The work function running a setup and its infinite loop acquiring data and checking for plotting
    :param _worker_object:
    :return:
    """
    global acquiring_on
    global task
    global buffer_size
    global worker_object
    global channels
    global rate
    global sample_mode
    global vis
    global dpg_is_running

    worker_object = _worker_object

    vis = Visualisation(worker_object.node_name, worker_object.node_index)
    vis.set_new_visualisation_loop(start_visualisation_thread)
    vis.visualisation_init()

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
        vis.visualised_data = np.array(task.read(number_of_samples_per_channel=buffer_size))
        #worker_object.socket_push_data.send_array(vis.visualised_data, copy=False)
        worker_object.send_data_to_com(vis.visualised_data)

        try:
            vis.visualisation_on = worker_object.parameters[0]
        except:
            vis.visualisation_on = nidaqmx_analog_volts_in_com.ParametersDefaultValues[0]

        check_to_kill_dpg()
        check_to_plot()


def on_end_of_life():
    global task
    global figure
    global acquiring_on
    global vis

    acquiring_on = False
    try:
        vis.kill()

        task.stop()
        task.close()
        del task
        dpg.stop_dearpygui()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    gu.start_the_source_worker_process(acquire, on_end_of_life)