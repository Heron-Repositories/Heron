
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

worker_object: SourceWorker
latest_user_input: str
previous_user_input: str
initial_param_updates_num = 0
loop_on = True


def start_user_input_capture(_worker_object):
    global worker_object
    global latest_user_input
    global previous_user_input
    global initial_param_updates_num
    global loop_on

    worker_object = _worker_object

    while loop_on:
        try:
            visualisation_on = worker_object.parameters[0]
            output_type = worker_object.parameters[1]
            latest_user_input = str(worker_object.parameters[2])

            if latest_user_input != '':
                '''
                try:
                    latest_user_input = int(latest_user_input)
                except:
                    try:
                        latest_user_input = float(latest_user_input)
                    except:
                        pass
                '''

                if output_type == 'int':
                    latest_user_input = [int(i) for i in latest_user_input.split(' ')]
                if output_type == 'float':
                    latest_user_input = [float(i) for i in latest_user_input.split(' ')]

                if visualisation_on:
                    print(latest_user_input)

                result = np.array([latest_user_input])

                worker_object.socket_push_data.send_array(result, copy=False)
                latest_user_input = ''
                worker_object.parameters[1] = latest_user_input
        except:
            pass

        time.sleep(0.1)


def on_end_of_life():
    global loop_on
    loop_on = False


if __name__ == "__main__":
    gu.start_the_source_worker_process(start_user_input_capture, on_end_of_life)