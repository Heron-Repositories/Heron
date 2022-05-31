:py:mod:`Heron.general_utils`
=============================

.. py:module:: Heron.general_utils


Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   Heron.general_utils.convertToNumber
   Heron.general_utils.convertFromNumber
   Heron.general_utils.full_split_path
   Heron.general_utils.float_to_binary
   Heron.general_utils.binary_to_float
   Heron.general_utils.accurate_delay
   Heron.general_utils.choose_color_according_to_operations_type
   Heron.general_utils.get_next_available_port_group
   Heron.general_utils.add_heron_to_pythonpath
   Heron.general_utils.register_exit_signals
   Heron.general_utils.setup_logger
   Heron.general_utils.add_timestamp_to_filename
   Heron.general_utils.parse_arguments_to_com
   Heron.general_utils.parse_arguments_to_worker
   Heron.general_utils.start_the_source_communications_process
   Heron.general_utils.start_the_source_worker_process
   Heron.general_utils.start_the_transform_communications_process
   Heron.general_utils.start_the_transform_worker_process
   Heron.general_utils.start_the_sink_communications_process
   Heron.general_utils.start_the_sink_worker_process



.. py:function:: convertToNumber(s)


.. py:function:: convertFromNumber(n)


.. py:function:: full_split_path(path)

   Splits a path to its constituent folders and returns a list of all of the folders
   :param path: The path string
   :return: The list of strings of folders


.. py:function:: float_to_binary(num)


.. py:function:: binary_to_float(binary)


.. py:function:: accurate_delay(delay)

   Function to provide accurate time delay in millisecond
   :param delay: Delay in milliseconds
   :return: Nothing


.. py:function:: choose_color_according_to_operations_type(operations_parent_name)

   Returns a colour to colour the operations list in the gui according to the type they belong to
   :param operations_parent_name: Name of operation (it included the type)
   :return: The colour


.. py:function:: get_next_available_port_group(starting_port, step)

   A generator that creates the next port jumping over ports at a step of ct.MAXIMUM_RESERVED_SOCKETS_PER_NODE
   :return: A new int +step larger than the previous one returned


.. py:function:: add_heron_to_pythonpath()


.. py:function:: register_exit_signals(function_to_register)

   In windows it registers a function to the SIGBREAK signal, while in linux to the SIGTERM signal
   :param function_to_register: The function to register
   :return: Nothing


.. py:function:: setup_logger(name, log_file, level=logging.DEBUG)


.. py:function:: add_timestamp_to_filename(file_name, datetime)


.. py:function:: parse_arguments_to_com(args)

   Turns the list of argv arguments that is send to a com process (by the editor) into appropriate list of strings
   and lists (of topics). It is up to the node's start_exec function to create a list of argv that can be properly
   parsed.
   :param args: The argv returned by the sys.argv
   :return: port = the initial port for the com process,
   receiving_topics = a list of the names of the topics the process receives (inputs) link at
   sending_topics = a list of the names of the topics the process sends (outputs) link at
   parameters_topic = the node_name of the topic the process receives parameter updates from the node
   verbose = Whether to print out comments while running
   ssh_local_server = The ID of the local ssh server (see ssh_info.json) if the node is to run its worker_exec over ssh
   ssh_remote_server = The ID of the remote ssh server (see ssh_info.json) if the node is to run its worker_exec over ssh
   worker_exec = The python script (or executable) of the worker_exec process


.. py:function:: parse_arguments_to_worker(args)

   Turns the list of argv arguments that is send to a com process (by the editor) into appropriate list of strings
   and lists (of topics). It is up to the com's start_worker function (in the *Com.start_worker functions) to create a
   list of argv that can be properly parsed.
   :param args: The argv returned by the sys.argv
   :return: port = the initial port for the worker_exec process,
   parameters_topic = the node_name of the topic the process receives parameter updates from the node
   receiving_topics = a list of the names of the topics the process receives (inputs) link at
   verbose = the verbosity of the worker_exec process (True or False)
   ssh_local_ip =
   ssh_local_username =
   ssh_local_password =


.. py:function:: start_the_source_communications_process(node_attribute_type, node_attribute_names)

   Creates a SourceCom object for a source process
   (i.e. initialises the worker_exec process and keeps the zmq communication between the worker_exec and the forwarders)
   :return: The SourceCom object


.. py:function:: start_the_source_worker_process(work_function, end_of_life_function, initialisation_function=None)

   Creates a SourceWorker for a worker_exec process of a Source
   :param work_function:
   :return:


.. py:function:: start_the_transform_communications_process(node_attribute_type, node_attribute_names)

   Creates a TransformCom object for a transformation process
   (i.e. initialises the worker_exec process and keeps the zmq communication between the worker_exec
   and the forwarder)
   :return: The TransformCom object


.. py:function:: start_the_transform_worker_process(work_function, end_of_life_function, initialisation_function=None)

   Starts the _worker process of the Transform that grabs link from the _com process, does something with them
   and sends them back to the _com process. It also grabs any updates of the parameters of the worker_exec function
   :return: The TransformWorker object


.. py:function:: start_the_sink_communications_process()

   Creates a Sink object for a sink process
   (i.e. initialises the worker_exec process and keeps the zmq communication between the worker_exec
   and the forwarder)
   :return: The SinkCom object


.. py:function:: start_the_sink_worker_process(work_function, end_of_life_function, initialisation_function=None)

   Starts the _worker process of the Sink that grabs link from the _com process, does something with them
   and sends them back to the _com process. It also grabs any updates of the parameters of the worker_exec function
   :return: The SinkWorker object


