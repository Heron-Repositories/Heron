:py:mod:`Heron.gui.visualisation`
=================================

.. py:module:: Heron.gui.visualisation


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.gui.visualisation.Visualisation




.. py:class:: Visualisation(node_name, node_index)

   .. py:method:: set_new_visualisation_loop(self, new_visualisation_loop)

      If a specific source_worker needs to do something else regarding visualisation then it needs to implement a
      visualisation loop function and pass it here by giving it as an argument to this function
      :param new_visualisation_loop: The new function that will deal with the node's visualisation
      :return: Nothing


   .. py:method:: visualisation_loop(vis_object)
      :staticmethod:

      When the visualisation parameter in a node is set to True then this loop starts in a new visualisation thread.
      The thread terminates when the visualisation_on boolean is turned off. Because this is a static method it can
      be overridden by another loop from an xxx_worker script using the set_new_visualisation_loop
      :return: Nothing


   .. py:method:: visualisation_loop_update(self)

      The function that is run at every cycle of the WORKER_FUNCTION to check if the visualisation_on bool is True
      for the first time. When that happens it starts the visualisation loop. The loop takes care of the showing
      and hiding of the visualisation window.
      :return: Nothing


   .. py:method:: visualisation_init(self)


   .. py:method:: kill(self)



