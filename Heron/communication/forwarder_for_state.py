
import zmq
from Heron import constants as ct


def main():
    print('Forwarder for State ON')
    try:
        context = zmq.Context(1)
        frontend = context.socket(zmq.SUB)
        #frontend.CONFLATE = 1
        frontend.bind("tcp://*:{}".format(ct.STATE_FORWARDER_SUBMIT_PORT))
        frontend.SUBSCRIBE = ""

        backend = context.socket(zmq.PUB)
        #backend.CONFLATE = 1
        backend.bind("tcp://*:{}".format(ct.STATE_FORWARDER_PUBLISH_PORT))

        capture = context.socket(zmq.PUB)
        capture.bind("tcp://*:{}".format(4000))

        zmq.proxy(frontend, backend, capture)

    except Exception as e:
        print(e)
        print("bringing down zmq device")
    finally:
        frontend.close()
        backend.close()
        context.term()


if __name__ == "__main__":
    main()