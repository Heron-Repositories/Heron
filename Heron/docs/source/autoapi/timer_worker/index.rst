:py:mod:`timer_worker`
======================

.. py:module:: timer_worker


Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   timer_worker.constant
   timer_worker.uniform
   timer_worker.exponential
   timer_worker.trunc_exp_corrected
   timer_worker.gaussian
   timer_worker.initialise
   timer_worker.run_timer
   timer_worker.on_end_of_life



Attributes
~~~~~~~~~~

.. autoapisummary::

   timer_worker.current_dir
   timer_worker.current_dir
   timer_worker.running
   timer_worker.finish
   timer_worker.signal_out
   timer_worker.delay_generator
   timer_worker.a
   timer_worker.b
   timer_worker.c
   timer_worker.vis


.. py:data:: current_dir
   

   

.. py:data:: current_dir
   

   

.. py:data:: running
   :annotation: = False

   

.. py:data:: finish
   :annotation: = False

   

.. py:data:: signal_out
   :annotation: :str

   

.. py:data:: delay_generator
   :annotation: :str

   

.. py:data:: a
   :annotation: :float

   

.. py:data:: b
   :annotation: :float

   

.. py:data:: c
   :annotation: :float

   

.. py:data:: vis
   :annotation: :Heron.gui.visualisation_dpg.VisualisationDPG

   

.. py:function:: constant(a, b, c)


.. py:function:: uniform(a, b, c)


.. py:function:: exponential(a, b, c)


.. py:function:: trunc_exp_corrected(a, b, c)


.. py:function:: gaussian(a, b, c)


.. py:function:: initialise(_worker_object)


.. py:function:: run_timer(worker_object)


.. py:function:: on_end_of_life()


