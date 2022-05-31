:py:mod:`Heron.communication.transform_com`
===========================================

.. py:module:: Heron.communication.transform_com


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.communication.transform_com.TransformCom




.. py:class:: TransformCom(receiving_topics, sending_topics, parameters_topic, push_port, worker_exec, verbose=True, ssh_local_server_id='None', ssh_remote_server_id='None', outputs=None)

   .. py:method:: connect_sockets(self)

      Start the required sockets to communicate with the link forwarder and the worker_com processes
      :return: Nothing


   .. py:method:: define_verbosity_and_relic(self, verbosity_string)

      Splits the string that comes from the Node as verbosity_string into the string (or int) for the logging/printing
      (self.verbose) and the string that carries the path where the relic is to be saved. The self.relic is then
      passed to the worker process
      :param verbosity_string: The string with syntax verbosity||relic
      :return: (int)str vebrose, str relic


   .. py:method:: heartbeat_loop(self)

      The loop that send a 'PULSE' heartbeat to the worker_exec process to keep it alive (every ct.HEARTBEAT_RATE seconds)
      :return: Nothing


   .. py:method:: start_heartbeat_thread(self)

      The daemon thread that runs the infinite heartbeat_loop
      :return: Noting


   .. py:method:: start_worker(self)

      Starts the worker_exec process and then sends the parameters as are currently on the node to the process
      The pull_data_port of the worker_exec needs to be the push_data_port of the com (obviously).
      The way the arguments are structured is defined by the way they are read by the process. For that see
      general_utilities.parse_arguments_to_worker
      :return: Nothing


   .. py:method:: get_sub_data(self)

      Gets the link from the forwarder. It assumes that each message has four parts:
      The topic
      The data_index, an int that increases by one for every message the previous node sends
      The data_time, the time.perf_counter() result at the time the previous node send its message
      The messagedata, the array of link
      :return: Nothing


   .. py:method:: start_ioloop(self)

      Start the io loop for the transform node. It reads the link from the previous node's _com process,
      pushes it to the worker_com process,
      waits for the results,
      grabs the resulting link from the worker_com process and
      publishes the transformed link to the link forwarder with this nodes' topic
      :return: Nothing


   .. py:method:: on_kill(self, signal, frame)

      The function that is called when the parent process sends a SIGBREAK (windows) or SIGTERM (linux) signal.
      It needs signal and frame as parameters
      :param signal: The signal received
      :param frame: I haven't got a clue
      :return: Nothing



