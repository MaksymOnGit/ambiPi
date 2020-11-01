import numpy
from picamera import PiCamera
from picamera.array import PiRGBArray, PiRGBAnalysis
from picamera.color import Color
import time

INPUT_RES = (1920, 1088)
PROC_RES = (64, 48)#(640,360)
LED_RES = (37, 21)
        

class FrameProcessor(PiRGBAnalysis):
    def __init__(self, camera, resolution):
        super(FrameProcessor, self).__init__(camera, size=resolution)

        self.ledW = LED_RES[0]
        self.ledH = LED_RES[1]

        self.procW = PROC_RES[0]
        self.procH = PROC_RES[1]

        self.blockW = self.procW / self.ledW
        self.blockH = self.procH / self.ledH

        print(chr(27)+'[2j')
        print('\033c')
        print('\x1bc')
        print("\033[?25l")

        self.counts = 0
        self.lastreport = time.time()

    def analyze(self, data):
        for i in range(1, self.ledW):
            x = round(i * self.blockW)
            y = 0
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(0, i, r, g, b)

        for i in range(1, self.ledH):
            x = self.procW-1
            y = round(i * self.blockH)
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(i, self.ledW-1, r, g, b)

        for i in range(self.ledW-2, -1, -1):
            x = round(i * self.blockW)
            y = self.procH-1
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(self.ledH-1, i, r, g, b)

        for i in range(self.ledH-1, -1, -1):
            x = 0
            y = round(i * self.blockH)
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(i, 0, r, g, b)
        self.report()

    def printAt(self, y, x, r, g, b, t):
        print(f'\033[{y+1};{x+1}H\033[38;2;{r};{g};{b}m{t}', end='')

    def printLED(self, y, x, r, g, b):
        self.printAt(y, x*2, r, g, b, '██')

    def report(self):
        if (time.time()-self.lastreport)>1.0:
            self.lastreport = time.time()
            self.printAt(23, 0, 255, 255, 255, self.counts)
            self.counts = 0
        self.counts +=1


with PiCamera(resolution=INPUT_RES, framerate=30) as camera:
    camera.start_recording(FrameProcessor(camera, PROC_RES), format='rgb', resize=PROC_RES)
    camera.wait_recording(600)
    camera.stop_recording()