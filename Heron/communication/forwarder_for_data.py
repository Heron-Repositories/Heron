
import zmq
from Heron import constants as ct


def main():
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

        zmq.proxy(frontend, backend)

    except Exception as e:
        print(e)
        print("bringing down zmq device")
    finally:
        pass
        frontend.close()
        backend.close()
        context.term()


if __name__ == "__main__":
    main()