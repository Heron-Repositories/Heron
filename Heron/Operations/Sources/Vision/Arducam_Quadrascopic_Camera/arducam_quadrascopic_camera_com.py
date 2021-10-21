
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
# This is where a new nodes individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Arducam Quadrascopic Camera'
NodeAttributeNames = ['Parameters', 'Frame Out']
NodeAttributeType = ['Static', 'Output']
ParameterNames = ['Cam Index', 'FourCC', 'Exposure', 'Gain', 'Trigger Mode', 'Get Sub Camera', 'Sub Camera Scale',
                  'Save File', 'Timestamp', 'FPS of File']
ParameterTypes = ['int', 'str', 'int', 'int', 'bool', 'list', 'float', 'str', 'bool', 'int']
ParametersDefaultValues = [0, 'FMP4', -1, -1, False, ['0', '1', '2', '3', '4'], 1.0, '', False, 40]
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'arducam_quadrascopic_camera_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    camera_com = gu.start_the_source_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(camera_com.on_kill)
    camera_com.start_ioloop()
# </editor-fold>
