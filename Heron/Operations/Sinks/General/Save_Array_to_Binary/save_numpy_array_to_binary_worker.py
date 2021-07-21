
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import json
import numpy as np
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from diskarray import DiskArray

need_parameters = True
append_or_stack: bool
disk_array: DiskArray
file_name: str
input_shape = None
input_type: type
output_shape: tuple


def save_array(data, parameters):
    global need_parameters
    global append_or_stack
    global file_name
    global disk_array
    global input_shape
    global input_type
    global output_shape

    # Once the parameters are received at the starting of the graph then they cannot be updated any more.
    if need_parameters:
        try:
            file_name = parameters[0]
            append_or_stack = parameters[1]
            need_parameters = False
        except:
            return

    message = data[1:]  # data[0] is the topic
    array = Socket.reconstruct_array_from_bytes_message(message)

    if input_shape is None:
        input_shape = np.array(array.shape)
        input_type = array.dtype
        if append_or_stack:
            input_shape[0] = 0
        else:
            input_shape = [0]
            for i in array.shape:
                input_shape.append(i)

        input_shape = tuple(input_shape)
        disk_array = DiskArray(file_name, shape=input_shape, dtype=input_type)
        disk_array.extend(array)

    else:
        disk_array.extend(array)
        output_shape = tuple(map(int, disk_array.shape))
        with open("{}_header.json".format(file_name.split('.')[0]), "w+") as json_file:
            json.dump({'shape': list(output_shape), 'dtype': str(disk_array.dtype)}, json_file)


def on_end_of_life():
    global file_name
    global output_shape
    global input_type
    new_file_name = file_name.split('.')[0]
    with open("{}_header.json".format(new_file_name), "w+") as json_file:
        json.dump({'shape': list(output_shape), 'dtype': str(disk_array.dtype)}, json_file)


if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(save_array, on_end_of_life)
    worker_object.start_ioloop()
