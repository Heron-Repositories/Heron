
import copy
import os
import threading
import time

import pandas as pd
from datetime import datetime
from Heron import constants as ct, general_utils as gu



def rearrange_pandasdf_columns(df):
    """
    Takes a pandas Dataframe with columns 'DateTime' and 'WorkerIndex' amongst others and places them at the front
    :param df: The pandas Dataframe
    :return: The column rearranged df
    """
    new_columns = ['DateTime', 'WorkerIndex']
    for c in df.columns:
        if c != 'DateTime' and c != 'WorkerIndex':
            new_columns.append(c)

    return df[new_columns]


class SaveNodeState():

    def __init__(self, path, node_name, node_index, num_of_iters=None):
        self.operational = True

        if path == '_':
            self.operational = False

        if self.operational:
            self.name = '{}##{}'.format(node_name, node_index)
            self.path = path

        self.parameters_pandasdf_exists = False
        self.substate_pandasdf_exists = False
        self.substate_pandasdf_new_data = None
        self.temp_substate_list = []
        self.temp_substate_list_to_save = []
        self.parameters_pandasdf: pd.DataFrame
        self.substate_pandasdf: pd.DataFrame

        self.num_of_iters = ct.NUMBER_OF_ITTERATIONS_BEFORE_SAVENODESTATE_SUBSTATE_SAVE

        if num_of_iters is not None:
            self.num_of_iters = num_of_iters

        self.prev_time = 0

    def create_the_pandasdf(self, type, **variables):
        """
        :param type: Can be either 'Parameters' or 'Substate'
        :param parameters: the variables to be saved with their initial values. The variable names will become the
        column names
        :return: Nothing
        """

        if self.operational:
            assert type == 'Parameters' or type == 'Substate', 'The type of the pandasdf in SaveNodeState.create_the_pandasdf()' \
                                                               'must be either "Parameters" or "Substate"'
            variables['DateTime'] = datetime.now()
            variables['WorkerIndex'] = 0

            df = pd.DataFrame([variables])

            df['DateTime'] = pd.to_datetime(df['DateTime'], format='%Y-%m-%d %H:%M:%S')
            df = rearrange_pandasdf_columns(df)

            folder = os.path.join(self.path, self.name)

            if type == 'Parameters':
                self.parameters_pandasdf_exists = True
                self.parameters_pandasdf = df.copy(deep=True)
                os.makedirs(folder, exist_ok=True)
                self.parameters_pandasdf.to_pickle(os.path.join(self.path, self.name, 'Parameters.df'))

            elif type == 'Substate':
                self.substate_pandasdf_exists = True
                self.substate_pandasdf = df.copy(deep=True)
                os.makedirs(folder, exist_ok=True)
                self.substate_pandasdf.to_pickle(os.path.join(self.path, self.name, 'Substate.df'))

    def save_current_df(self, type):
        """
        :return: Nothing
        """
        if self.operational:
            assert type == 'Parameters' or type == 'Substate', 'The type of the pandasdf in SaveNodeState.save_current_df()' \
                                                               'must be either "Parameters" or "Substate"'

            df = pd.read_pickle(os.path.join(self.path, self.name, '{}.df'.format(type)))
            if type == 'Parameters':
                df = pd.concat([df, self.parameters_pandasdf], ignore_index=True)
                self.parameters_pandasdf = self.parameters_pandasdf.iloc[0:0].copy(deep=True)
            elif type == 'Substate':
                df = pd.concat([df, self.substate_pandasdf], ignore_index=True)
                self.substate_pandasdf = self.substate_pandasdf.iloc[0:0].copy(deep=True)

            df.reset_index(drop=True, inplace=True)

            df.to_pickle(os.path.join(self.path, self.name, '{}.df'.format(type)))

    def update_the_parameters_pandasdf(self, parameters: list, worker_index: int):
        """
        Updates the parameters_pandasdf of the SaveNodeState
        :param variables: a list with the variable values that define the Parameters (in the same order as defined in the
        create_the_pandasdf() function)
        :param worker_index: The index of the iteration of the worker
        :return: Nothing
        """
        if self.parameters_pandasdf_exists and self.operational:
            parameters = [worker_index] + parameters
            parameters = [datetime.now()] + parameters
            row = pd.DataFrame([parameters])
            self.parameters_pandasdf.loc[len(self.parameters_pandasdf.index)] = parameters

            self.save_current_df('Parameters')

    # TODO: Rewrite the doc
    def update_the_substate_pandasdf(self, worker_index, **variables):
        """
        Updates the Substate pandasdf of the SaveNodeState. It first checks to see if the Substate pandadf exist and if it
        doesn't it creates it. The update happens incrementally through the self.substate_pandasdf temporary
        dataframe which gets loaded and at a certain number of worker_function iterations it gets saved into the relic.
        This number can be either ct.NUMBER_OF_ITTERATIONS_BEFORE_RELIC_SUBSTATE_SAVE when the Node's worker function
        hasn't specified it in the xxx_worker.num_of_iters_to_update_savenodestate_substate variable or that variable. If that
        variable has the value of -1 then the information never gets saved to the hard disk until the process is about
        to die at which point the whole pandas (which has been kept in RAM) gets dumped in one go to the HD.
        Nodes that struggle to keep up with their operations can use the later strategy to not take any time in loading
        and re-saving the pandasdf. But that means that if the Node crashes without calling the on_kill of the worker
        object then the pandas is lost.
        :param worker_index: The index of the worker function iteration
        :param kwarg_variables: The variables passed as multiple arguments with names (**kwargs style)
        :return: Nothing
        """

        if self.operational:
            if not self.substate_pandasdf_exists:
                self.create_the_pandasdf(type='Substate', **variables)

            variables['DateTime'] = datetime.now()
            variables['WorkerIndex'] = worker_index
            self.add_new_line_to_temp_array(worker_index, variables)

            if self.num_of_iters != -1 and worker_index % self.num_of_iters == 0:
                save_thread = threading.Thread(group=None, target=self.save_substate_to_pandas_df)
                save_thread.start()

    def add_new_line_to_temp_array(self, worker_index, variables):
        """

        :param worker_index:
        :param variables:
        :return:
        """
        self.substate_pandasdf_new_data = None

        variables['DateTime'] = datetime.now()
        variables['WorkerIndex'] = worker_index

        new_variables = {'DateTime': datetime.now(), 'WorkerIndex': worker_index}
        for v in variables:
            new_variables[v] = variables[v]

        self.temp_substate_list.append(list(new_variables.values()))

    def save_substate_to_pandas_df(self):
        self.temp_substate_list_to_save = copy.deepcopy(self.temp_substate_list)
        self.temp_substate_list = []
        rows = pd.DataFrame(self.temp_substate_list_to_save, columns=self.substate_pandasdf.columns)
        self.substate_pandasdf = pd.concat([self.substate_pandasdf, rows], ignore_index=True)
        self.substate_pandasdf.reset_index(drop=True, inplace=True)
        self.save_current_df('Substate')
        self.temp_substate_list_to_save = []

    def save_substate_at_death(self):
        rows = pd.DataFrame(self.temp_substate_list, columns=self.substate_pandasdf.columns)
        self.substate_pandasdf = pd.concat([self.substate_pandasdf, rows], ignore_index=True)
        self.substate_pandasdf.reset_index(drop=True, inplace=True)
        self.save_current_df('Substate')
