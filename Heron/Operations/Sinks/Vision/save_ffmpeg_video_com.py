
import os
from Heron import general_utils as gu
Exec = os.path.realpath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new node's individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Save FFMPEG video'
NodeAttributeNames = ['Parameters', 'Frame In']
NodeAttributeType = ['Static', 'Input']
ParameterNames = ['File name', 'Pixel Format In', 'Pixel Format Out', 'Fps']
ParameterTypes = ['str', 'str', 'str', 'int']
ParametersDefaultValues = ['output.avi', 'bayer_rggb8', 'rgb24', 120]

# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    worker_exec = os.path.join(os.path.dirname(Exec), 'save_ffmpeg_video_worker.py')
    save_video_com = gu.start_the_sink_communications_process(worker_exec)
    save_video_com.start_ioloop()

# </editor-fold>
