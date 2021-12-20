
import cv2
import threading

import numpy as np
from Heron import general_utils as gu


class Visualisation():
    def __init__(self, node_name, node_index):
        self.node_name = node_name
        self.node_index = node_index
        self.visualisation_on = False
        self.visualisation_thread = None
        self.checking_thread: threading.thread
        self.visualised_data = np.empty((100, 100))
        self.running = True
        self.window_showing = False
        self.set_new_visualisation_loop(self.visualisation_loop)

    def set_new_visualisation_loop(self, new_visualisation_loop):
        """
        If a specific source_worker needs to do something else regarding visualisation then it needs to implement a
        visualisation loop function and pass it here by giving it as an argument to this function
        :param new_visualisation_loop: The new function that will deal with the node's visualisation
        :return: Nothing
        """
        self.visualisation_loop = new_visualisation_loop

    @staticmethod
    def visualisation_loop(vis_object):
        """
        When the visualisation parameter in a node is set to True then this loop starts in a new visualisation thread.
        The thread terminates when the visualisation_on boolean is turned off. Because this is a static method it can
        be overridden by another loop from an xxx_worker script using the set_new_visualisation_loop
        :return: Nothing
        """
        while vis_object.running:
            while vis_object.visualisation_on:
                if not vis_object.window_showing:
                    window_name = '{} {}'.format(vis_object.node_name, vis_object.node_index)
                    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                    cv2.imshow(window_name, vis_object.visualised_data)
                    cv2.waitKey(1)
                    vis_object.window_showing = True
                if vis_object.window_showing:
                    try:
                        width = cv2.getWindowImageRect(window_name)[2]
                        height = cv2.getWindowImageRect(window_name)[3]
                        image = cv2.resize(vis_object.visualised_data, (width, height), interpolation=cv2.INTER_AREA)
                        cv2.imshow(window_name, image)
                        cv2.waitKey(1)
                    except Exception as e:
                        print(e)

            cv2.destroyAllWindows()
            cv2.waitKey(1)
            vis_object.window_showing = False

    def visualisation_loop_update(self):
        """
        The function that is run at every cycle of the WORKER_FUNCTION to check if the visualisation_on bool is True
        for the first time. When that happens it starts the visualisation loop. The loop takes care of the showing
        and hiding of the visualisation window.
        :return: Nothing
        """
        while not self.visualisation_on:
            cv2.waitKey(1)

        if self.visualisation_thread is None:
            self.visualisation_thread = threading.Thread(target=self.visualisation_loop, daemon=True, args=(self,))
            self.visualisation_on = True
            self.visualisation_thread.start()

    def visualisation_init(self):
        self.checking_thread = threading.Thread(target=self.visualisation_loop_update, daemon=True)
        self.checking_thread.start()

    def kill(self):
        self.window_showing = False
        if self.visualisation_on:
            self.visualisation_on = False
        self.running = False
        gu.accurate_delay(200)

