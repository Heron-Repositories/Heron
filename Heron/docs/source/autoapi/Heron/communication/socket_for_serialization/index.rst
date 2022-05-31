:py:mod:`Heron.communication.socket_for_serialization`
======================================================

.. py:module:: Heron.communication.socket_for_serialization


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.communication.socket_for_serialization.Socket




.. py:class:: Socket(*a, **kw)

   Bases: :py:obj:`zmq.Socket`

   A ZeroMQ socket that allows sending and receiving numpy arrays through their pointers.
   This socket needs to be initialised by taking a context (not through context.Socket that ZeroMQ
   uses to initialise sockets)

   .. py:method:: send_array(self, array, flags=0, copy=True, track=False)

      Send a numpy array nthrough a series of messages
      :param array: The array
      :param flags: See zmq.Socket.send flags
      :param copy: If copy is True then the whole array is copied over. If False then only the array's memory pointer is send
      :param track:
      :return:


   .. py:method:: recv_array(self, flags=0, copy=True, track=False)

      Receive a numpy array
      :param flags: See zmq.Socket.recv flags
      :param copy: see the copy parameter of the zmq.Socket.recv()
      :param track: see the track parameter of the zmq.Socket.recv()
      :return:


   .. py:method:: switch_type_to_unsigned(type)
      :staticmethod:

      it returns the unsigned type
      :param type: the type to be switched to unsigned
      :return:


   .. py:method:: _reconstruct_array_from_bytes_message(msg, switch_to_unsigned=False)
      :staticmethod:

      Static method to reconstruct a message that represents a numpy array to that array
      :param msg: The message received from zmq
      :param switch_to_unsigned: If true then switch the arrays type to unsigned
      :return:


   .. py:method:: reconstruct_array_from_bytes_message(msg)
      :staticmethod:


   .. py:method:: reconstruct_array_from_bytes_message_cv2correction(msg)
      :staticmethod:

      OpenCV has a bug that cannot deal with images with signed types. This function turns the numpy
      array's type to unsigned to solve that problem
      :param msg: The message representing the numpy array received from zmq
      :return:



