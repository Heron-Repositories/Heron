
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
BaseName = 'TL Cottonbud Angle'
NodeAttributeNames = ['Parameters', 'Frame In', 'Angle Out', 'Image Out']
NodeAttributeType = ['Static', 'Input', 'Output', 'Output']
ParameterNames = ['Model zoo yaml', 'Model Weights File', 'Number of Classes', 'Calculate Image with Boxes']
ParameterTypes = ['str', 'str', 'int', 'bool']
ParametersDefaultValues = ['model_zoo_file.yaml', 'model_final.pth', 5, False]
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'tl_cottonbud_angle_worker.py')

# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    # Since this is a multiple output node we need to pass NodeAttributeType, NodeAttributeNames to
    # general_utilities start_the_xxx_communications_process function
    tl_cottonbud_angle_com = gu.start_the_transform_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(tl_cottonbud_angle_com.on_kill)
    tl_cottonbud_angle_com.start_ioloop()

# </editor-fold>
