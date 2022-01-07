
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
BaseName = 'TL Task2 Screens'
NodeAttributeNames = ['Parameters', 'Move By']
NodeAttributeType = ['Static', 'Input']
ParameterNames = ['Screen', 'T=Rotation (F=Translation)', 'Opacity']
ParameterTypes = ['list', 'bool', 'int']
ParametersDefaultValues = [['Both', 'Left', 'Top'], True, 255]
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'tl_task2_screens_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    tl_task2_screens_com = gu.start_the_sink_communications_process()
    gu.register_exit_signals(tl_task2_screens_com.on_kill)
    tl_task2_screens_com.start_ioloop()

# </editor-fold>
