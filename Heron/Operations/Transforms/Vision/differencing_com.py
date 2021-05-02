

import os
import sys
from Heron import general_utils as gu
from Heron.communication.transform_com import TransformCom
Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new node's individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Differencing'
NodeAttributeNames = ['Parameters', 'Frame 1 In', 'Frame 2 In', 'Difference Out']
NodeAttributeType = ['Static', 'Input', 'Input', 'Output']
ParameterNames = ['Visualisation', 'Frame 2 - Frame In']
ParameterTypes = ['bool', 'bool']
ParametersDefaultValues = [False, False]

# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    worker_exec = os.path.join(os.path.dirname(Exec), 'differencing_worker.py')
    differencing_com = gu.start_the_communications_process(worker_exec)
    differencing_com.start_ioloop()

# </editor-fold>