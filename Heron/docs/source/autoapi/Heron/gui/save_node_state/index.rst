:py:mod:`Heron.gui.save_node_state`
===================================

.. py:module:: Heron.gui.save_node_state


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.gui.save_node_state.SaveNodeState



Functions
~~~~~~~~~

.. autoapisummary::

   Heron.gui.save_node_state.rearrange_pandasdf_columns



.. py:function:: rearrange_pandasdf_columns(df)

   Takes a pandas Dataframe with columns 'DateTime' and 'WorkerIndex' amongst others and places them at the front
   :param df: The pandas Dataframe
   :return: The column rearranged df


.. py:class:: SaveNodeState(path, node_name, node_index, num_of_iters=None)

   .. py:method:: create_the_pandasdf(self, type, **variables)

      :param type: Can be either 'Parameters' or 'Substate'
      :param parameters: the variables to be saved with their initial values. The variable names will become the
      column names
      :return: Nothing


   .. py:method:: save_current_df(self, type)

      :return: Nothing


   .. py:method:: update_the_parameters_pandasdf(self, parameters, worker_index)

      Updates the parameters_pandasdf of the SaveNodeState
      :param variables: a list with the variable values that define the Parameters (in the same order as defined in the
      create_the_pandasdf() function)
      :param worker_index: The index of the iteration of the worker
      :return: Nothing


   .. py:method:: update_the_substate_pandasdf(self, worker_index, **variables)

      Updates the Substate pandasdf of the SaveNodeState. It first checks to see if the Substate pandadf exist and if it
      doesn't it creates it. The update happens incrementally through the self.substate_pandasdf temporary
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


   .. py:method:: update_the_substate_pandasdf_thread(self, worker_index, variables)

      The thread spawned to do the relic substate update of the pandasdf as described in the
      update_the_substate_pandasdf function (which is calling this thread)
      :param worker_index: The index of the worker function iteration
      :param variables: The variables saved in the dataframe passed as a dict
      :return:


   .. py:method:: save_substate_at_death(self)



