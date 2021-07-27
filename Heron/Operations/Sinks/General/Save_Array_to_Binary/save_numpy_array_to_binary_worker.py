
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
from Heron.Operations.Sinks.General.Save_Array_to_Binary.diskarray import DiskArray

need_parameters = True
append_on_axis: int
disk_array: DiskArray
file_name: str
input_shape = None
input_type: type
output_shape: tuple
output_type: str


def save_array(data, parameters):
    global need_parameters
    global append_on_axis
    global file_name
    global disk_array
    global input_shape
    global input_type
    global output_shape
    global output_type

    # Once the parameters are received at the starting of the graph then they cannot be updated any more.
    if need_parameters:
        try:
            file_name = parameters[0]
            append_on_axis = parameters[1]
            output_type = parameters[2]
            need_parameters = False
        except:
            return

    message = data[1:]  # data[0] is the topic
    array = Socket.reconstruct_array_from_bytes_message(message)

    if input_shape is None:
        try:
            input_type = array.dtype

            input_shape = []
            for i, n in enumerate(array.shape):
                if i == append_on_axis:
                    input_shape.append(0)
                input_shape.append(n)
            input_shape = tuple(input_shape)

            if output_type == 'Same':
                output_type = input_type
            else:
                output_type = np.dtype(output_type)

            disk_array = DiskArray(file_name, shape=input_shape, dtype=output_type)
            array = np.expand_dims(array, append_on_axis)
            disk_array.append(array, append_on_axis)
        except Exception as e:
            print(e)
    else:
        try:
            array = np.expand_dims(array, append_on_axis)
            disk_array.append(array, append_on_axis)
            output_shape = tuple(map(int, disk_array.shape))
            with open("{}_header.json".format(file_name.split('.')[0]), "w+") as json_file:
                json.dump({'shape': list(output_shape), 'dtype': str(output_type)}, json_file)
        except Exception as e:
            print(e)


def on_end_of_life():
    global file_name
    global output_shape
    global input_type
    global output_type

    new_file_name = file_name.split('.')[0]
    with open("{}_header.json".format(new_file_name), "w+") as json_file:
        json.dump({'shape': list(output_shape), 'dtype': str(output_type)}, json_file)


if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(save_array, on_end_of_life)
    worker_object.start_ioloop()
