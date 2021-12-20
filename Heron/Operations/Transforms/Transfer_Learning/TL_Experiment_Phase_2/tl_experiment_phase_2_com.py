
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
BaseName = 'TL Experiment Phase 2'
NodeAttributeNames = ['Parameters', 'Levers Box In', 'Command to Screens', 'Command to Reward Poke']
NodeAttributeType = ['Static', 'Input', 'Output', 'Output']
ParameterNames = ['Reward On Poke', 'Reward On Poke Delay / sec', 'Trap On', 'Max Dist to Target', 'Speed deg/sec',
                  'Variable Targets', 'Must Lift at Target', '# Pellets']
ParameterTypes = ['bool', 'float', 'bool', 'int', 'float', 'bool', 'bool', 'int']
ParametersDefaultValues = [False, 0.0, True, 90, 25, False, False, 1]
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'tl_experiment_phase_2_worker.py')

# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    tl_experiment_phase_2_com = gu.start_the_transform_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(tl_experiment_phase_2_com.on_kill)
    tl_experiment_phase_2_com.start_ioloop()

# </editor-fold>
