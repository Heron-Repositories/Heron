
# <editor-fold desc="The following 6 lines of code are required to allow Heron to be able to see the Operation without
# package installation. Do not change.">
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))
# </editor-fold>

# <editor-fold desc="Extra imports if required">
import os
import pandas as pd
from datetime import datetime
from Heron.communication.socket_for_serialization import Socket
from Heron.gui.visualisation import Visualisation
from Heron import general_utils as gu
# </editor-fold>

column_names_str: str
file_name: str
overwrite_file: bool
vis: Visualisation
df: pd.DataFrame
# </editor-fold>


def add_timestamp_to_filename(save_file):

    filename = save_file.split('.')
    date_time = '{}'.format(datetime.now()).replace(':', '-').replace(' ', '_').split('.')[0]
    save_file = '{}_{}.{}'.format(filename[0], date_time, filename[1])

    return save_file


def initialise(_worker_object):
    global vis
    global column_names_str
    global file_name
    global overwrite_file
    global df

    # put the initialisation of the Node's parameter's in a try loop to take care of the time it takes for the GUI to
    # update the SinkWorker object.
    try:
        parameters = _worker_object.parameters
        vis = parameters[0]
        column_names_str = parameters[1]
        file_name = parameters[2]
        overwrite_file = parameters[3]
    except:
        return False

    # Ignore visualisation for now
    #vis = Visualisation(_worker_object.node_name, _worker_object.node_index)
    #vis.visualisation_init()

    if os.path.isfile(file_name):
        if overwrite_file:
            os.remove(file_name)
        else:
            print('File {} exists and cannot be overwritten so data will not be saved'.format(file_name))

    column_names = column_names_str.split(',')

    df = pd.DataFrame(columns=column_names)

    worker_object.savenodestate_create_parameters_df(visualisation_on=vis, column_names=column_names, file_name=file_name,
                                                     overwrite_file=overwrite_file)
    return True


def work_function(data, parameters):
    global vis
    global df


    try:
        vis.visualisation_on = parameters[0]
    except:
        pass


    topic = data[0]

    message = data[1:]
    message = Socket.reconstruct_data_from_bytes_message(message)
    #print('--- Message in Save DF: {}'.format(message))
    time = datetime.now()
    row = pd.DataFrame([message], columns=df.columns, index=[time])
    #print('--- DF Row: {}'.format(row))
    df = pd.concat([df, row], ignore_index=False)
    #vis.visualised_data = np.random.random((100,100))


def on_end_of_life():
    global df
    global file_name

    file_name = add_timestamp_to_filename(file_name)
    if not os.path.isfile(file_name):
        df.to_pickle(file_name)


# This needs to exist. The worker_function and the end_of_life function must be defined and passed. The initialisation_
# function is optional.
if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(work_function=work_function,
                                                     end_of_life_function=on_end_of_life,
                                                     initialisation_function=initialise)
    worker_object.start_ioloop()