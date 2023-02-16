:py:mod:`visualiser_worker_old`
===============================

.. py:module:: visualiser_worker_old


Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   visualiser_worker_old.get_vis_type_parameter
   visualiser_worker_old.show_image
   visualiser_worker_old.show_text_value
   visualiser_worker_old.show_1d_plot
   visualiser_worker_old.show_2d_plot
   visualiser_worker_old.update_dpg_gui
   visualiser_worker_old.start_dpg
   visualiser_worker_old.stop_dpg
   visualiser_worker_old.dpg_visualisation_thread
   visualiser_worker_old.on_resize_viewport
   visualiser_worker_old.visualise
   visualiser_worker_old.on_end_of_life



Attributes
~~~~~~~~~~

.. autoapisummary::

   visualiser_worker_old.current_dir
   visualiser_worker_old.current_dir
   visualiser_worker_old.visualisation_on
   visualiser_worker_old.is_dearpygui_running
   visualiser_worker_old.visualisation_type
   visualiser_worker_old.buffer
   visualiser_worker_old.window_name
   visualiser_worker_old.visualiser_showing
   visualiser_worker_old.data
   visualiser_worker_old.worker_object
   visualiser_worker_old.dpg_ids
   visualiser_worker_old.data_shape
   visualiser_worker_old.dpg_thread
   visualiser_worker_old.visualisation_checking_thread_is_on
   visualiser_worker_old.initialised_plots
   visualiser_worker_old.worker_object


.. py:data:: current_dir
   

   

.. py:data:: current_dir
   

   

.. py:data:: visualisation_on
   :annotation: :bool

   

.. py:data:: is_dearpygui_running
   :annotation: :bool

   

.. py:data:: visualisation_type
   :annotation: :str

   

.. py:data:: buffer
   :annotation: :int

   

.. py:data:: window_name
   :annotation: :str

   

.. py:data:: visualiser_showing
   :annotation: = False

   

.. py:data:: data
   

   

.. py:data:: worker_object
   :annotation: :Heron.communication.transform_worker.TransformWorker

   

.. py:data:: dpg_ids
   

   

.. py:data:: data_shape
   

   

.. py:data:: dpg_thread
   :annotation: :threading.Thread

   

.. py:data:: visualisation_checking_thread_is_on
   :annotation: = False

   

.. py:data:: initialised_plots
   :annotation: = False

   

.. py:function:: get_vis_type_parameter(_worker_object)


.. py:function:: show_image()


.. py:function:: show_text_value()


.. py:function:: show_1d_plot()


.. py:function:: show_2d_plot()


.. py:function:: update_dpg_gui()


.. py:function:: start_dpg()

   The outside loop runs forever and blocks when the dpg.start_dearpygui() is called.
   When the plot_callback() calls dpg.stop_dearpygui() then it continues running forever until the
   visualisation_on turns on at which point the start_dearpygui is called again and this blocks
   :return: Nothing


.. py:function:: stop_dpg()


.. py:function:: dpg_visualisation_thread()


.. py:function:: on_resize_viewport()


.. py:function:: visualise(msg, parameters)


.. py:function:: on_end_of_life()


.. py:data:: worker_object
   

   

