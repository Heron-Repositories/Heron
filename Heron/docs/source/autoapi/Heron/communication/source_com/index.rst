:py:mod:`Heron.communication.source_com`
========================================

.. py:module:: Heron.communication.source_com


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.communication.source_com.SourceCom




.. py:class:: SourceCom(sending_topics, parameters_topic, port, worker_exec, verbose='||', ssh_local_server_id='None', ssh_remote_server_id='None', outputs=None)

   .. py:method:: connect_sockets(self)

      Start the required sockets to communicate with the link forwarder and the source_com processes
      :return: Nothing


   .. py:method:: define_verbosity_and_relic(self, verbosity_string)

      Splits the string that comes from the Node as verbosity_string into the string (or int) for the logging/printing
      (self.verbose) and the string that carries the path where the relic is to be saved. The self.relic is then
      passed to the worker process
      :param verbosity_string: The string with syntax verbosity||relic
      :return: (int)str vebrose, str relic


   .. py:method:: on_receive_data_from_worker(self, msg)

      The callback that runs every time link is received from the worker_exec process. It takes the link and passes it
      onto the link forwarder
      :param msg: The link packet (carrying the actual link (np array))
      :return:


   .. py:method:: heartbeat_loop(self)

      Sending every ct.HEARTBEAT_RATE a 'PULSE' to the worker_exec so that it stays alive
      :return: Nothing


   .. py:method:: start_heartbeat_thread(self)

      Starts the daemon thread that runs the self.heartbeat loop
      :return: Nothing


   .. py:method:: start_worker_process(self)

      Starts the worker_exec process and then sends the parameters as are currently on the node to the process
      The pull_data_port of the worker_exec needs to be the push_data_port of the com (obviously).
      The way the arguments are structured is defined by the way they are read by the process. For that see
      general_utilities.parse_arguments_to_worker
      :return: Nothing


   .. py:method:: start_ioloop(self)

      Starts the ioloop of the zmqstream
      :return: Nothing


   .. py:method:: on_kill(self, signal, frame)

      The function that is called when the parent process sends a SIGBREAK (windows) or SIGTERM (linux) signal.
      It needs signal and frame as parameters
      :param signal: The signal received
      :param frame: I haven't got a clue
      :return: Nothing



