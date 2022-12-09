
import sys
from os import path
import time
import numpy as np

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron import general_utils as gu
from Heron.communication.source_worker import SourceWorker
from Heron.gui.visualisation_dpg import VisualisationDPG


worker_object: SourceWorker
visualisation_on: bool
latest_user_input: str
loop_on = False
finish = False
vis: VisualisationDPG


def initialise(_worker_object):
    global visualisation_on
    global output_type
    global latest_user_input
    global loop_on
    global vis

    try:
        visualisation_on = _worker_object.parameters[0]
        output_type = _worker_object.parameters[1]
        latest_user_input = str(_worker_object.parameters[2])

        vis = VisualisationDPG(_node_name=_worker_object.node_name, _node_index=_worker_object.node_index,
                               _visualisation_type='Value', _buffer=20)

        loop_on = True

    except:
        pass

    return loop_on


def start_user_input_capture(_worker_object):
    global visualisation_on
    global output_type
    global latest_user_input
    global loop_on

    while not loop_on and not finish:
        gu.accurate_delay(1)

    _worker_object.savenodestate_create_parameters_df(visualisation_on=False,
                                                      output_type=output_type,
                                                      user_input=latest_user_input)

    while loop_on and not finish:
        try:
            visualisation_on = _worker_object.parameters[0]
            output_type = _worker_object.parameters[1]
            latest_user_input = str(_worker_object.parameters[2])

            vis.visualisation_on = visualisation_on

            if latest_user_input != '':

                if output_type == 'int':
                    latest_user_input = [int(i) for i in latest_user_input.split(' ')]
                if output_type == 'float':
                    latest_user_input = [float(i) for i in latest_user_input.split(' ')]

                _worker_object.savenodestate_update_substate_df(user_input=latest_user_input)

                result = np.array([latest_user_input])
                _worker_object.send_data_to_com(result)
                vis.visualise(result)

                latest_user_input = ''
                _worker_object.parameters[2] = latest_user_input
        except Exception as e:
            print(e)

        time.sleep(0.1)


def on_end_of_life():
    global loop_on
    global finish

    finish = False
    loop_on = False
    vis.end_of_life()


if __name__ == "__main__":
    gu.start_the_source_worker_process(start_user_input_capture, on_end_of_life, initialisation_function=initialise)