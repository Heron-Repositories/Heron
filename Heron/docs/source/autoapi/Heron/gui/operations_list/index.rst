:py:mod:`Heron.gui.operations_list`
===================================

.. py:module:: Heron.gui.operations_list


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.gui.operations_list.Operation



Functions
~~~~~~~~~

.. autoapisummary::

   Heron.gui.operations_list.load_module
   Heron.gui.operations_list.generate_operations_list
   Heron.gui.operations_list.create_operation_from_dictionary



Attributes
~~~~~~~~~~

.. autoapisummary::

   Heron.gui.operations_list.root
   Heron.gui.operations_list.operations_list


.. py:data:: root
   

   

.. py:class:: Operation

   .. py:attribute:: name
      :annotation: :str

      

   .. py:attribute:: full_filename
      :annotation: :str

      

   .. py:attribute:: attributes
      :annotation: :list

      

   .. py:attribute:: attribute_types
      :annotation: :list

      

   .. py:attribute:: parameters
      :annotation: :list

      

   .. py:attribute:: parameter_types
      :annotation: :list

      

   .. py:attribute:: parameters_def_values
      :annotation: :list

      

   .. py:attribute:: executable
      :annotation: :str

      

   .. py:attribute:: parent_dir
      :annotation: :str

      

   .. py:attribute:: worker_exec
      :annotation: :str

      


.. py:data:: operations_list
   :annotation: = []

   

.. py:function:: load_module(path, name)


.. py:function:: generate_operations_list()


.. py:function:: create_operation_from_dictionary(op_dict)


