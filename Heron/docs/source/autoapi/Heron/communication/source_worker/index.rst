:py:mod:`Heron.communication.source_worker`
===========================================

.. py:module:: Heron.communication.source_worker


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.communication.source_worker.SourceWorker




.. py:class:: SourceWorker(port, parameters_topic, initialisation_function, end_of_life_function, num_sending_topics, savenodestate_path, ssh_local_ip=' ', ssh_local_username=' ', ssh_local_password=' ')

   .. py:method:: connect_socket(self)

      Sets up the sockets to do the communication with the source_com process through the forwarders
      (for the link and the parameters).
      :return: Nothing


   .. py:method:: send_data_to_com(self, data)


   .. py:method:: savenodestate_create_parameters_df(self, **parameters)

      Creates a new savenodestate with the Parameters pandasdf in it or adds the Parameters pandasdf in the existing Node's
      Relic.
      :param parameters: The dictionary of the parameters. The keys of the dict will become the column names of the
      pandasdf
      :return: Nothing


   .. py:method:: savenodestate_create_substate_df(self, **variables)

      Creates a new savenodestate with the Substate pandasdf in it or adds the Substate pandasdf in the existing Node's
      savenodestate.
      :param variables: The dictionary of the variables to save. The keys of the dict will become the column names of
      the pandasdf
      :return: Nothing


   .. py:method:: _savenodestate_create_df(self, type, **variables)

      Base function to create either a Parameters or a Substate pandasdf in a new or the existing Node's Relic
      :param type: Parameters or Substate
      :param variables: The variables dictionary to be saved in the pandas. The keys of the dict will become the c
      olumn names of the pandasdf
      :return: Nothing


   .. py:method:: savenodestate_update_substate_df(self, **variables)

      Updates the Substate pandasdf of the Node's Relic
      :param variables: The Substate's variables dict
      :return: Nothing


   .. py:method:: update_parameters(self)

      This updates the self.parameters from the parameters send form the node (through the gui_com)
      If the savenodestate system is up and running it also saves the new parameters into the Parameters df of the
      savenodestate.
      :return: Nothing


   .. py:method:: parameters_loop(self)

      The loop that updates the arguments (self.parameters)
      :return: Nothing


   .. py:method:: start_parameters_thread(self)

      Start the thread that runs the infinite arguments_loop
      :return: Nothing


   .. py:method:: heartbeat_loop(self)

      The loop that reads the heartbeat 'PULSE' from the source_com. If it takes too long to receive the new one
      it kills the worker_exec process
      :return: Nothing


   .. py:method:: proof_of_life(self)

      When the worker_exec process starts it sends to the gui_com (through the proof_of_life_forwarder thread) a signal
      that lets the node (in the gui_com process) that the worker_exec is running and ready to receive parameter updates.
      :return: Nothing


   .. py:method:: start_heartbeat_thread(self)

      Start the heartbeat thread that run the infinite heartbeat_loop
      :return: Nothing


   .. py:method:: on_kill(self, pid)



