
import numpy as np
import dearpygui.dearpygui as dpg
import cv2
import threading
import pprint as pp
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu


class VisualisationDPG:

    def __init__(self, _node_name, _node_index, _visualisation_type='Image', _buffer=10, _image_size=None,
                 _x_axis_label=None, _y_axis_base_label=None, _base_plot_title=None):
        """
        The basic class for handling visualisations (using the dearpygui library for most of what it does).
        :param _node_name: The node's name (found in worker_object.node_name)
        :param _node_index: The node's index (found in worker_object.node_index)
        :param _visualisation_type: Can be 'Image', 'Value', 'Single Pane Plot', 'Multi Pane Plot'
        :param _buffer: The number of data points shown on a single visualisation window if the 'visualisation_type is not 'Image'
        :param _image_size: The size of an image if the _visualisation_type is 'Image'
        :param _x_axis_label: A string with the name of the x axis
        :param _y_axis_base_label: A string with the base name of the y axes for the Multi Pane or the name of the y
        axis for the Single Pane. In the Multi Pane the actual names will be numbered (_y_axis_base_label 0,
        _y_axis_base_label 1, etc.)
        :param _base_plot_title: A string giving the base name for each plot for Multi Pane, or the name of the plot for
        Single Pane. In the Multi Pane the actual plots will be numbered starting from 0
        """

        self.visualisation_on = False
        self.visualisation_type = _visualisation_type
        self.buffer = _buffer
        self.image_size = _image_size
        if _x_axis_label is None:
            self.x_axis_label = 'Data index'
        else:
            self.x_axis_label = _x_axis_label
        self.y_axis_label = _y_axis_base_label
        if _base_plot_title is None:
            self.plot_title = 'Plot'
        self.plot_title = _base_plot_title
        self.window_name = '{} {}'.format(_node_name, _node_index)

        self.visualiser_showing = False
        self.data = None

        self.dpg_ids = {}
        self.data_shape = None
        self.dpg_thread: threading.Thread
        self.visualisation_checking_thread_is_on = False
        self.initialised_plots = False

        self.is_dearpygui_running: bool
        
        if self.visualisation_type != 'Image':
            self.is_dearpygui_running = False
            self.dpg_thread = threading.Thread(target=self._dpg_visualisation_thread, daemon=True)
            self.dpg_thread.start()

    def _show_image(self):
        """
        If the visualisation should be on checks if a cv2 window is up (and puts one up if not) and then visualised
        the self.data as a picture
        :return: Nothing
        """
        if self.visualisation_on:
            if not self.visualiser_showing:
                cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
                try:
                    cv2.imshow(self.window_name, self.data)
                except Exception as e:
                    print(e)
                cv2.waitKey(1)
                self.visualiser_showing = True
            if self.visualiser_showing:
                if self.image_size is None:
                    width = cv2.getWindowImageRect(self.window_name)[2]
                    height = cv2.getWindowImageRect(self.window_name)[3]
                else:
                    width = self.image_size[0]
                    height = self.image_size[1]
                try:
                    image = cv2.resize(self.data, (width, height), interpolation=cv2.INTER_AREA)
                    cv2.imshow(self.window_name, image)
                    cv2.waitKey(1)
                except Exception as e:
                    print(e)
        else:
            cv2.destroyAllWindows()
            self.visualiser_showing = False
            cv2.waitKey(1)

    def _show_text_value(self):
        """
        Formats and puts the self.data on a Text DPG window
        :return: Nothning
        """
        if len(self.data) == 1:
            self.data_to_show = self.data[0]
            self.data_to_show = str(self.data_to_show)
            splitter = '\n'
        else:
            self.data_to_show = pp.pformat(self.data)
            splitter = '||\n'

        previous_txt_data = dpg.get_value(self.dpg_ids['Text'])

        previous_list_data = previous_txt_data.split(splitter)
        if len(previous_list_data) == self.buffer:
            previous_list_data.pop(0)

        new_txt_data = ''
        for i in previous_list_data:
            if i != '__start__':
                new_txt_data = new_txt_data + i + splitter
        new_txt_data = new_txt_data + self.data_to_show

        dpg.set_value(self.dpg_ids['Text'], new_txt_data)

    def _show_1d_plot(self):
        """
        Formats the self.data (assuming it is a 1D or 2D array) and puts them to a single plot window of a DPG window
        :return: Nothing
        """

        if self.buffer == -1 or self.buffer > self.data.shape[-1]:
            length_to_show = self.data.shape[-1]
        else:
            length_to_show = self.buffer

        if len(self.data.shape) > 1:
            number_of_lines = self.data.shape[0]
            if not self.initialised_plots:
                for n in np.arange(0, number_of_lines):
                    self.dpg_ids['Plot line {}'.format(n)] = dpg.add_line_series(np.arange(length_to_show).tolist(),
                                                                                 self.data[n, -length_to_show:],
                                                                                 parent=self.dpg_ids['y_axis'])
        else:
            number_of_lines = 1
            if not self.initialised_plots:
                for n in np.arange(0, number_of_lines):
                    self.dpg_ids['Plot line {}'.format(n)] = dpg.add_line_series(np.arange(length_to_show).tolist(),
                                                                                 self.data[-length_to_show:],
                                                                                 parent=self.dpg_ids['y_axis'])

            self.initialised_plots = True

        if number_of_lines > 1:
            for n in np.arange(number_of_lines):
                dpg.set_value(self.dpg_ids['Plot line {}'.format(n)], [np.arange(length_to_show), self.data[n, -length_to_show:]])
        else:
            dpg.set_value(self.dpg_ids['Plot line {}'.format(0)], [np.arange(length_to_show), self.data[-length_to_show:]])
        dpg.fit_axis_data(self.dpg_ids['x_axis'])

    def _show_2d_plot(self):
        """
        Checks if the self.data is a 2D array and then puts each row of the array on a separate plot window in a
        DPG window
        :return: Nothing
        """
        if self.buffer == -1 or self.buffer > self.data_shape[-1]:
            length_to_show = self.data.shape[-1]
        else:
            length_to_show = self.buffer

        assert len(self.data.shape) > 1, 'The Data provided to a Multi Pane Plot must be 2D'
        number_of_lines = self.data.shape[0]

        if not self.initialised_plots:

            if self.y_axis_label is None:
                self.y_axis_label = 'Data'
            y_axis_labels = [self.y_axis_label + '[{}]'.format(i) for i in np.arange(number_of_lines)]

            if self.plot_title is None:
                self.plot_title = 'Plot'
            plot_title = [self.plot_title + " {}".format(k) for k in np.arange(number_of_lines)]

            for n in np.arange(number_of_lines):
                self.dpg_ids[plot_title[n]] = \
                    dpg.add_plot(label=plot_title[n], height=int(800 / self.data.shape[0]), width=1030, show=True,
                                 parent=self.dpg_ids['Visualisation'])

                self.dpg_ids['x_axis {}'.format(n)] = \
                    dpg.add_plot_axis(dpg.mvXAxis, label=self.x_axis_label, parent=self.dpg_ids[plot_title[n]])

                self.dpg_ids['y_axis {}'.format(n)] = \
                    dpg.add_plot_axis(dpg.mvYAxis, label=y_axis_labels[n], parent=self.dpg_ids[plot_title[n]])

                self.dpg_ids['Plot line {}'.format(n)] = dpg.add_line_series(np.arange(length_to_show),
                                                                             self.data[n, -length_to_show:],
                                                                             parent=self.dpg_ids['y_axis {}'.format(n)])
            self.initialised_plots = True

        for n in np.arange(number_of_lines):
            dpg.set_value(self.dpg_ids['Plot line {}'.format(n)], [np.arange(length_to_show), self.data[n, -length_to_show:]])

    def _update_dpg_gui(self):
        """
        Used to call for an update to the DPG window
        :return: Nothing
        """
        if self.visualiser_showing:
            try:
                if self.visualisation_type == 'Value':
                    self._show_text_value()
                if self.visualisation_type == 'Single Pane Plot':
                    self._show_1d_plot()
                if self.visualisation_type == 'Multi Pane Plot':
                    print('UPDATE 2D')
                    self._show_2d_plot()
            except Exception as e:
                print(e)

    def _start_dpg(self):
        """
        The main DPG loop
        The outside loop runs forever and blocks when the dpg.start_dearpygui() is called.
        When the plot_callback() calls dpg.stop_dearpygui() then it continues running forever until the
        self.visualisation_on turns on at which point the start_dearpygui is called again and this blocks
        :return: Nothing
        """

        self.is_dearpygui_running = True
        self.initialised_plots = False

        dpg.create_context()
        dpg.create_viewport(title='Visualiser', width=330, height=280)

        with dpg.window(label=self.window_name, show=True) as self.dpg_ids['Visualisation']:
            if self.visualisation_type == 'Value':
                self.dpg_ids['Text'] = dpg.add_text(default_value='__start__', label='Value')
                dpg.set_item_width(self.dpg_ids['Visualisation'], 300)
                dpg.set_item_height(self.dpg_ids['Visualisation'], 250)
            elif self.visualisation_type == 'Single Pane Plot':
                dpg.set_viewport_width(1050)
                dpg.set_viewport_height(770)
                dpg.set_item_width(self.dpg_ids['Visualisation'], 1050)
                dpg.set_item_height(self.dpg_ids['Visualisation'], 770)

                if self.y_axis_label is None:
                    self.y_axis_label = 'Data'
                y_axis_label = self.y_axis_label

                with dpg.plot(label=self.plot_title, height=700, width=1000, show=True, pan_button=True,
                              fit_button=True) as self.dpg_ids['Plot 0']:
                    self.dpg_ids['x_axis'] = dpg.add_plot_axis(dpg.mvXAxis, label=self.x_axis_label)
                    self.dpg_ids['y_axis'] = dpg.add_plot_axis(dpg.mvYAxis, label=y_axis_label)

            elif self.visualisation_type == 'Multi Pane Plot':
                dpg.set_viewport_width(1050)
                dpg.set_viewport_height(850)
                dpg.set_item_width(self.dpg_ids['Visualisation'], 1050)
                dpg.set_item_height(self.dpg_ids['Visualisation'], 820)

        dpg.set_viewport_resize_callback(self._on_resize_viewport)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        self.visualiser_showing = True
        if self.data is not None:
            self._update_dpg_gui()

        dpg.start_dearpygui()
        dpg.destroy_context()

    def _stop_dpg(self):
        """
        Stops the DPG loop
        :return: Nothing
        """
        dpg.stop_dearpygui()
        self.visualiser_showing = False
        self.is_dearpygui_running = False

    def _dpg_visualisation_thread(self):
        """
        Starts the DPG loop in its own thread
        :return: Noting
        """
        self.visualisation_checking_thread_is_on = True

        while self.visualisation_checking_thread_is_on:
            if self.visualisation_on and not self.is_dearpygui_running:

                start_dpg_thread = threading.Thread(group=None, target=self._start_dpg, daemon=True)
                start_dpg_thread.start()

            if not self.visualisation_on and self.is_dearpygui_running:
                self._stop_dpg()

            gu.accurate_delay(10)

        self._stop_dpg()

    def _on_resize_viewport(self):
        """
        A callback called when the user resizes the DPG viewport and mainly deals with the sizes of the subplots in the
        Multi Pane Plot.
        :return: Nothing
        """
        width = dpg.get_viewport_width()
        height = dpg.get_viewport_height()

        dpg.set_item_width(self.dpg_ids['Visualisation'], width - 20)
        dpg.set_item_height(self.dpg_ids['Visualisation'], height - 40)

        series = 1
        if self.data is not None and len(self.data.shape) > 1 and self.visualisation_type == 'Multi Pane Plot':
            series = self.data.shape[0]

        height_divisor = 1
        if self.visualisation_type == 'Multi Pane Plot':
            height_divisor = series

        try:
            for n in np.arange(series):
                dpg.set_item_width(self.dpg_ids["Plot {}".format(n)], width - 40)
                dpg.set_item_height(self.dpg_ids["Plot {}".format(n)], int(height/height_divisor) - int(80/height_divisor))
        except:
            pass

    def visualise(self, data):
        '''
        The function to call to actually do the update of the data on the visualisation window
        :param data: The new data to visualise
        :return:
        '''
        self.data = data

        try:
            if self.visualisation_type == 'Image':
                self._show_image()

            elif self.visualisation_type == 'Value':
                self._update_dpg_gui()

            elif self.visualisation_type == 'Single Pane Plot':
                self._update_dpg_gui()

            elif self.visualisation_type == 'Multi Pane Plot':
                self._update_dpg_gui()

            elif self.visualisation_type == 'Histogram':
                pass

        except Exception as e:
            print(e)

    def end_of_life(self):
        """
        This should be called at the end_of_life of a worker script to properly close the DPG loop or the cv2 loop
        :return: Nothing
        """
        self.visualisation_checking_thread_is_on = False