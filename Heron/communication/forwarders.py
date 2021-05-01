

import sys
import threading
import zmq
import time
from Heron import constants as ct

debug_data = False
debug_state = False
debug_proof_of_life = False


def data_forwarder_loop():
    global debug_data

    # if process is called with 'True' then it becomes verbose and sends all messages also to the capture port
    if debug_data:
        print('Forwarder for data is in debug mode (capture is on)')

    try:
        context = zmq.Context(1)
        frontend = context.socket(zmq.SUB)
        frontend.set_hwm(1)
        frontend.bind("tcp://*:{}".format(ct.DATA_FORWARDER_SUBMIT_PORT))
        frontend.SUBSCRIBE = ""

        backend = context.socket(zmq.PUB)
        backend.set_hwm(1)
        backend.bind("tcp://*:{}".format(ct.DATA_FORWARDER_PUBLISH_PORT))

        if debug_data:
            capture = context.socket(zmq.PUB)
            capture.bind("tcp://*:{}".format(ct.DATA_FORWARDER_CAPTURE_PORT))

            zmq.proxy(frontend, backend, capture)
        else:
            zmq.proxy(frontend, backend)

    except Exception as e:
        print(e)
        print("bringing down Forwarder for Data")


def state_forwarder_loop():
    global debug_state

    # if process is called with 'True' then it becomes verbose and sends all messages also to the capture port
    if debug_state:
        print('Forwarder for state is in debug mode (capture is on)')

    try:
        context = zmq.Context(1)
        frontend = context.socket(zmq.SUB)
        frontend.bind("tcp://*:{}".format(ct.STATE_FORWARDER_SUBMIT_PORT))
        frontend.SUBSCRIBE = ""

        backend = context.socket(zmq.PUB)
        backend.bind("tcp://*:{}".format(ct.STATE_FORWARDER_PUBLISH_PORT))

        if debug_state:
            capture = context.socket(zmq.PUB)
            capture.bind("tcp://*:{}".format(ct.STATE_FORWARDER_CAPTURE_PORT))

            zmq.proxy(frontend, backend, capture)
        else:
            zmq.proxy(frontend, backend)

    except Exception as e:
        print(e)
        print("bringing down Forwarder for State")


def proof_of_life_forwarder_loop():
    global debug_proof_of_life

    # if process is called with 'True' then it becomes verbose and sends all messages also to the capture port
    if debug_proof_of_life:
        print('Forwarder for proof of life is in debug mode (capture is on)')

    try:
        context = zmq.Context(1)
        frontend = context.socket(zmq.SUB)
        frontend.bind("tcp://*:{}".format(ct.PROOF_OF_LIFE_FORWARDER_SUBMIT_PORT))
        frontend.SUBSCRIBE = ""

        backend = context.socket(zmq.PUB)
        backend.bind("tcp://*:{}".format(ct.PROOF_OF_LIFE_FORWARDER_PUBLISH_PORT))

        if debug_proof_of_life:
            capture = context.socket(zmq.PUB)
            capture.bind("tcp://*:{}".format(ct.PROOF_OF_LIFE_FORWARDER_CAPTURE_PORT))

            zmq.proxy(frontend, backend, capture)
        else:
            zmq.proxy(frontend, backend)

    except Exception as e:
        print(e)
        print("bringing down Forwarder for State")


def main():
    global debug_data
    global debug_state
    global debug_proof_of_life

    args = sys.argv[1:]
    debug_data = args[0] == 'True'
    debug_state = args[1] == 'True'
    debug_proof_of_life = args[2] == 'True'

    data_thread = threading.Thread(target=data_forwarder_loop, daemon=True)
    data_thread.start()
    state_thread = threading.Thread(target=state_forwarder_loop, daemon=True)
    state_thread.start()
    proof_of_life_thread = threading.Thread(target=proof_of_life_forwarder_loop, daemon=True)
    proof_of_life_thread.start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()