:py:mod:`Heron.gui.ssh_info_editor`
===================================

.. py:module:: Heron.gui.ssh_info_editor


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.gui.ssh_info_editor.Table



Functions
~~~~~~~~~

.. autoapisummary::

   Heron.gui.ssh_info_editor.set_parent_id
   Heron.gui.ssh_info_editor.edit_ssh_info
   Heron.gui.ssh_info_editor.add_ssh_server_row
   Heron.gui.ssh_info_editor.remove_ssh_server_rows
   Heron.gui.ssh_info_editor.on_close



Attributes
~~~~~~~~~~

.. autoapisummary::

   Heron.gui.ssh_info_editor.ssh_table
   Heron.gui.ssh_info_editor.parent_id


.. py:class:: Table(name, header = None, parent_id = 0)

   .. py:method:: add_header(self, header)


   .. py:method:: add_row(self, row_content)


   .. py:method:: delete_selected_rows(self)


   .. py:method:: get_cell_data(self, row, col)


   .. py:method:: get_row_data(self, row)

      Return a row as a dict with keys the names of the columns
      :param row: The row to be retrieved
      :return: A dict of the row data


   .. py:method:: populate_from_json(self)


   .. py:method:: save_to_json(self)


   .. py:method:: on_edit(self, item, data)



.. py:data:: ssh_table
   :annotation: :Table

   

.. py:data:: parent_id
   :annotation: :int

   

.. py:function:: set_parent_id(_parent_id)


.. py:function:: edit_ssh_info()


.. py:function:: add_ssh_server_row()


.. py:function:: remove_ssh_server_rows()


.. py:function:: on_close()


