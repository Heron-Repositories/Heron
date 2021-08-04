

import os
from functools import reduce
from logging import Logger

import numpy as np


class DiskArray(object):

    def __init__(self, fpath, dtype, mode='r+', shape=None, log=Logger):

        itemsize = np.dtype(dtype).itemsize

        if not os.path.exists(fpath):
            if not shape:
                shape = (0,)

            capacity = tuple([max(x, 1) for x in shape])

            n_init_capacity = self._shape_bytes(capacity, itemsize)
            open(fpath, 'w').write('\x00' * n_init_capacity) # touch file

        if not shape:
            n = int(os.path.getsize(fpath) / itemsize)
            shape = (n,)

        self._fpath = fpath
        self._shape = shape
        self._capacity_shape = shape
        self._dtype = dtype
        self._mode = mode
        self.log = log

        self.data = None
        self._update_ndarray()

    def _update_ndarray(self, order='C'):
        if self.data is not None:
            self.data.flush()

        self._create_ndarray(order)

    def _create_ndarray(self, order):
        self.data = np.memmap(self._fpath,
                              shape=self._capacity_shape,
                              dtype=self._dtype,
                              mode=self._mode,
                              order=order)
        if self._shape is None:
            self._shape = self.data.shape

    def flush(self):
        self.data.flush()
        self._truncate_if_needed()

    def _shape_bytes(self, shape, dtype_bytes):
        return reduce((lambda x, y: x * y), shape) * dtype_bytes

    def _truncate_if_needed(self):
        fd = os.open(self._fpath, os.O_RDWR|os.O_CREAT)
        try:
            dtype_bytes = np.dtype(self._dtype).itemsize
            nbytes = self._shape_bytes(self._shape, dtype_bytes)
            os.ftruncate(fd, nbytes)
            self._capacity_shape = self._shape
        finally:
            os.close(fd)
        self._create_ndarray()

    @property
    def shape(self):
        return self._shape

    @property
    def capacity(self):
        return self._capacity_shape

    @property
    def dtype(self):
        return self._dtype

    def __getitem__(self, idx):
        return self.data[idx]

    def __setitem__(self, idx, v):
        self.data[idx] = v

    def __len__(self):
        return self._shape[0]

    def _incr_shape(self, shape, n):
        _s = np.array(shape)
        _s += n
        return tuple(_s)

    def append(self, v, axis=-1):
        if axis < 0:
            axis = len(self._shape) + axis

        remaining_capacity = np.array(self._capacity_shape)
        remaining_capacity[axis] = np.array(self._capacity_shape)[axis] - np.array(self._shape)[axis]
        data_shape = np.array(v.shape)

        for d in range(len(self._shape)):
            if d != axis:
                assert self._shape[d] == v.shape[d], 'Array to append needs to have equal dimensions on all but the appended to axis'

        diff = data_shape - remaining_capacity
        self._capacity_shape = self._incr_shape(self._capacity_shape, diff)

        self._update_ndarray(order='F')

        slice = [np.s_[:] for i in range(len(self._capacity_shape))]
        slice[axis] = np.s_[self._shape[axis]:self._capacity_shape[axis]]
        self.data[tuple(slice)] = v

        self._shape = self._incr_shape(self._shape, diff)

    def close(self):
        self.data._mmap.close()
        del self.data
        del self._fpath

    def destroy(self):
        self.data = None
        os.remove(self._fpath)