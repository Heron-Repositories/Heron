
import os
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron import general_utils as gu
Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new node's individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'TL Poke Controller'
NodeAttributeNames = ['Parameters', 'Start', 'Finished']
NodeAttributeType = ['Static', 'Input', 'Output']
ParameterNames = ['Com port', 'Availability Time (s)', 'Availability Freq (Hz)', 'Success Freq (Hz)', 'Trigger String']
ParameterTypes = ['str', 'float', 'list', 'list', 'str']
ParametersDefaultValues = ['COM5', 40, [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000],
                           [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000], 'start']
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'tl_poke_controller_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    tl_poke_controller_com = gu.start_the_transform_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(tl_poke_controller_com.on_kill)
    tl_poke_controller_com.start_ioloop()

# </editor-fold>
