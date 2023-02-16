:py:mod:`save_pandas_df_worker`
===============================

.. py:module:: save_pandas_df_worker


Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   save_pandas_df_worker.add_timestamp_to_filename
   save_pandas_df_worker.initialise
   save_pandas_df_worker.work_function
   save_pandas_df_worker.on_end_of_life



Attributes
~~~~~~~~~~

.. autoapisummary::

   save_pandas_df_worker.current_dir
   save_pandas_df_worker.current_dir
   save_pandas_df_worker.column_names_str
   save_pandas_df_worker.file_name
   save_pandas_df_worker.overwrite_file
   save_pandas_df_worker.vis
   save_pandas_df_worker.df
   save_pandas_df_worker.worker_object


.. py:data:: current_dir
   

   

.. py:data:: current_dir
   

   

.. py:data:: column_names_str
   :annotation: :str

   

.. py:data:: file_name
   :annotation: :str

   

.. py:data:: overwrite_file
   :annotation: :bool

   

.. py:data:: vis
   :annotation: :Heron.gui.visualisation.Visualisation

   

.. py:data:: df
   :annotation: :pandas.DataFrame

   

.. py:function:: add_timestamp_to_filename(save_file)


.. py:function:: initialise(_worker_object)


.. py:function:: work_function(data, parameters)


.. py:function:: on_end_of_life()


.. py:data:: worker_object
   

   

