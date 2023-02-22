:py:mod:`key_press_worker`
==========================

.. py:module:: key_press_worker


Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   key_press_worker.on_key_pressed
   key_press_worker.on_key_released
   key_press_worker.visualisation_to_stdout
   key_press_worker.start_key_press_capture
   key_press_worker.on_end_of_life



Attributes
~~~~~~~~~~

.. autoapisummary::

   key_press_worker.current_dir
   key_press_worker.current_dir
   key_press_worker.worker_object
   key_press_worker.listener
   key_press_worker.key_pressed_and_released
   key_press_worker.previous_user_input
   key_press_worker.loop_on
   key_press_worker.new_input_for_vis
   key_press_worker.vis


.. py:data:: current_dir
   

   

.. py:data:: current_dir
   

   

.. py:data:: worker_object
   :annotation: :Heron.communication.source_worker.SourceWorker

   

.. py:data:: listener
   :annotation: :pynput.keyboard.Listener

   

.. py:data:: key_pressed_and_released
   :annotation: = [None, None]

   

.. py:data:: previous_user_input
   :annotation: = False

   

.. py:data:: loop_on
   :annotation: = True

   

.. py:data:: new_input_for_vis
   :annotation: = 

   

.. py:data:: vis
   :annotation: :Heron.gui.visualisation_dpg.VisualisationDPG

   

.. py:function:: on_key_pressed(key)


.. py:function:: on_key_released(key)


.. py:function:: visualisation_to_stdout(vis_object)


.. py:function:: start_key_press_capture(_worker_object)


.. py:function:: on_end_of_life()


