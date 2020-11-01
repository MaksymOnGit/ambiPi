import numpy
from picamera import PiCamera
from picamera.array import PiRGBArray, PiRGBAnalysis
from picamera.color import Color
import time

INPUT_RES = (1920, 1088)
PROC_RES = (640, 360)
LED_RES = (37, 21)
        

class FrameProcessor(PiRGBAnalysis):
    def __init__(self, camera, resolution):
        super(FrameProcessor, self).__init__(camera, size=resolution)
        self.fullW = PROC_RES[0] if PROC_RES else INPUT_RES[0]
        self.fullH = PROC_RES[1] if PROC_RES else INPUT_RES[1]
        self.blockW = self.fullW//LED_RES[0]
        self.blockH = self.fullH//LED_RES[1]

        print(chr(27)+'[2j')
        print('\033c')
        print('\x1bc')
        print("\033[?25l")

        self.counts = 0
        self.lastreport = time.time()

    def analyze(self, data):
        for i in range(self.blockW, self.fullW, self.blockW):
            r=int(numpy.mean(data[0:self.blockH, i:i+self.blockW, 0]))
            g=int(numpy.mean(data[0:self.blockH, i:i+self.blockW, 1]))
            b=int(numpy.mean(data[0:self.blockH, i:i+self.blockW, 2]))
            self.printAt(1, (i*2)//self.blockW, r, g, b, '██')
                
        for i in range(self.blockH, self.fullH-self.blockH, self.blockH):
            r=int(numpy.mean(data[i:i+self.blockH, self.fullW-self.blockW:self.fullW, 0]))
            g=int(numpy.mean(data[i:i+self.blockH, self.fullW-self.blockW:self.fullW, 1]))
            b=int(numpy.mean(data[i:i+self.blockH, self.fullW-self.blockW:self.fullW, 2]))
            self.printAt((i+self.blockH)//self.blockH, 74, r, g, b, '██')
            
        for i in range(self.fullW-self.blockW, 0, -self.blockW):
            r=int(numpy.mean(data[self.fullH-self.blockH-1:self.fullH-1, i:i+self.blockW, 0]))
            g=int(numpy.mean(data[self.fullH-self.blockH-1:self.fullH-1, i:i+self.blockW, 1]))
            b=int(numpy.mean(data[self.fullH-self.blockH-1:self.fullH-1, i:i+self.blockW, 2]))
            self.printAt(21, (i*2//self.blockW), r, g, b, '██')
            
        for i in range(self.fullH-self.blockH, 0, -self.blockH):
            r=int(numpy.mean(data[i:i+self.blockH, 0:self.blockW, 0]))
            g=int(numpy.mean(data[i:i+self.blockH, 0:self.blockW, 1]))
            b=int(numpy.mean(data[i:i+self.blockH, 0:self.blockW, 2]))
            self.printAt(i//self.blockH, 1, r, g, b, '██')
        self.report()

    def printAt(self, y, x, r, g, b, t):
        print(f'\033[{y};{x}H\033[38;2;{r};{g};{b}m{t}', end='')

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