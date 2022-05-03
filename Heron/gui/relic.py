
import os
import pandas as pd
from datetime import datetime
from Heron import constants as ct


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
    def __init__(self, relic_path, node_name, node_index, num_of_iters=None):
        self.operational = True

        if relic_path == '_':
            self.operational = False
        else:
            try:
                import reliquery
                import reliquery.storage
                file_storage = reliquery.storage.FileStorage
                relic = reliquery.Relic
            except ImportError:
                self.operational = False
                reliquery = None
                file_storage = None
                relic = None

        if self.operational:
            root, relic_type = create_storage_names(relic_path)
            self.name = '{}##{}'.format(node_name, node_index)
            self.storage = file_storage(root, '{}##storage'.format(self.name))
            self.relic = relic(name=self.name, relic_type=relic_type, storage=self.storage)
            self.relic_path = relic_path
        else:
            self.storage = None
            self.relic = None

        self.parameters_pandasdf_exists = False
        self.substate_pandasdf_exists = False
        self.temp_substate_pandasdf = None

        self.num_of_iters = ct.NUMBER_OF_ITTERATIONS_BEFORE_RELIC_SUBSTATE_SAVE
        if num_of_iters is not None:
            self.num_of_iters = num_of_iters

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
            self.temp_substate_pandasdf = df

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
        doesn't it creates it. The update happens incrementally through a self.temp_substate_pandasdf temporary
        dataframe which gets loaded and at a certain number of worker_function iterations it gets saved into the relic.
        This number can be either ct.NUMBER_OF_ITTERATIONS_BEFORE_RELIC_SUBSTATE_SAVE when the Node's worker function
        hasn't specified it in the xxx_worker.num_of_iters_to_update_relics_substate variable or that variable. If that
        variable has the value of -1 then the information never gets saved to the hard disk until the process is about
        to die at which point the whole pandas (which has been kept in RAM) gets dumped in one go to the HD.
        Nodes that struggle to keep up with their operations can use the later strategy to not take any time in loading
        and re-saving the pandasdf. But that means that if the Node crashes without calling the on_kill of the worker
        object then the pandas is lost.
        :param worker_index: The index of the worker function iteration
        :param kwarg_variables: The variables passed as multiple arguments with names (**kwargs style)
        :return: Nothing
        """
        if self.relic is not None:
            if not self.substate_pandasdf_exists:
                self.create_the_pandasdf(type='Substate', **variables)

            variables['DateTime'] = datetime.now()
            variables['WorkerIndex'] = worker_index

            row = pd.DataFrame([variables])
            self.temp_substate_pandasdf = pd.concat([self.temp_substate_pandasdf, row], ignore_index=True)
            self.temp_substate_pandasdf.reset_index(drop=True, inplace=True)

            if self.num_of_iters != -1 and worker_index % self.num_of_iters == 0:
                self.save_current_substate_df()

    def save_current_substate_df(self):
        """
        This grabs the relic's Substate pandasdf, concatenates it with the self.temp_substate_pandasdf df and saves
        everything back to the relic. This is done to avoid loading and saving at every iteration
        :return: Nothing
        """
        df = self.relic.get_pandasdf('Substate')

        df = pd.concat([df, self.temp_substate_pandasdf], ignore_index=True)
        df.reset_index(drop=True, inplace=True)

        self.relic.add_pandasdf(name='Substate', pandas_data=df)

        self.temp_substate_pandasdf = self.temp_substate_pandasdf.iloc[0:0]

    def save_substate_at_death(self):
        """
        This is required because it will be called by the on_kill function of the Worker objects. This function is a
        callback that is called by a different Thread to the rest of the object so it will not see the self.relic
        appropriately (it cannot write to the metadata). So at death a new relic is created and saves the remaining
        self.temp_substate_pandasdf in the relic's 'Substate' type
        :return: Nothing
        """
        import reliquery.storage
        file_storage = reliquery.storage.FileStorage
        relic = reliquery.Relic

        root, relic_type = create_storage_names(self.relic_path)
        new_storage = file_storage(root, '{}##storage'.format(self.name))
        new_relic = relic(name=self.name, relic_type=relic_type, storage=new_storage)

        df = new_relic.get_pandasdf('Substate')
        df = pd.concat([df, self.temp_substate_pandasdf], ignore_index=True)
        df.reset_index(drop=True, inplace=True)

        new_relic.add_pandasdf(name='Substate', pandas_data=df)
