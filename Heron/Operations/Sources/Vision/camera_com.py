
import os
from Heron import general_utils as gu

Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new nodes individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Camera'
NodeAttributeNames = ['Parameters', 'Frame Out']
NodeAttributeType = ['Static', 'Output']
ParameterNames = ['Visualisation', 'Cam Index']
ParameterTypes = ['bool', 'int']
ParametersDefaultValues = [False, 0]

# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    worker_exec = os.path.join(os.path.dirname(Exec), 'camera_worker.py')
    spin_camera_com = gu.start_the_source_communications_process(worker_exec)
    spin_camera_com.start_ioloop()
# </editor-fold>
