:py:mod:`Heron.gui.visualisation_dpg`
=====================================

.. py:module:: Heron.gui.visualisation_dpg


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.gui.visualisation_dpg.VisualisationDPG




.. py:class:: VisualisationDPG(_node_name, _node_index, _visualisation_type='Image', _buffer=10, _image_size=None, _x_axis_label=None, _y_axis_base_label=None, _base_plot_title=None)

   .. py:method:: _show_image(self)

      If the visualisation should be on checks if a cv2 window is up (and puts one up if not) and then visualised
      the self.data as a picture
      :return: Nothing


   .. py:method:: _show_text_value(self)

      Formats and puts the self.data on a Text DPG window
      :return: Nothning


   .. py:method:: _show_1d_plot(self)

      Formats the self.data (assuming it is a 1D or 2D array) and puts them to a single plot window of a DPG window
      :return: Nothing


   .. py:method:: _show_2d_plot(self)

      Checks if the self.data is a 2D array and then puts each row of the array on a separate plot window in a
      DPG window
      :return: Nothing


   .. py:method:: _update_dpg_gui(self)

      Used to call for an update to the DPG window
      :return: Nothing


   .. py:method:: _start_dpg(self)

      The main DPG loop
      The outside loop runs forever and blocks when the dpg.start_dearpygui() is called.
      When the plot_callback() calls dpg.stop_dearpygui() then it continues running forever until the
      self.visualisation_on turns on at which point the start_dearpygui is called again and this blocks
      :return: Nothing


   .. py:method:: _stop_dpg(self)

      Stops the DPG loop
      :return: Nothing


   .. py:method:: _dpg_visualisation_thread(self)

      Starts the DPG loop in its own thread
      :return: Noting


   .. py:method:: _on_resize_viewport(self)

      A callback called when the user resizes the DPG viewport and mainly deals with the sizes of the subplots in the
      Multi Pane Plot.
      :return: Nothing


   .. py:method:: visualise(self, data)

      The function to call to actually do the update of the data on the visualisation window
      :param data: The new data to visualise
      :return:


   .. py:method:: end_of_life(self)

      This should be called at the end_of_life of a worker script to properly close the DPG loop or the cv2 loop
      :return: Nothing



