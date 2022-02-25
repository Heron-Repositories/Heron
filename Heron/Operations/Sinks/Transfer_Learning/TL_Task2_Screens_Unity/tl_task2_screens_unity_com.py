
# <editor-fold desc="The following 9 lines of code are required to allow Heron to be able to see the Operation without
# package installation. Do not change.">
import os
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron import general_utils as gu

Exec = os.path.realpath(__file__)
# </editor-fold>


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.

"""
Properties of the generated Node
"""
BaseName = 'TL Task2 Screens Unity '  # The base name can have spaces.

NodeAttributeNames = ['Parameters', 'Move By']
NodeAttributeType = ['Static', 'Input']
ParameterNames = ['Screen', 'T=Rotation (F=Translation)', 'Opacity']
ParameterTypes = ['list', 'bool', 'float']
ParametersDefaultValues = [['Both', 'Right', 'Front'], True, 1.0]
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'tl_task2_screens_unity_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph.
#  You can refactor the name of the xxx_com variable but do not change anything else">
if __name__ == "__main__":
    #  In this case refactor the name sink_template_com to whatever_com
    tl_task2_screens_unity_com = gu.start_the_sink_communications_process()
    gu.register_exit_signals(tl_task2_screens_unity_com.on_kill)
    tl_task2_screens_unity_com.start_ioloop()
# </editor-fold>
