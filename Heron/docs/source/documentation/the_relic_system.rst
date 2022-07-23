

The Relic system
=================

Heron allows a Node developer to quickly set up a system that saves the parameters, every time they update, and any
data the worker script has access to at every iteratrion of the Node's worker function. This saving system is based on
the `reliquery <https://github.com/The-Dev-Effect/reliquery>`_ Python package (more info about it can be
found on the developers' `website <https://www.deveffect.io/blog-1/reliquery-cj247>`_). In this package individual
pieces of information are saved as what is defined a Relic.

A Node's Relic
______________

If the Relic system is used Heron will generate a Relic with up to two pandas Dataframes. One will store all the parameters,
with columns names defined by the developer, and with every row corresponding to the parameters of the Node when any of
them was changed by the user. In the Relic folder this dataframe will be called 'Parameters'. The other dataframe (called
Substate) has column names also defined by the Node's developer and saves any piece of information the developer assigns. In
this case each row represents a single iteration of the worker function.

In both the Parameters and Substate dataframes the rows are also timestamped through the 'DateTime' column and there
is a column (called 'WorkerIndex') that registers the current iteration of the worker function.

The Relic system needs two things to automatically start saving information. One is an implementation in the Node (see
bellow how this is done). The other is a folder path in the 'Save Relic to folder' text entry of the Node's secondary
window (see :doc:`the_editor`). If any of these two things are missing then the system just doesn't work. That means
that if there is a Node implementation then it is up to the user to put a folder path in to get the system to work
(or not). On the other hand if the Node hasn't implemented the system then adding a folder path will do nothing
(including not notifying the user that nothing will happen).

Implementation in the Node
__________________________

Acces to Heron's implementation of the Relic system is done through the worker object in the Node's initialisation
function and the Source Nodes' worker function and through the relic_update_substate_df function that is passed as an
argument to the worker functions of the Transform and Sink Nodes every time they are called by Heron.

More sepcifically the worker_object has two methods (relic_create_parameters_df and relic_update_substate_df) and a
variable (num_of_iters_to_update_relics_substate) that pertain to the Relic system.

Saving the parameters
^^^^^^^^^^^^^^^^^^^^^
A developer who wishes to have a Node that is able to save all its parameters' changes through the lifetime of a
running Graph can add the following line either to the initialisation function of any Node or to the pre infinite loop
part of the worker function of Source Nodes.

.. code-block:: python

    worker_object.relic_create_parameters_df(parameter_var_1=global_var_1, parameter_var_2=global_var_2,
                                             parameter_var_3=global_var_3, parameter_var_4=global_var_4)

The parameter_var_1, parameter_var_2, etc. will become the column names of the saved dataframe. They can be any names
the developer wants but using the same names as the parameters of the Node is considered good practice. The global_var_1,
global_var_2 variables will become the initial values (1st row of the dataframe) and need to be valid variables in the
Node at the time this method is called.

Given the above code and a Relic folder path in the secondary window of the Node, the system will then save all parameter
values any time the user changes any of the parameters at the Node's main GUI.

Saving part of the Node's state
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Saving some of the Node's state in the Node's Relic can be achieved with one of two different methods given the type
of Node.

In the case of Source Nodes (which expose the full SourceWorker worker object in the worker function of the worker
script) one can simply add (usually in the infinite loop part of the worker function) the following code:

.. code-block:: python

    worker_object.relic_update_substate_df(some_name_1=some_data_1, some_name_2, some_data_2)


The Transform and Sink Nodes on the other hand, have worker functions which do not expose the whole worker object, but
expose the function relic_update_substate_df as an argument. So if a Node developer whishes to use the Relic system
in Transform and Sink Nodes they must define their worker functions with relic_update_substate_df as a third argument
(after the data and parameters ones) and then call that function exactly like above inside the worker function:

.. code-block:: python

    def worker_function(parameters, data, relic_update_substate_df):
        ...
        relic_update_substate_df(some_name_1=some_data_1, some_name_2, some_data_2)
        ...


Here, as in the case of the parameters, the 'some_name_1', etc. names of the arguments of the relic_update_substate_df
function are going to become the names of the dataframe's columns. The some_data_1, etc values are data that the user
wishes to save.



Controlling the update of the dataframes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The Parameters dataframe, as mentioned above is automatically updates every time the user changes any of the parameters
(which is not a very frequent action). The update of the Substate dataframe though to the hard disk can be an expensive
operation especially if it needs to happen many times per second (at the speed at which a fast Node might need to
call its worker function) and/or that data saved are large.

Currently the Node's developer and users can control when Heron will save the dataframe (which is constantly being
updated in RAM) to disk. This is achieved either through a global variable found in the constants script called
NUMBER_OF_ITTERATIONS_BEFORE_RELIC_SUBSTATE_SAVE or through a Node specific variable called
num_of_iters_to_update_relics_substate the worker object exposes. If the num_of_iters_to_update_relics_substate is set
then it takes precedence over the global variable.

If the num_of_iters_to_update_relics_substate (or the NUMBER_OF_ITTERATIONS_BEFORE_RELIC_SUBSTATE_SAVE when no
num_of_iters_to_update_relics_substate is set for the Node) is set to -1 then the Relic system will not update the
Substate dataframe to disk until the process is about to terminate. There is a tradeoff here. If the relic's dataframe
is saved to disk only as the process closes down then any crash that would abnormally terminate the process without
allowing it to run its end_of_life function will mean loss of the relic's dataframe. On the other hand long running
processes in machines with small RAM might run out of memory while keeping the dataframe in RAM.


Loading saved Relics
^^^^^^^^^^^^^^^^^^^^
Although one can refer to the reliquery's manual as to how a saved Relic can be loaded to memory, the following code
can load either a Parameters (get_parameters_df_from_relic) or a Substate (get_substate_df_from_relic) pandas dataframe
given the path and the Node' name.

.. code-block:: python

    import os
    from reliquery.storage import FileStorage
    from reliquery import Relic


    def _create_storage_names(relic_path):
        relic_path = os.path.normpath(relic_path)
        root = os.path.dirname(relic_path)
        relic_type = relic_path.split(os.sep)[-1]
        return root, relic_type


    def _get_relic(relic_path, node_name):
        root, relic_type = _create_storage_names(relic_path)
        storage = FileStorage(root, node_name)
        relic = Relic(name=node_name, relic_type=relic_type, storage=storage)

        return relic


    def get_parameters_df_from_relic(relic_path, node_name):
        relic = _get_relic(relic_path, node_name)
        return relic.get_pandasdf('Parameters')


    def get_substate_df_from_relic(relic_path, node_name):
        relic = _get_relic(relic_path, node_name)
        return relic.get_pandasdf('Substate')


