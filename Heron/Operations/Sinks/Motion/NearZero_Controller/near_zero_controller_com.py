
import os
from Heron import general_utils as gu
Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new node's individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'NearZero Gimbal Controller'
NodeAttributeNames = ['Parameters', 'Command In']
NodeAttributeType = ['Static', 'Input']
ParameterNames = ['Use pylibi2c', 'I2C Address', 'Motor', 'Position OR Rotation', 'Value', 'Current', 'Trigger String']
ParameterTypes = ['bool', 'str', 'int', 'list', 'str', 'str', 'str']
ParametersDefaultValues = [False, '0x40', 1, ['p', 'r'], '+00000', '00000', 'move']
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'near_zero_controller_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    near_zero_controller_com = gu.start_the_sink_communications_process()
    gu.register_exit_signals(near_zero_controller_com.on_kill)
    near_zero_controller_com.start_ioloop()

# </editor-fold>
