
import os
from Heron import general_utils as gu

Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new nodes individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Timer'
NodeAttributeNames = ['Parameters', 'Signal Out']
NodeAttributeType = ['Static', 'Output']
ParameterNames = ['Visualisation', 'SignalOut', 'Delay Generator (sec)', 'a', 'b', 'c']
ParameterTypes = ['bool', 'str', 'list', 'float', 'float', 'float']
ParametersDefaultValues = [False, 'True',
                           ['constant: a=const', 'random uniform: a=min, b=max',
                            'random exponential: a=lambda',
                            'random truncated exponential: a=lambda, b=min, c=max',
                            'random gaussian: a=mu, b=sigma'],
                           0.0, 0.0, 0.0]
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'timer_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    timer_com = gu.start_the_source_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(timer_com.on_kill)
    timer_com.start_ioloop()
# </editor-fold>
