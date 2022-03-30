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

# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new node's individual elements should be defined">
"""
Properties of the generated Node
"""
BaseName = 'User Defined Function 2I 1O'
NodeAttributeNames = ['Parameters', 'Input', 'Input', 'Output']

NodeAttributeType = ['Static', 'Input', 'Input', 'Output']

ParameterNames = [r"Full path to function's filename"]

ParameterTypes = ['str']

ParametersDefaultValues = [r'E:\Temp\function.py']

WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'user_defined_function_2i1o_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph.
#  You can refactor the name of the xxx_com variable but do not change anything else">
if __name__ == "__main__":
    user_defined_function_2i1o_com = gu.start_the_transform_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(user_defined_function_2i1o_com.on_kill)
    user_defined_function_2i1o_com.start_ioloop()

# </editor-fold>
