
import zmq
from Heron import constants as ct
import sys


def main():
    args = sys.argv[1:]
    debug = args[0] == 'True'

    # if process is called with 'True' then it becomes verbose and sends all messages also to the capture port
    if debug:
        print('Forwarder for state is in debug mode (capture is on)')

    try:
        context = zmq.Context(1)
        frontend = context.socket(zmq.SUB)
        #frontend.CONFLATE = 1
        frontend.bind("tcp://*:{}".format(ct.STATE_FORWARDER_SUBMIT_PORT))
        frontend.SUBSCRIBE = ""

        backend = context.socket(zmq.PUB)
        #backend.CONFLATE = 1
        backend.bind("tcp://*:{}".format(ct.STATE_FORWARDER_PUBLISH_PORT))

        if debug:
            capture = context.socket(zmq.PUB)
            capture.bind("tcp://*:{}".format(ct.STATE_FORWARDER_CAPTURE_PORT))

            zmq.proxy(frontend, backend, capture)
        else:
            zmq.proxy(frontend, backend)

    except Exception as e:
        print(e)
        print("bringing down Forwarder for State")


if __name__ == "__main__":
    main()