:py:mod:`Heron.gui.node`
========================

.. py:module:: Heron.gui.node


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.gui.node.Node




.. py:class:: Node(name, parent)

   .. py:method:: get_attribute_order(self, type)


   .. py:method:: initialise_parameters_socket(self)


   .. py:method:: initialise_proof_of_life_socket(self)


   .. py:method:: remove_from_editor(self)


   .. py:method:: get_numbers_of_inputs_and_outputs(self)


   .. py:method:: get_corresponding_operation(self)


   .. py:method:: assign_default_parameters(self)


   .. py:method:: get_node_index(self)


   .. py:method:: add_topic_in(self, topic)


   .. py:method:: add_topic_out(self, topic)


   .. py:method:: remove_topic_in(self, topic)


   .. py:method:: remove_topic_out(self, topic)


   .. py:method:: update_parameters(self)


   .. py:method:: spawn_node_on_editor(self)


   .. py:method:: extra_input_window(self)


   .. py:method:: update_verbosity(self, sender, data)


   .. py:method:: get_ssh_server_names_and_ids(self)


   .. py:method:: update_ssh_combo_boxes(self)


   .. py:method:: assign_local_server(self, sender, data)


   .. py:method:: assign_remote_server(self, sender, data)


   .. py:method:: assign_worker_executable(self, sender, data)


   .. py:method:: start_com_process(self)


   .. py:method:: sending_parameters_multiple_times(self)


   .. py:method:: start_thread_to_send_parameters_multiple_times(self)


   .. py:method:: wait_for_proof_of_life(self)


   .. py:method:: stop_com_process(self)



