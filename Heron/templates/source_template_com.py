
import os
import sys
from Heron import general_utils as gu
from Heron.communication.source_com import SourceCom

Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new nodes individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Name'
NodeAttributeNames = ['Parameters', 'Output name']
NodeAttributeType = ['Static', 'Output']
ParameterNames = ['Visualisation', 'Name of parameter 2', 'Name of parameter 3']
ParameterTypes = ['bool', 'int', 'float']
ParametersDefaultValues = [False, 0, 12.5]

# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    worker_exec = os.path.join(os.path.dirname(Exec), 'spinnaker_camera_worker.py')
    some_object_com = gu.start_the_communications_process(worker_exec)
    some_object_com.start_ioloop()
# </editor-fold>