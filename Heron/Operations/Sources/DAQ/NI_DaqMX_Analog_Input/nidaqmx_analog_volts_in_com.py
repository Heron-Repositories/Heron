
import os
from Heron import general_utils as gu

Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new nodes individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'NIDAQ Analog Volt In'
NodeAttributeNames = ['Parameters', 'Voltage Out']
NodeAttributeType = ['Static', 'Output']
ParameterNames = ['Visualisation', 'Device_name/channel_name', 'Acq. Rate', 'Sample Mode', 'Buffer Size']
ParameterTypes = ['bool', 'str', 'int', 'list', 'int']
ParametersDefaultValues = [False, 'Dev1/ai0', 20000, ['CONTINUOUS', 'FINITE', 'HW_TIMED_SINGLE_POINT'], 1000]
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'nidaqmx_analog_volts_in_worker.py')
# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    nidaqmx_analog_volt_in_com = gu.start_the_source_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(nidaqmx_analog_volt_in_com.on_kill)
    nidaqmx_analog_volt_in_com.start_ioloop()
# </editor-fold>
