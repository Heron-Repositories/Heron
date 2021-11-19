
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
BaseName = 'TL Projector Output'
NodeAttributeNames = ['Parameters', 'Trigger Photodiode.', 'Angle of Pic']
NodeAttributeType = ['Static', 'Input', 'Input']
ParameterNames = ['Picture file name', 'Screen X', 'Screen Y', 'Picture X', 'Picture Y', 'Show Inner Pic']
ParameterTypes = ['str', 'int', 'int', 'int', 'int', 'bool']
ParametersDefaultValues = ['pic.png', 2560, 0, 535, 545, True]
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'tl_projector_output_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    tl_projector_output_com = gu.start_the_sink_communications_process()
    gu.register_exit_signals(tl_projector_output_com.on_kill)
    tl_projector_output_com.start_ioloop()

# </editor-fold>
