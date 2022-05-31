:py:mod:`Heron.gui.editor`
==========================

.. py:module:: Heron.gui.editor


Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   Heron.gui.editor.generate_node_tree
   Heron.gui.editor.on_add_node
   Heron.gui.editor.on_link
   Heron.gui.editor.delete_link
   Heron.gui.editor.start_forwarders_process
   Heron.gui.editor.on_start_graph
   Heron.gui.editor.on_end_graph
   Heron.gui.editor.on_del_pressed
   Heron.gui.editor.update_control_graph_buttons
   Heron.gui.editor.save_graph
   Heron.gui.editor.get_attribute_id_from_label
   Heron.gui.editor.load_graph
   Heron.gui.editor.clear_editor
   Heron.gui.editor.add_new_symbolic_link_node_folder
   Heron.gui.editor.view_operations_repos
   Heron.gui.editor.on_drag
   Heron.gui.editor.on_mouse_release
   Heron.gui.editor.create_node_selector_window



Attributes
~~~~~~~~~~

.. autoapisummary::

   Heron.gui.editor.operations_list
   Heron.gui.editor.heron_path
   Heron.gui.editor.last_used_port
   Heron.gui.editor.nodes_list
   Heron.gui.editor.links_dict
   Heron.gui.editor.panel_coordinates
   Heron.gui.editor.mouse_dragging_deltas
   Heron.gui.editor.forwarders
   Heron.gui.editor.node_selector
   Heron.gui.editor.port_generator
   Heron.gui.editor.default_font
   Heron.gui.editor.start_graph_button_id
   Heron.gui.editor.node_selector


.. py:data:: operations_list
   

   

.. py:data:: heron_path
   

   

.. py:data:: last_used_port
   :annotation: = 6000

   

.. py:data:: nodes_list
   :annotation: = []

   

.. py:data:: links_dict
   

   

.. py:data:: panel_coordinates
   :annotation: = [0, 0]

   

.. py:data:: mouse_dragging_deltas
   :annotation: = [0, 0]

   

.. py:data:: forwarders
   :annotation: :subprocess.Popen

   

.. py:data:: node_selector
   :annotation: :int

   

.. py:data:: port_generator
   

   

.. py:function:: generate_node_tree()

   The function that looks into the Heron/Operations path and creates a list of tuples of
   directories where the first element in the tuple is a dir and the second is
   its parent dir. All names for the dirs are generated (using ## to separate the different
   parts of the node_name) in such a way that can be used by dearpygui (i.e. they are
   unique and the first part before the first ## - which is the one that shows on a widget - is
   descriptive of the dir or the file).
   So one tuple would be ('Transforms##Operations##', 'Vision##Transforms##Operations##') which
   would mean that a dir called Vision (with real node_name Vision##Transforms##Operations##) has as
   its parent dir a dir called Transforms (with real node_name Transforms##Operations##). The list does not include
   the directories that house the actual code (each operation must have its own directory into which any
   python files must exist).
   The returned list can be used in a tree_node widget.
   :return: The list of tuples (parent dir, dir)


.. py:function:: on_add_node(sender, data)

   The callback that creates a Heron.gui.node.Node in the node editor for the operation defined by the button
   calling the callback.
   :param sender: The button's node_name
   :param data: Not used
   :return: Nothing


.. py:function:: on_link(sender, link)

   When a link is created it is stored as a topic_out in the node with the output and as a topic_in in the
   node with the input
   :param sender: The node editor (not used)
   :param link: The link list
   :return: Nothing


.. py:function:: delete_link(sender, link)

   Deletes a link and removes the topics (in and out) it represents from the corresponding nodes
   :param sender: Not used
   :param link: The id of the link item
   :return: Nothing


.. py:function:: start_forwarders_process(path_to_com)

   This initialises the two processes that run the two forwarders connecting the link flow between com and worker_exec
   processes and the parameters flow between the same processes
   :param path_to_com: The path that the two python files that define the processes are
   :return: Nothing


.. py:function:: on_start_graph(sender, data)

   The callback of the Start Graph button. It reads all the connections between the nodes and starts all the
   required processes assigning the correct topics and ports to each one of them so that the resulting
   communication between the processes resembles the node graph in the editor.
   :param sender: Not used
   :param data: Not used
   :return: Nothing


.. py:function:: on_end_graph(sender, data)

   Kill all running processes (except the one running the gui). Also shows a progress bar while waiting for processes
   to die. They need a ct.HEARTBEAT_RATE * ct.HEARTBEATS_TO_DEATH seconds to die.
   :param sender: Not used
   :param data: Not used
   :return: Nothing


.. py:function:: on_del_pressed(sender, key_value)


.. py:function:: update_control_graph_buttons(is_graph_running)

   Used to enable and disable (grey out) the Start Graph or the End Graph according to whether the Graph is running or
   not
   :param is_graph_running: Is the graph running bool
   :return: Nothing


.. py:function:: save_graph()

   Saves the current graph
   :return: Nothing


.. py:function:: get_attribute_id_from_label(label)


.. py:function:: load_graph()

   Loads a saved graph
   :return: Nothing


.. py:function:: clear_editor()

   Clear the editor of all nodes and links
   :return: Nothing


.. py:function:: add_new_symbolic_link_node_folder()


.. py:function:: view_operations_repos()


.. py:function:: on_drag(sender, data, user_data)

   When mouse is dragged and a node is selected then update that node's coordinates
   When mouse is dragged on the canvas with no node selected then move all nodes by the mouse movement and
   update their coordinates
   :param sender: Not used (the editor window)
   :param data: The mouse drag amount in x and y
   :param user_data: Not used
   :return: Nothing


.. py:function:: on_mouse_release(sender, app_data, user_data)


.. py:function:: create_node_selector_window()


.. py:data:: default_font
   

   

.. py:data:: start_graph_button_id
   

   

.. py:data:: node_selector
   

   

