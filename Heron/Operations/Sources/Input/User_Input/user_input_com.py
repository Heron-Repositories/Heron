

import os
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron import general_utils as gu

Exec = os.path.abspath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new nodes individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'User Input'
NodeAttributeNames = ['Parameters', 'Text Out']
NodeAttributeType = ['Static', 'Output']
ParameterNames = ['Visualisation', 'Output Type', 'User Input']
ParameterTypes = ['bool', 'list', 'str']
ParametersDefaultValues = [False, ['string', 'int', 'float'], '']
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'user_input_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    user_input_com = gu.start_the_source_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(user_input_com.on_kill)
    user_input_com.start_ioloop()
# </editor-fold>
