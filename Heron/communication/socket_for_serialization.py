
import zmq
import numpy as np
import ast
import json
from Heron import decorators as dec


class Socket(zmq.Socket):
    """
    A ZeroMQ socket that allows sending and receiving numpy arrays through their pointers.
    This socket needs to be initialised by taking a context (not through context.Socket that ZeroMQ
    uses to initialise sockets)
    """
    def __init__(self, *a, **kw):
        super().__init__(*a, *kw)

    def send_data(self, data, flags=0, copy=True, track=False):
        if type(data) == np.ndarray:
            self._send_array(data, flags=flags, copy=copy, track=track)
        if type(data) == dict:
            self._send_dict(data, flags=flags)

    def _send_array(self, array, flags=0, copy=True, track=False):
        """
        Send a numpy array through a series of messages
        :param array: The array
        :param flags: See zmq.Socket.send flags
        :param copy: If copy is True then the whole array is copied over. If False then only the array's memory pointer is send
        :param track:
        :return:
        """
        md = dict(data_type='ndarray', dtype=str(array.dtype), shape=array.shape)
        self.send_json(md, flags | zmq.SNDMORE)
        return self.send(array, flags, copy=copy, track=track)

    def _send_dict(self, dictionary, flags=0):
        """
        Send a dictionary through a series of messages
        :param dictionary: The dictionary
        :param flags: See zmq.Socket.send flags
        :param copy: If copy is True then the whole array is copied over. If False then only the array's memory pointer is send
        :param track:
        :return:
        """
        md = dict(data_type='dict')
        self.send_json(md, flags | zmq.SNDMORE)
        return self.send_json(dictionary, flags)

    def recv_data(self, flags=0, copy=True, track=False):
        md = self.recv_json(flags=flags)
        type = md['data_type']
        if type == 'ndarray':
            return self._recv_array(md=md, flags=flags, copy=copy, track=track)
        if type == 'dict':
            return self._recv_dict(flags=flags)

    def _recv_array(self, md, flags=0, copy=True, track=False):
        """
        Receive a numpy array
        :param flags: See zmq.Socket.recv flags
        :param copy: see the copy parameter of the zmq.Socket.recv()
        :param track: see the track parameter of the zmq.Socket.recv()
        :return:
        """
        msg = self.recv(flags=flags, copy=copy, track=track)
        buf = memoryview(msg)
        A = np.frombuffer(buf, dtype=md['dtype'])
        result = A.reshape(md['shape'])
        return result

    def _recv_dict(self, flags=0):
        """
        Receive a dictionary
        :param flags: See zmq.Socket.recv flags
        :param copy: see the copy parameter of the zmq.Socket.recv()
        :param track: see the track parameter of the zmq.Socket.recv()
        :return:
        """
        return self.recv_json(flags=flags)

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
    def reconstruct_data_from_bytes_message(msg):

        md_bytes = msg[0]

        md_str = md_bytes.decode("UTF-8")
        md = ast.literal_eval(md_str)

        data_type = md['data_type']
        if data_type == 'ndarray':
            dtype = md['dtype']
            shape = md['shape']
            return Socket._reconstruct_array_from_bytes_message(msg, dtype=dtype, shape=shape, switch_to_unsigned=False)

        if data_type == 'dict':
            return Socket._reconstruct_dict_from_bytes_message(msg)

    @staticmethod
    def _reconstruct_array_from_bytes_message(msg, dtype, shape, switch_to_unsigned=False):
        """
        Static method to reconstruct a message that represents a numpy array to that array
        :param msg: The message received from zmq
        :param switch_to_unsigned: If true then switch the arrays type to unsigned
        :return:
        """
        if switch_to_unsigned:
            dtype = Socket.switch_type_to_unsigned(dtype)

        data = msg[1]
        buf = memoryview(data)
        array = np.frombuffer(buf, dtype=dtype)

        return array.reshape(shape)

    @staticmethod
    def _reconstruct_dict_from_bytes_message(msg):
        data_bytes = msg[1]
        data = json.loads(data_bytes)
        return data

    @staticmethod
    def reconstruct_array_from_bytes_message_cv2correction(msg):
        """
        OpenCV has a bug that cannot deal with images with signed types. This function turns the numpy
        array's type to unsigned to solve that problem
        :param msg: The message representing the numpy array received from zmq
        :return: ndarray that represents an image that can be read by cv2
        """
        md_bytes = msg[0]

        md_str = md_bytes.decode("UTF-8")
        md = ast.literal_eval(md_str)

        dtype = md['dtype']
        shape = md['shape']

        return Socket._reconstruct_array_from_bytes_message(msg, dtype, shape, switch_to_unsigned=True)

    @staticmethod
    @dec.deprecated("Use reconstruct_data_from_bytes_message")
    def reconstruct_array_from_bytes_message(msg):
        """
        Static method to reconstruct a message that represents a numpy array to that array
        :param msg: The message received from zmq
        :param switch_to_unsigned: If true then switch the arrays type to unsigned
        :return:
        """
        md_bytes = msg[0]

        md_str = md_bytes.decode("UTF-8")
        md = ast.literal_eval(md_str)

        dtype = md['dtype']
        shape = md['shape']

        return Socket._reconstruct_array_from_bytes_message(msg, dtype, shape, switch_to_unsigned=False)