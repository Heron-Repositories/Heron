# This is the code that defines the Parameters, Inputs and Outputs of the Node. Most of the code should not be
# changed. The only parts that should be changed are the information in the lists of the properties of the Node and the
# name of the xxx_com variable under the if __name__ == "__main__": clause


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

Exec = os.path.abspath(__file__)
# </editor-fold>

# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new node's individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Source Template'  # The base name can have spaces.
NodeAttributeNames = ['Parameters', 'Something Out 1']
# The names of the output of the Node. Currently the Source Node supports only a single output. In the future it will
# support multiple outputs.
# If the Node has any parameters then the first name has to be Parameters. This is neither an input or an output but
# provides space on the Node to show parameter widgets.

NodeAttributeType = ['Static', 'Output']  # Whether the above names are outputs or inputs. A Source can only have
# a single Output. If the first attribute name is Parameters then the first attribute type must be Static
# (i.e. neither an Output nor and Input). So for a Source Node the only possible combinations of NodeAttributeType are
# ['Static', 'Output'] or ['Output']

ParameterNames = ['Visualisation', 'Parameter 1', 'Parameter 2', 'Parameter 3', 'Parameter 4']  # If there are
# parameters then write their names here. If there are not make an empty list (i.e. ParameterNames = [])

ParameterTypes = ['bool', 'str', 'list', 'float', 'int']  # The types of the parameters (in string form).
# types allowed are: 'bool', 'str', 'list', 'int' and 'float'. Again for no parameters make an empty list.

ParametersDefaultValues = [False,
                           'True',
                           ['item 1',
                            'item 2'],
                           0.0,
                           2]  # The default values of each parameter.  These are the values the Node will
# have when first created into the Node Editor. Parameter of 'list' type become drop down menus and the list of their
# default values becomes the drop down menu items. The Node by default uses the first item (so the order matters).

# The following line needs to exist with the correct name for the xxx_worker.py script
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'source_template_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph.
#  You can refactor the name of the xxx_com variable but do not change anything else">
if __name__ == "__main__":
    source_template_com = gu.start_the_source_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(source_template_com.on_kill)
    source_template_com.start_ioloop()
# </editor-fold>
