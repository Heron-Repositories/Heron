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
# It is meant to create Node specific elements.
# This is where a new Node's individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Save Pandas DF'  # The base name can have spaces.

NodeAttributeNames = ['Parameters', 'Row In']
NodeAttributeType = ['Static', 'Input']
ParameterNames = ['Visualisation', 'Columns', 'File Name', 'Overwrite']
ParameterTypes = ['bool', 'str', 'str', 'bool']
ParametersDefaultValues = [False, 'Column 1, Column 2', r'C:\test.df', False]
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'save_pandas_df_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph.
#  You can refactor the name of the xxx_com variable but do not change anything else">
if __name__ == "__main__":
    #  In this case refactor the name sink_template_com to whatever_com
    save_pandas_df_com = gu.start_the_sink_communications_process()
    gu.register_exit_signals(save_pandas_df_com.on_kill)
    save_pandas_df_com.start_ioloop()
# </editor-fold>
