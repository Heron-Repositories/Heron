
import os
import pandas as pd
from datetime import datetime


def create_storage_names(relic_path):
    """
    Creates the names for the storage and the relic given the path the relic needs to be saved in
    (which the user provides in the Node)
    :param relic_path: The path the relic is going to be saved in
    :return: The root of the FileStorage and the relic_type of the Relic
    """
    relic_path = os.path.normpath(relic_path)
    root = os.path.dirname(relic_path)
    relic_type = relic_path.split(os.sep)[-1]
    return root, relic_type

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

class HeronRelic():
    """
    The class that deals with saving into Relics (using reliquery) of the parameters and any other variable defined
    in the worker script of a Node.
    """
    def __init__(self, relic_path, node_name, node_index):
        self.operational = True
        try:
            from reliquery.storage import FileStorage
            from reliquery import Relic
        except ImportError:
            self.operational = False

        if relic_path == '_':
            self.operational = False

        if self.operational:
            root, relic_type = create_storage_names(relic_path)
            self.name = '{}##{}'.format(node_name, node_index)
            self.storage = FileStorage(root, '{}##storage'.format(self.name))
            self.relic = Relic(name=self.name, relic_type=relic_type, storage=self.storage)
        else:
            self.storage = None
            self.relic = None

        self.parameters_pandasdf_exists = False
        self.substate_pandasdf_exists = False

    def create_the_pandasdf(self, type, **variables):
        """
        Creates the pandasdf that stores the variables in the appropriately named part of the relic (type). It also adds
        two columns at the beginning of the df named DateTime (where the datetime.now() is stored) and the WorkerIndex
        where the index of the worker function's iteration is stored.
        :param type: Can be either 'Parameters' or 'Substate'
        :param parameters: the variables to be saved with their initial values. The variable names will become the
        column names
        :return: Nothing
        """
        assert type == 'Parameters' or type == 'Substate', 'The type of the pandasdf in HeronRelic.create_the_pandasdf()' \
                                                           'must be either "Parameters" or "Substate"'
        variables['DateTime'] = datetime.now()
        variables['WorkerIndex'] = 0

        df = pd.DataFrame([variables])

        df['DateTime'] = pd.to_datetime(df['DateTime'], format='%Y-%m-%d %H:%M:%S')
        df = rearrange_pandasdf_columns(df)

        self.relic.add_pandasdf(name=type, pandas_data=df)
        if type == 'Parameters':
            self.parameters_pandasdf_exists = True
        elif type == 'Substate':
            self.substate_pandasdf_exists = True

    def update_the_parameters_pandasdf(self, parameters: list, worker_index: int):
        """
        Updates the Parameters pandasdf of the relic
        :param variables: a list with the variable values that define the Parameters (in the same order as defined in the
        create_the_pandasdf() function)
        :param worker_index: The index of the iteration of the worker
        :return: Nothing
        """
        if self.parameters_pandasdf_exists:
            df = self.relic.get_pandasdf('Parameters')
            parameters = [worker_index] + parameters
            parameters = [datetime.now()] + parameters
            df.loc[len(df.index)] = parameters
            self.relic.add_pandasdf(name='Parameters', pandas_data=df)

    def update_the_substate_pandasdf(self, worker_index, **variables):
        """
        Updates the Substate pandasdf of the relic. It first checks to see if the Substate pandadf exist and if it
        doesn't it creates it.
        :param worker_index: The index of the worker function iteration
        :param kwarg_variables: The variables passed as multiple arguments with names (**kwargs style)
        :return: Nothing
        """
        if self.relic is not None:
            if not self.substate_pandasdf_exists:
                self.create_the_pandasdf(type='Substate', **variables)

            df = self.relic.get_pandasdf('Substate')
            variables['DateTime'] = datetime.now()
            variables['WorkerIndex'] = worker_index

            row = pd.DataFrame([variables])
            df = pd.concat([df, row], ignore_index=True)
            df.reset_index(drop=True, inplace=True)

            self.relic.add_pandasdf(name='Substate', pandas_data=df)
