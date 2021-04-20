

import os
import sys
from Heron.communication.transform_com import TransformCom
global Exec
Exec = os.path.realpath(__file__)

# Properties of the generated Node
BaseName = 'Canny'
NodeAttributeNames = ['Frame In', 'Edges Out']
NodeAttributeType = ['Input', 'Output']


def main():
    """
    Creates a TransformCom object for the Canny transformation
    (i.e. initialises the canny_worker process and keeps the zmq communication between the worker
    and the forwarders)
    The pull_port is the port that the canny_com uses to pull data from the canny_worker
    The push_port is the port that the canny_com uses to push data to the canny_worker
    :return: Nothing (continuous loop)
    """
    global Exec

    args = sys.argv[1:]
    assert len(args) == 4, 'There should be 4 arguments passed to the Canny process.' \
                           'The sending_topic, the receiving_topic, the push_port and the pull_port'
    push_port = args[0]
    pull_port = args[1]
    receiving_topic = args[2]
    sending_topic = args[3]

    worker_exec = os.path.join(os.path.dirname(Exec), 'canny_worker.py')

    canny_com = TransformCom(sending_topic=sending_topic, receiving_topic=receiving_topic, push_port=push_port,
                             pull_port=pull_port, worker_exec=worker_exec, verbose=True)
    canny_com.connect_sockets()
    canny_com.start_worker()
    canny_com.start_ioloop()


if __name__ == "__main__":
    main()