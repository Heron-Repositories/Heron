

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
NodeAttributeNames = ['Parameters', 'Frame_1_In', 'Frame_2_In', 'Difference_Out']
NodeAttributeType = ['Static', 'Input', 'Input', 'Output']
ParameterNames = ['Visualisation', 'Frame 2 - Frame In']
ParameterTypes = ['bool', 'bool']
ParametersDefaultValues = [False, False]
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'differencing_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    differencing_com = gu.start_the_transform_communications_process()
    gu.register_exit_signals(differencing_com.on_kill)
    differencing_com.start_ioloop()

# </editor-fold>