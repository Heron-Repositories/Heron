:py:mod:`save_numpy_array_to_binary_worker`
===========================================

.. py:module:: save_numpy_array_to_binary_worker


Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   save_numpy_array_to_binary_worker.initialise
   save_numpy_array_to_binary_worker.add_timestamp_to_filename
   save_numpy_array_to_binary_worker.add_data_to_array
   save_numpy_array_to_binary_worker.save_array
   save_numpy_array_to_binary_worker.on_end_of_life



Attributes
~~~~~~~~~~

.. autoapisummary::

   save_numpy_array_to_binary_worker.current_dir
   save_numpy_array_to_binary_worker.current_dir
   save_numpy_array_to_binary_worker.need_parameters
   save_numpy_array_to_binary_worker.time_stamp
   save_numpy_array_to_binary_worker.expand
   save_numpy_array_to_binary_worker.on_axis
   save_numpy_array_to_binary_worker.disk_array
   save_numpy_array_to_binary_worker.file_name
   save_numpy_array_to_binary_worker.input_shape
   save_numpy_array_to_binary_worker.input_type
   save_numpy_array_to_binary_worker.output_type
   save_numpy_array_to_binary_worker.shape_step
   save_numpy_array_to_binary_worker.hdf5_file
   save_numpy_array_to_binary_worker.worker_object


.. py:data:: current_dir
   

   

.. py:data:: current_dir
   

   

.. py:data:: need_parameters
   :annotation: = True

   

.. py:data:: time_stamp
   :annotation: :bool

   

.. py:data:: expand
   :annotation: :bool

   

.. py:data:: on_axis
   :annotation: :int

   

.. py:data:: disk_array
   :annotation: :h5py.Dataset

   

.. py:data:: file_name
   :annotation: :str

   

.. py:data:: input_shape
   

   

.. py:data:: input_type
   :annotation: :type

   

.. py:data:: output_type
   :annotation: :str

   

.. py:data:: shape_step
   :annotation: :list

   

.. py:data:: hdf5_file
   :annotation: :h5py.File

   

.. py:function:: initialise(worker_object)


.. py:function:: add_timestamp_to_filename()


.. py:function:: add_data_to_array(data)


.. py:function:: save_array(data, parameters)


.. py:function:: on_end_of_life()


.. py:data:: worker_object
   

   

