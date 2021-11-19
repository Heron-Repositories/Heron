
import sys
from os import path
import numpy as np

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import logging
import torch
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer

from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu
from Heron.Operations.Transforms.Transfer_Learning.TL_Cottonbud_Angle import tl_cottonbud_angle_com
from Heron.communication.transform_worker import TransformWorker

worker_object: TransformWorker
predictor = None
instance_threshold_score = 0.85


def put_boxes_on_image(image, outputs):
    v = Visualizer(image[:, :, ::-1], scale=1.0)
    v = v.draw_instance_predictions(outputs["instances"].to("cpu"))
    im = v.get_image()[:, :, ::-1].astype(np.uint8)

    return im


def get_parameters(worker_object):
    global predictor
    global calculate_image_with_boxes

    # The default value of the 1st parameter is a generic name that must always be changed. That is why the below is
    # a valid test of whether the parameters have been read
    if tl_cottonbud_angle_com.ParametersDefaultValues[0] == worker_object.parameters[0]:
        return False

    if predictor is None:
        cfg = get_cfg()
        cfg.merge_from_file(model_zoo.get_config_file(worker_object.parameters[0]))
        cfg.MODEL.WEIGHTS = worker_object.parameters[1]
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = worker_object.parameters[2]
        predictor = DefaultPredictor(cfg)

    return True


def calculate_stick_angle(outputs):

    instances = outputs['instances']
    center_of_bud_1 = None
    center_of_bud_2 = None
    angle = None

    if len(instances) > 1:
        for i in range(len(instances)):
            instance = instances[i]
            if instance.pred_classes == 3 and instance.scores > instance_threshold_score:
                bud_box = instance.pred_boxes
                center_of_bud = bud_box.get_centers()
                if center_of_bud_1 is None:
                    center_of_bud_1 = center_of_bud.flatten().flatten()
                else:
                    center_of_bud_2 = center_of_bud.flatten().flatten()

        if center_of_bud_1 is not None and center_of_bud_2 is not None:
            if center_of_bud_1[0] > center_of_bud_2[0]:
                zeroed_tensor = torch.subtract(center_of_bud_1, center_of_bud_2)
            else:
                zeroed_tensor = torch.subtract(center_of_bud_2, center_of_bud_1)
            zeroed_tensor = zeroed_tensor.to('cpu')
            cos = zeroed_tensor[0]/(zeroed_tensor[0].pow(2) + zeroed_tensor[1].pow(2)).pow(0.5)
            angle = -torch.rad2deg(torch.acos(cos))

            if zeroed_tensor[1] > 0:
                angle = -angle

    return angle


def detect(data, parameters):
    global worker_object
    global predictor

    image_with_predictions = np.array(np.random.random((100, 100)))
    worker_object.worker_visualisable_result = np.array(['Not calculated'])

    if data is None or parameters is None or predictor is None:
        logging.debug('Passed')
    else:
        try:
            calculate_image_with_boxes = parameters[3]

            message = data[1:]  # data[0] is the topic
            image = Socket.reconstruct_array_from_bytes_message_cv2correction(message)

            image = np.repeat(image[:, :, np.newaxis], 3, axis=2)
            outputs = predictor(image)
            angle = calculate_stick_angle(outputs)

            if angle is not None:
                angle = np.array([angle.tolist()])
                worker_object.worker_visualisable_result = angle
            else:
                worker_object.worker_visualisable_result = np.array(['Not Calculated'])

            if calculate_image_with_boxes:
                image_with_predictions = np.ascontiguousarray(put_boxes_on_image(image, outputs))

        except Exception as e:
            worker_object.worker_visualisable_result = np.array(['Error'])
            logging.debug('Detecting cottonbud angle {} operation failed'.format(worker_object.node_index))
            logging.debug(e)

    # The order in the list should be the same as the order of outputs shown on the Node from top to bottom.
    # The individual elements of the list should always have a value (not None) otherwise the order changes!
    results = [worker_object.worker_visualisable_result, image_with_predictions]

    return results


def on_end_of_life():
    global worker_object
    global predictor

    del worker_object
    del predictor


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(detect, on_end_of_life, get_parameters)
    worker_object.start_ioloop()
