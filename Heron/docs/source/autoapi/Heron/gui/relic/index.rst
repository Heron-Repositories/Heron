:py:mod:`Heron.gui.relic`
=========================

.. py:module:: Heron.gui.relic


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.gui.relic.HeronRelic



Functions
~~~~~~~~~

.. autoapisummary::

   Heron.gui.relic.create_storage_names
   Heron.gui.relic.rearrange_pandasdf_columns



.. py:function:: create_storage_names(relic_path)

   Creates the names for the storage and the relic given the path the relic needs to be saved in
   (which the user provides in the Node)
   :param relic_path: The path the relic is going to be saved in
   :return: The root of the FileStorage and the relic_type of the Relic


.. py:function:: rearrange_pandasdf_columns(df)

   Takes a pandas Dataframe with columns 'DateTime' and 'WorkerIndex' amongst others and places them at the front
   :param df: The pandas Dataframe
   :return: The column rearranged df


.. py:class:: HeronRelic(relic_path, node_name, node_index, num_of_iters=None)

   The class that deals with saving into Relics (using reliquery) of the parameters and any other variable defined
   in the worker script of a Node.

   .. py:method:: create_the_pandasdf(self, type, **variables)

      Creates the pandasdf that stores the variables in the appropriately named part of the relic (type). It also adds
      two columns at the beginning of the df named DateTime (where the datetime.now() is stored) and the WorkerIndex
      where the index of the worker function's iteration is stored.
      :param type: Can be either 'Parameters' or 'Substate'
      :param parameters: the variables to be saved with their initial values. The variable names will become the
      column names
      :return: Nothing


   .. py:method:: update_the_parameters_pandasdf(self, parameters, worker_index)

      Updates the Parameters pandasdf of the relic
      :param variables: a list with the variable values that define the Parameters (in the same order as defined in the
      create_the_pandasdf() function)
      :param worker_index: The index of the iteration of the worker
      :return: Nothing


   .. py:method:: update_the_substate_pandasdf(self, worker_index, **variables)

      Updates the Substate pandasdf of the relic. It first checks to see if the Substate pandadf exist and if it
      doesn't it creates it. The update happens incrementally through a self.temp_substate_pandasdf temporary
      dataframe which gets loaded and at a certain number of worker_function iterations it gets saved into the relic.
      This number can be either ct.NUMBER_OF_ITTERATIONS_BEFORE_RELIC_SUBSTATE_SAVE when the Node's worker function
      hasn't specified it in the xxx_worker.num_of_iters_to_update_relics_substate variable or that variable. If that
      variable has the value of -1 then the information never gets saved to the hard disk until the process is about
      to die at which point the whole pandas (which has been kept in RAM) gets dumped in one go to the HD.
      Nodes that struggle to keep up with their operations can use the later strategy to not take any time in loading
      and re-saving the pandasdf. But that means that if the Node crashes without calling the on_kill of the worker
      object then the pandas is lost.
      :param worker_index: The index of the worker function iteration
      :param kwarg_variables: The variables passed as multiple arguments with names (**kwargs style)
      :return: Nothing


   .. py:method:: save_current_substate_df(self)

      This grabs the relic's Substate pandasdf, concatenates it with the self.temp_substate_pandasdf df and saves
      everything back to the relic. This is done to avoid loading and saving at every iteration
      :return: Nothing


   .. py:method:: save_substate_at_death(self)

      This is required because it will be called by the on_kill function of the Worker objects. This function is a
      callback that is called by a different Thread to the rest of the object so it will not see the self.relic
      appropriately (it cannot write to the metadata). So at death a new relic is created and saves the remaining
      self.temp_substate_pandasdf in the relic's 'Substate' type
      :return: Nothing



