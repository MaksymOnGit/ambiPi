import numpy
from picamera import PiCamera
from picamera.array import PiRGBArray, PiRGBAnalysis
from picamera.color import Color

INPUT_RES = (1920, 1088)
PROC_RES = (720, 480)

class FrameProcessor(PiRGBAnalysis):
    def __init__(self, camera, resolution):
        super(FrameProcessor, self).__init__(camera, size=resolution)

    def analyze(self, data):
        print(data.shape)

with PiCamera(resolution=INPUT_RES, framerate=25) as camera:
    camera.start_recording(FrameProcessor(camera, PROC_RES), format='rgb', resize=PROC_RES)
    camera.wait_recording(600)
    camera.stop_recording()