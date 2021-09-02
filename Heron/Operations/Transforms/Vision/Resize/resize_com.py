
import os
from Heron import general_utils as gu
Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new node's individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Resize'
NodeAttributeNames = ['Parameters', 'Frame In', 'Frame Out']
NodeAttributeType = ['Static', 'Input', 'Output']
ParameterNames = ['Visualisation', 'X', 'Y']
ParameterTypes = ['bool', 'int', 'int']
ParametersDefaultValues = [False, 600, 400]
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'resize_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    resize_com = gu.start_the_transform_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(resize_com.on_kill)
    resize_com.start_ioloop()

# </editor-fold>
