
import cv2
import threading

import numpy as np


class Visualisation():
    def __init__(self, node_name, node_index):
        self.node_name = node_name
        self.node_index = node_index
        self.visualisation_on = False
        self.visualisation_thread = None
        self.visualised_data: np.ndarray
        self.running = True

    def set_new_visualisation_loop(self, new_visualisation_loop):
        """
        If a specific source_worker needs to do something else regarding visualisation then it needs to implement a
        visualisation loop function and pass it here by giving it as an argument to this function
        :param new_visualisation_loop: The new function that will deal with the node's visualisation
        :return: Nothing
        """
        self.visualisation_loop = new_visualisation_loop

    def visualisation_loop(self):
        """
        When the visualisation parameter in a node is set to True then this loop starts in a new visualisation thread.
        The thread terminates when the visualisation_on boolean is turned off
        :return: Nothing
        """
        window_showing = False

        while self.running:
            while self.visualisation_on:
                if not window_showing:
                    window_name = '{} {}'.format(self.node_name, self.node_index)
                    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                    cv2.imshow(window_name, self.visualised_data)
                    cv2.waitKey(1)
                    window_showing = True
                if window_showing:
                    try:
                        width = cv2.getWindowImageRect(window_name)[2]
                        height = cv2.getWindowImageRect(window_name)[3]
                        image = cv2.resize(self.visualised_data, (width, height), interpolation=cv2.INTER_AREA)
                        cv2.imshow(window_name, image)
                        cv2.waitKey(1)
                    except Exception as e:
                        print(e)

            cv2.destroyAllWindows()
            cv2.waitKey(1)
            window_showing = False
        print('hello')

    def visualisation_loop_update(self):
        """
        The function that is run at every cycle of the WORKER_FUNCTION to check if the visualisation_on bool is True
        for the first time. When that happens it starts the visualisation loop. The loop takes care of the showing
        and hiding of the visualisation window
        :return: Nothing
        """
        if self.visualisation_on and self.visualisation_thread is None:
            self.visualisation_thread = threading.Thread(target=self.visualisation_loop, daemon=True)
            self.visualisation_on = True
            self.visualisation_thread.start()

    def kill(self):
        if self.visualisation_on:
            self.visualisation_on = False
            cv2.waitKey(10)
        self.running = False
        cv2.waitKey(10)