
import sys
import threading
import zmq
import zmq.ssh
import time
import sys
import os
from os.path import dirname
sys.path.insert(0, dirname(dirname(dirname(os.path.realpath(__file__)))))
from Heron import constants as ct, general_utils as gu

debug_data = False
debug_parameters = False
debug_proof_of_life = False
all_proxies = []
all_sockets = []
all_contexts = []


def data_forwarder_loop():
    global debug_data
    global all_proxies
    global all_sockets
    global all_contexts

    # if process is called with 'True' then it becomes verbose and sends all messages also to the capture port
    if debug_data:
        print('Forwarder for data is in debug mode (capture is on)')

    try:
        context = zmq.Context(1)
        all_contexts.append(context)

        frontend = context.socket(zmq.SUB)
        frontend.setsockopt(zmq.LINGER, 0)
        frontend.set_hwm(2)
        frontend.bind("tcp://*:{}".format(ct.DATA_FORWARDER_SUBMIT_PORT))
        frontend.SUBSCRIBE = ""

        backend = context.socket(zmq.PUB)
        backend.setsockopt(zmq.LINGER, 0)
        backend.set_hwm(2)
        backend.bind("tcp://*:{}".format(ct.DATA_FORWARDER_PUBLISH_PORT))

        all_sockets.append(frontend)
        all_sockets.append(backend)

        if debug_data:
            capture = context.socket(zmq.PUB)
            capture.bind("tcp://*:{}".format(ct.DATA_FORWARDER_CAPTURE_PORT))
            all_sockets.append(capture)

            all_proxies.append(zmq.proxy(frontend, backend, capture))
        else:
            all_proxies.append(zmq.proxy(frontend, backend))

    except Exception as e:
        print("Closing down Forwarder for Data because {}\n".format(e))


def parameters_forwarder_loop():
    global debug_parameters
    global all_proxies
    global all_sockets
    global all_contexts

    # if process is called with 'True' then it becomes verbose and sends all messages also to the capture port
    if debug_parameters:
        print('Forwarder for parameters is in debug mode (capture is on)')

    try:
        context = zmq.Context(1)
        all_contexts.append(context)

        frontend = context.socket(zmq.SUB)
        frontend.setsockopt(zmq.LINGER, 0)
        frontend.bind("tcp://*:{}".format(ct.PARAMETERS_FORWARDER_SUBMIT_PORT))
        frontend.SUBSCRIBE = ""

        backend = context.socket(zmq.PUB)
        backend.setsockopt(zmq.LINGER, 0)
        backend.bind("tcp://*:{}".format(ct.PARAMETERS_FORWARDER_PUBLISH_PORT))

        all_sockets.append(frontend)
        all_sockets.append(backend)

        if debug_parameters:
            capture = context.socket(zmq.PUB)
            capture.bind("tcp://*:{}".format(ct.PARAMETERS_FORWARDER_CAPTURE_PORT))
            all_sockets.append(capture)
            all_proxies.append(zmq.proxy(frontend, backend, capture))
        else:
            all_proxies.append(zmq.proxy(frontend, backend))

    except Exception as e:
        print("Closing down Forwarder for Parameters because {}\n".format(e))


def proof_of_life_forwarder_loop():
    global debug_proof_of_life
    global all_proxies
    global all_sockets
    global all_contexts

    # if process is called with 'True' then it becomes verbose and sends all messages also to the capture port
    if debug_proof_of_life:
        print('Forwarder for proof of life is in debug mode (capture is on)')

    try:
        context = zmq.Context(1)
        all_contexts.append(context)

        frontend = context.socket(zmq.SUB)
        frontend.setsockopt(zmq.LINGER, 0)
        frontend.bind("tcp://*:{}".format(ct.PROOF_OF_LIFE_FORWARDER_SUBMIT_PORT))
        frontend.SUBSCRIBE = ""

        backend = context.socket(zmq.PUB)
        backend.setsockopt(zmq.LINGER, 0)
        backend.bind("tcp://*:{}".format(ct.PROOF_OF_LIFE_FORWARDER_PUBLISH_PORT))

        all_sockets.append(frontend)
        all_sockets.append(backend)

        if debug_proof_of_life:
            capture = context.socket(zmq.PUB)
            capture.bind("tcp://*:{}".format(ct.PROOF_OF_LIFE_FORWARDER_CAPTURE_PORT))
            all_sockets.append(capture)
            all_proxies.append(zmq.proxy(frontend, backend, capture))
        else:
            all_proxies.append(zmq.proxy(frontend, backend))

        all_sockets.append(frontend, backend)

    except Exception as e:
        print("Closing down Forwarder for Proof of Life because {}\n".format(e))


def close_all_sockets(signal, frame):
    global all_proxies
    global all_sockets
    global all_contexts

    for socket in all_sockets:
        try:
            socket.close()
        except Exception as e:
            print('Trying to close down socket: {} resulted in error: {}'.format(socket, e))

    for context in all_contexts:
        context.term()


def main():
    global debug_data
    global debug_parameters
    global debug_proof_of_life

    gu.register_exit_signals(close_all_sockets)

    args = sys.argv[1:]
    debug_data = args[0] == 'True'
    debug_parameters = args[1] == 'True'
    debug_proof_of_life = args[2] == 'True'

    data_thread = threading.Thread(target=data_forwarder_loop, daemon=True)
    data_thread.start()
    parameters_thread = threading.Thread(target=parameters_forwarder_loop, daemon=True)
    parameters_thread.start()
    proof_of_life_thread = threading.Thread(target=proof_of_life_forwarder_loop, daemon=True)
    proof_of_life_thread.start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()