
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
# This is where a new node's individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Visualiser'
NodeAttributeNames = ['Parameters', 'In', 'Out']
NodeAttributeType = ['Static', 'Input', 'Output']
ParameterNames = ['Visualisation', 'Type', 'Buffer']
ParameterTypes = ['bool', 'list', 'int']
ParametersDefaultValues = [False, ['Image', 'Value', 'Single Pane Plot', 'Multi Pane Plot'], 100]
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'visualiser_worker.py')

# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    visualiser_com = gu.start_the_transform_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(visualiser_com.on_kill)
    visualiser_com.start_ioloop()

# </editor-fold>
