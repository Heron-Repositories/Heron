:py:mod:`Heron.communication.sink_worker`
=========================================

.. py:module:: Heron.communication.sink_worker


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.communication.sink_worker.SinkWorker




.. py:class:: SinkWorker(recv_topics_buffer, pull_port, initialisation_function, work_function, end_of_life_function, parameters_topic, num_sending_topics, relic_path, ssh_local_ip=' ', ssh_local_username=' ', ssh_local_password=' ')

   .. py:method:: connect_sockets(self)

      Sets up the sockets to do the communication with the transform_com process through the forwarders
      (for the link and the parameters).
      :return: Nothing


   .. py:method:: data_callback(self, data)

      The callback that is called when link is send from the previous com process this com process is connected to
      (receives link from and shares a common topic) and pushes the link to the worker_exec.
      The link are a three zmq.Frame list. The first is the topic (used for the worker_exec to distinguish which input the
      link have come from in the case of multiple input nodes). The other two items are the details and the link load
      of the numpy array coming from the previous node). Once the work function returns the com process is notified
      with a ct.IGNORE signal
      :param data: The link received
      :return: Nothing


   .. py:method:: import_reliquery(self)

      This import is required because it takes a good few seconds to load the package and if the import is done
      first time in the HeronRelic instance that delays the initialisation of the worker process which can be
      a problem
      :return: Nothing


   .. py:method:: relic_create_parameters_df(self, **parameters)

      Creates a new relic with the Parameters pandasdf in it or adds the Parameters pandasdf in the existing Node's
      Relic.
      :param parameters: The dictionary of the parameters. The keys of the dict will become the column names of the
      pandasdf
      :return: Nothing


   .. py:method:: relic_create_substate_df(self, **variables)

      Creates a new relic with the Substate pandasdf in it or adds the Substate pandasdf in the existing Node's Relic.
      :param variables: The dictionary of the variables to save. The keys of the dict will become the column names of
      the pandasdf
      :return: Nothing


   .. py:method:: _relic_create_df(self, type, **variables)

      Base function to create either a Parameters or a Substate pandasdf in a new or the existing Node's Relic
      :param type: Parameters or Substate
      :param variables: The variables dictionary to be saved in the pandas. The keys of the dict will become the c
      olumn names of the pandasdf
      :return: Nothing


   .. py:method:: relic_update_substate_df(self, **variables)

      Updates the Substate pandasdf of the Node's Relic
      :param variables: The Substate's variables dict
      :return: Nothing


   .. py:method:: parameters_callback(self, parameters_in_bytes)

      The callback called when there is an update of the parameters (worker_exec function's parameters) from the node
      (send by the gui_com)
      :param parameters_in_bytes:
      :return:


   .. py:method:: heartbeat_callback(self, pulse)

      The callback called when the com sends a 'PULSE'. It registers the time the 'PULSE' has been received
      :param pulse: The pulse (message from the com's push) received
      :return:


   .. py:method:: heartbeat_loop(self)

      The loop that checks whether the latest 'PULSE' received from the com's heartbeat push is not too stale.
      If it is then the current process is killed
      :return: Nothing


   .. py:method:: proof_of_life(self)

      When the worker_exec process starts it sends to the gui_com (through the proof_of_life_forwarder thread) a signal
      that lets the node (in the gui_com process) that the worker_exec is running and ready to receive parameter updates.
      :return: Nothing


   .. py:method:: start_ioloop(self)

      Starts the heartbeat thread daemon and the ioloop of the zmqstreams
      :return: Nothing


   .. py:method:: on_kill(self, pid)



