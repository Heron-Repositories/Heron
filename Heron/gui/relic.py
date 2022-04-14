
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

        if relic_path == '':
            self.operational = False

        if self.operational:
            root, relic_type = create_storage_names(relic_path)
            self.name = '{}##{}'.format(node_name, node_index)
            self.storage = FileStorage(root, '{}##storage'.format(self.name))
            self.relic = Relic(name=self.name, relic_type=relic_type, storage=self.storage)
            self.parameters_pandasdf_exists = False
            self.state_pandasdf_exists = False
        else:
            self.storage = None
            self.relic = None

    def create_the_parameters_pandasdf(self,**parameters):
        """
        Creates the pandasdf that stores the Parameters
        :param parameters: the variables of the parameters with their initial values. The variable names will become the
        column names
        :return: Nothing
        """
        parameters['DateTime'] = datetime.now()
        parameters['WorkerIndex'] = 0
        df = pd.DataFrame([parameters])
        df['DateTime'] = pd.to_datetime(df['DateTime'], format='%Y-%m-%d %H:%M:%S')
        self.relic.add_pandasdf(name='Parameters', pandas_data=df)
        self.parameters_pandasdf_exists = True

    def update_the_parameters_pandasdf(self, parameters: list, worker_index: int):
        """
        Updates the Parameters pandasdf of the relic
        :param parameters: a list with the parameter values
        :param worker_index: The index of the iteration of the worker
        :return: Nothing
        """
        if self.parameters_pandasdf_exists:
            df = self.relic.get_pandasdf('Parameters')
            parameters.append(datetime.now())
            parameters.append(worker_index)
            df.loc[len(df.index)] = parameters
            self.relic.add_pandasdf(name='Parameters', pandas_data=df)

