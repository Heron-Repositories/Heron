
import sys
import zmq
from Heron import constants as ct


def main():
    args = sys.argv[1:]
    debug = args == 'True'
    # if process is called with 'True' then it becomes verbose and sends all messages also to the capture port
    if debug:
        print("Forwarder for Data ON")

    try:
        context = zmq.Context(1)
        frontend = context.socket(zmq.SUB)
        frontend.set_hwm(1)
        frontend.bind("tcp://*:{}".format(ct.DATA_FORWARDER_SUBMIT_PORT))
        frontend.SUBSCRIBE = ""

        backend = context.socket(zmq.PUB)
        backend.set_hwm(1)
        backend.bind("tcp://*:{}".format(ct.DATA_FORWARDER_PUBLISH_PORT))

        if debug:
            capture = context.socket(zmq.PUB)
            capture.bind("tcp://*:{}".format(ct.DATA_FORWARDER_CAPTURE_PORT))

            zmq.proxy(frontend, backend, capture)
        else:
            zmq.proxy(frontend, backend)

    except Exception as e:
        print(e)
        print("bringing down Forwarder for Data")


if __name__ == "__main__":
    main()