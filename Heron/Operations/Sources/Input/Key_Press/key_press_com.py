

import os
from Heron import general_utils as gu

Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new nodes individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Key Press'
NodeAttributeNames = ['Parameters', 'Key Out']
NodeAttributeType = ['Static', 'Output']
ParameterNames = ['Visualisation', 'Key']
ParameterTypes = ['bool', 'str']
ParametersDefaultValues = [False, 'a']
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'key_press_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    key_com = gu.start_the_source_communications_process()
    gu.register_exit_signals(key_com.on_kill)
    key_com.start_ioloop()
# </editor-fold>
