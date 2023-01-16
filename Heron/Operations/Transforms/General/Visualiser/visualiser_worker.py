
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron.communication.socket_for_serialization import Socket
from Heron.gui.visualisation_dpg import VisualisationDPG
from Heron import general_utils as gu

visualisation_dpg: VisualisationDPG


def initialise(_worker_object):
    global worker_object
    global visualisation_dpg

    worker_object = _worker_object

    visualisation_on = worker_object.parameters[0]
    visualisation_type = worker_object.parameters[1]
    buffer = worker_object.parameters[2]

    visualisation_dpg = VisualisationDPG(_node_name=_worker_object.node_name, _node_index=_worker_object.node_index,
                                         _visualisation_type=visualisation_type, _buffer=buffer)

    worker_object.savenodestate_create_parameters_df(visualisation_on=visualisation_on,
                                                     visualisation_type=visualisation_type,
                                                     buffer=buffer)
    return True


def visualise(msg, parameters):
    global visualisation_dpg

    message = msg[1:]  # data[0] is the topic
    data = Socket.reconstruct_data_from_bytes_message(message)

    if parameters is not None:
        try:
            visualisation_on = parameters[0]
            visualisation_dpg.visualisation_on = visualisation_on
            visualisation_dpg.visualise(data)
        except Exception as e:
            print(e)

    return [data]


def on_end_of_life():
    global visualisation_dpg
    visualisation_dpg.end_of_life()


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(initialisation_function=initialise,
                                                          work_function=visualise,
                                                          end_of_life_function=on_end_of_life)
    worker_object.start_ioloop()