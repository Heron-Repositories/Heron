
import PySpin
import cv2 as cv2
import os
import threading
from Heron import general_utils as gu
from Heron.Operations.Sources.Vision import spinnaker_camera_com
from Heron.communication.source_worker import SourceWorker
from PySpin.PySpin import CameraPtr
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

worker_object: SourceWorker
cam: CameraPtr

recording_on = False
fps = 0

# The following variables must be global so that they do not die after the start_acquisition function exits
system = None
cam_list = None
nodemap_tldevice = None
sNodemap = None


def setup_camera_and_start_acquisition(camera_index, pixel_format, fps):
    """
    This function sets up the camera

    :return: True if successful, False otherwise.
    :rtype: bool
    """

    global cam
    global system
    global cam_list
    global nodemap_tldevice
    global sNodemap

    system = PySpin.System.GetInstance()

    # Retrieve list of cameras from the system
    cam_list = system.GetCameras()
    num_cameras = cam_list.GetSize()

    print('Number of cameras detected: %d' % num_cameras)

    # Finish if there are no cameras
    if num_cameras == 0:
        # Clear camera list before releasing system
        cam_list.Clear()
        # Release system instance
        system.ReleaseInstance()
        print('No cameras detected!')
        return False

    # Get the camera with the required index
    for i, camera in enumerate(cam_list):
        if i == camera_index:
            cam = camera
            print('Found camera {}'.format(i))
    if cam is None:
        print("Didn't find camera with index {}".format(camera_index))
        return False

    try:
        nodemap_tldevice = cam.GetTLDeviceNodeMap()
        # Initialize camera
        cam.Init()

        # Retrieve GenICam nodemap
        nodemap = cam.GetNodeMap()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    sNodemap = cam.GetTLStreamNodeMap()

    # ------------------------------
    # Change bufferhandling mode to NewestOnly
    node_bufferhandling_mode = PySpin.CEnumerationPtr(sNodemap.GetNode('StreamBufferHandlingMode'))
    if not PySpin.IsAvailable(node_bufferhandling_mode) or not PySpin.IsWritable(node_bufferhandling_mode):
        print('Unable to set stream buffer handling mode.. Aborting...')
        return False

    # Retrieve entry node from enumeration node
    node_newestonly = node_bufferhandling_mode.GetEntryByName('NewestOnly')
    if not PySpin.IsAvailable(node_newestonly) or not PySpin.IsReadable(node_newestonly):
        print('Unable to set stream buffer handling mode.. Aborting...')
        return False

    node_newestonly_mode = node_newestonly.GetValue()
    node_bufferhandling_mode.SetIntValue(node_newestonly_mode)
    # ------------------------------

    try:
        # ------------------------------
        # Setup Acquisition to Continuous
        node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
        if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
            print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
            return False

        # Retrieve entry node from enumeration node
        node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
        if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
                node_acquisition_mode_continuous):
            print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
            return False

        acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
        node_acquisition_mode.SetIntValue(acquisition_mode_continuous)
        # ------------------------------

        # ------------------------------
        # Set the Pixel Format to BayerRG8
        node_pixel_format_enum = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
        if not PySpin.IsAvailable(node_pixel_format_enum) or not PySpin.IsWritable(node_pixel_format_enum):
            print('Unable to set Pixel Format to {} (enum retrieval). Aborting...'.format(pixel_format))
            return False
        node_pixel_format = node_pixel_format_enum.GetEntryByName(pixel_format)
        if not PySpin.IsAvailable(node_pixel_format) or not PySpin.IsReadable(node_pixel_format):
            print('Unable to set Pixel Format to {} (entry retrieval). Aborting...'.format(pixel_format))
            return False

        pixel_format_BayerRG8 = node_pixel_format.GetValue()
        node_pixel_format_enum.SetIntValue(pixel_format_BayerRG8)
        # ------------------------------

        # ------------------------------
        # Set Acquisition Frame Rate
        node_acqFrameRate_float = PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate"))
        node_acqFrameRate_float.SetValue(fps)
        print('Running Spinnaker Camera with {} FPS'.format(node_acqFrameRate_float.GetValue()))
        # ------------------------------

        # ------------------------------
        #  Begin acquiring images
        cam.BeginAcquisition()
        print('Acquiring images...')
        # ------------------------------

        '''
        device_serial_number = ''
        node_device_serial_number = PySpin.CStringPtr(nodemap_tldevice.GetNode('DeviceSerialNumber'))
        if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
            device_serial_number = node_device_serial_number.GetValue()
            print('Device serial number retrieved as %s...' % device_serial_number)
        '''

    except PySpin.SpinnakerException as ex:
        print('Error capturing frame from Spinnaker camera: {}'.format(ex))
        return False

    return True


def grab_frame():
    global cam

    try:
        image_result = cam.GetNextImage(1000)

        #  Ensure image completion
        if image_result.IsIncomplete():
            print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
        else:
            # Getting the image data as a numpy array and change it to an RGB format
            image_data = image_result.GetNDArray()
            #image_data = cv2.cvtColor(image_data, cv2.COLOR_BAYER_RG2RGB)
        image_result.Release()

    except PySpin.SpinnakerException as ex:
        print('Error capturing frame from Spinnaker camera: {}'.format(ex))
        return False

    return image_data


def new_visualisation():
    global worker_object

    while worker_object.visualisation_on:
        window_name = '{} {}'.format(worker_object.name, worker_object.index)
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        width = 400
        height = 200
        try:
            image = cv2.cvtColor(worker_object.worker_result, cv2.COLOR_BAYER_RG2RGB)
            image = cv2.resize(image, (height, width), interpolation=cv2.INTER_AREA)

            cv2.imshow(window_name, image)
            cv2.waitKey(1)
        except:
            pass
    cv2.destroyAllWindows()


def run_spinnaker_camera(_worker_object):
    global recording_on
    global worker_object
    worker_object = _worker_object
    cam_index = None
    worker_object.set_new_visualisation_loop(new_visualisation)

    if not recording_on:  # Get the parameters from the node
        while not recording_on:
            try:
                cam_index = worker_object.parameters[1]
                pixel_format = worker_object.parameters[2]
                fps = int(worker_object.parameters[3])
                recording_on = True

                print('Got Spinnaker camera parameters. Starting capture')
            except:
                cv2.waitKey(1)

        if not setup_camera_and_start_acquisition(cam_index, pixel_format, fps):
            recording_on = False

    # The infinite loop that does the frame capture and push to the output of the node
    while recording_on:
        worker_object.worker_result = grab_frame()
        worker_object.socket_push_data.send_array(worker_object.worker_result, copy=False)

        try:
            worker_object.visualisation_on = worker_object.parameters[0]
        except:
            worker_object.visualisation_on = spinnaker_camera_com.ParametersDefaultValues[0]

        worker_object.visualisation_toggle()


def on_end_of_life():
    global cam
    try:
        cam.EndAcquisition()
        cam.DeInit()
    except:
        pass
    del cam


if __name__ == "__main__":
    gu.start_the_source_worker_process(run_spinnaker_camera, on_end_of_life)