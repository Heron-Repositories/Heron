# This is the code that defines the Parameters, Inputs and Outputs of the Node. Most of the code should not be
# changed. The only parts that should be changed are the information in the lists of the properties of the Node and the
# name of the xxx_com variable under the if __name__ == "__main__": clause


# <editor-fold desc="The following 9 lines of code are required to allow Heron to be able to see the Operation without
# package installation. Do not change.">
import os
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron import general_utils as gu

Exec = os.path.abspath(__file__)
# </editor-fold>


"""
Properties of the generated Node
"""
BaseName = 'Load Pandas'  # The base name can have spaces.
NodeAttributeNames = ['Parameters', 'Something Out 1']

NodeAttributeType = ['Static', 'Output']

ParameterNames = ['Visualisation', 'Parameter 1', 'Parameter 2', 'Parameter 3', 'Parameter 4']

ParameterTypes = ['bool', 'str', 'list', 'float', 'int']

ParametersDefaultValues = [False,
                           'True',
                           ['item 1',
                            'item 2'],
                           0.0,
                           2]

WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'load_pandas_worker.py')
# </editor-fold>

if __name__ == "__main__":
    load_pandas_com = gu.start_the_source_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(load_pandas_com.on_kill)
    load_pandas_com.start_ioloop()
# </editor-fold>
