
import zmq
import numpy as np
import ast
import time

class Socket(zmq.Socket):
    """
    A ZeroMQ socket that allows snding and receiving numpy arrays through their pointers.
    This socket needs to be initialised by taking a context (not through context.Socket that ZeroMQ
    uses to initialise sockets)
    """
    def __init__(self, *a, **kw):
        super().__init__(*a, *kw)

    def send_array(self, array, flags=0, copy=True, track=False):
        """
        Send a numpy array nthrough a series of messages
        :param array: The array
        :param flags: See zmq.Socket.send flags
        :param copy: If copy is True then the whole array is copied over. If False then only the array's memory pointer is send
        :param track:
        :return:
        """
        md = dict(dtype=str(array.dtype), shape=array.shape)
        self.send_json(md, flags|zmq.SNDMORE)
        return self.send(array, flags, copy=copy, track=track)

    def recv_array(self, flags=0, copy=True, track=False):
        """
        Receive a numpy array
        :param flags: See zmq.Socket.recv flags
        :param copy: see the copy parameter of the zmq.Socket.recv()
        :param track: see the track parameter of the zmq.Socket.recv()
        :return:
        """
        md = self.recv_json(flags=flags)
        msg = self.recv(flags=flags, copy=copy, track=track)
        buf = memoryview(msg)
        A = np.frombuffer(buf, dtype=md['dtype'])
        return A.reshape(md['shape'])

    @staticmethod
    def switch_type_to_unsigned(type):
        """
        it returns the unsigned type
        :param type: the type to be switched to unsigned
        :return:
        """
        if 'int' in type:
            if 'u' not in type:
                type = 'u' + type
        return type

    @staticmethod
    def _reconstruct_array_from_bytes_message(msg, switch_to_unsigned=False):
        """
        Static method to reconstruct a message that represents a numpy array to that array
        :param msg: The message received from zmq
        :param switch_to_unsigned: If true then switch the arrays type to unsigned
        :return:
        """
        md_bytes = msg[0]

        md_str = md_bytes.decode("UTF-8")
        md = ast.literal_eval(md_str)

        type = md['dtype']

        if switch_to_unsigned:
            type = Socket.switch_type_to_unsigned(type)

        data = msg[1]
        buf = memoryview(data)
        array = np.frombuffer(buf, dtype=type)

        return array.reshape(md['shape'])

    @staticmethod
    def reconstruct_array_from_bytes_message(msg):
        return Socket._reconstruct_array_from_bytes_message(msg, switch_to_unsigned=False)


    @staticmethod
    def reconstruct_array_from_bytes_message_cv2correction(msg):
        """
        OpenCV has a bug that cannot deal with images with signed types. This function turns the numpy
        array's type to unsigned to solve that problem
        :param msg: The message representing the numpy array received from zmq
        :return:
        """
        return Socket._reconstruct_array_from_bytes_message(msg, switch_to_unsigned=True)