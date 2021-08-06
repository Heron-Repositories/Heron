
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
import h5py
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu

need_parameters = True
expand: bool
on_axis: int
disk_array: h5py.Dataset
file_name: str
input_shape = None
input_type: type
output_type: str
shape_step: list
hdf5_file: h5py.File


def add_data_to_array(data):
    global disk_array
    global shape_step
    global on_axis

    disk_array.resize(np.array(disk_array.shape) + shape_step)
    slice = [np.s_[:] for i in range(len(data.shape))]
    slice[on_axis] = np.s_[int(disk_array.shape[on_axis] - shape_step[on_axis]):disk_array.shape[on_axis]]
    disk_array[tuple(slice)] = data


def save_array(data, parameters):
    global need_parameters
    global expand
    global on_axis
    global file_name
    global disk_array
    global input_shape
    global input_type
    global output_type
    global shape_step
    global hdf5_file

    # Once the parameters are received at the starting of the graph then they cannot be updated any more.
    if need_parameters:
        try:
            file_name = parameters[0]
            expand = parameters[1]
            on_axis = parameters[2]
            output_type = parameters[3]
            need_parameters = False
        except:
            return

    message = data[1:]  # data[0] is the topic
    array = Socket.reconstruct_array_from_bytes_message(message)

    if input_shape is None:
        try:
            input_type = array.dtype

            if expand:
                input_shape = list(array.shape)
                shape_step = np.zeros(len(input_shape))
                input_shape[on_axis] = 0
                shape_step[on_axis] = array.shape[on_axis]
            else:
                input_shape = []
                shape_step = []
                for i, n in enumerate(array.shape):
                    if i == on_axis:
                        input_shape.append(0)
                        shape_step.append(1)
                    input_shape.append(n)
                    shape_step.append(0)
            max_shape = np.copy(input_shape)
            max_shape = list(max_shape)
            max_shape[np.where(np.array(input_shape) == 0)[0][0]] = None
            input_shape = tuple(input_shape)
            max_shape = tuple(max_shape)

            if output_type == 'Same':
                output_type = input_type
            else:
                output_type = np.dtype(output_type)

            hdf5_file = h5py.File(file_name, 'w')
            disk_array = hdf5_file.create_dataset('data', shape=input_shape, maxshape=max_shape, dtype=output_type,
                                                  chunks=True)

            if not expand:
                array = np.expand_dims(array, on_axis)

            add_data_to_array(array)

        except Exception as e:
            print(e)
    else:
        try:
            if not expand:
                array = np.expand_dims(array, on_axis)
            add_data_to_array(array)
        except Exception as e:
            print(e)


def on_end_of_life():
    global hdf5_file

    hdf5_file.close()


if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(save_array, on_end_of_life)
    worker_object.start_ioloop()
