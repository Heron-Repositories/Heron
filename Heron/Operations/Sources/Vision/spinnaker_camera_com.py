
import os
import sys
from Heron.communication import source_com as sc
global Exec
Exec = os.path.realpath(__file__)

# Properties of the generated Node
BaseName = 'Spinnaker Camera'
NodeAttributeNames = ['Frame Out']
NodeAttributeType = ['Output']


def main():
    """
    Creates a SourceCom object for a Spinnaker based camera
    (i.e. initialises the spinnaker_camera_worker process and keeps the zmq communication between the worker
    and the forwarders)
    :return: Nothing (continuous loop)
    """
    global Exec

    args = sys.argv[1:]
    assert len(args) == 2, 'There should be 2 arguments passed to the Spinnaker camera process. ' \
                           'The sending_topic and the push_port'
    push_port = args[0]
    sending_topic = args[1]


    worker_exec = os.path.join(os.path.dirname(Exec), 'spinnaker_camera_worker.py')

    spin_camera_com = sc.SourceCom(topic=sending_topic, port=push_port, worker_exec=worker_exec, verbose=True)

    spin_camera_com.connect_sockets()
    spin_camera_com.start_worker()
    spin_camera_com.start_ioloop()


if __name__ == "__main__":
    main()