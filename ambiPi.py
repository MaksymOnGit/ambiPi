import numpy
from picamera import PiCamera
from picamera.array import PiRGBArray, PiRGBAnalysis
from picamera.color import Color
import time
from signal import pause

from RPLCD.gpio import CharLCD
from RPi import GPIO
from gpiozero import Button
from LCDMenu import LCDMenu

from AmbiPiDB import AmbiPiDB

from rpi_ws281x import Adafruit_NeoPixel, Color

# LED strip configuration:
LED_COUNT      = 160      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

INPUT_RES = (1920, 1088)
PROC_RES = (64, 48)#(640,360)
LED_RES = (35, 21)
DEBUG = True
        

class FrameProcessor(PiRGBAnalysis):
    def __init__(self, camera: PiCamera, resolution: tuple, strip: Adafruit_NeoPixel, ledRes: tuple, sideStartIndexes: tuple):
        super(FrameProcessor, self).__init__(camera, size=resolution)

        self.strip = strip

        self.ledW = ledRes[0]
        self.ledH = ledRes[1]

        self.procW = PROC_RES[0]
        self.procH = PROC_RES[1]

        self.blockW = self.procW / self.ledW
        self.blockH = self.procH / self.ledH

        self.topStart = sideStartIndexes[0]
        self.rightStart = sideStartIndexes[1]
        self.bottomStart = sideStartIndexes[2]
        self.leftStart = sideStartIndexes[3]

        print(chr(27)+'[2j')
        print('\033c')
        print('\x1bc')
        print("\033[?25l")

        self.counts = 0
        self.lastreport = time.time()

    def analyze(self, data):

        for i in range(1, self.ledW):   #TOP
            x = round(i * self.blockW)
            y = 0
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(0, i, r, g, b)
            self.strip.setPixelColor(self.topStart + self.ledW - i, Color(r,g,b))
        self.strip.show()

        for i in range(1, self.ledH):   #RIGHT
            x = self.procW-1
            y = round(i * self.blockH)
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(i, self.ledW-1, r, g, b)
            self.strip.setPixelColor(self.rightStart + self.ledH - i, Color(r,g,b))
        self.strip.show()

        for i in range(self.ledW-2, -1, -1):    #BOTTOM
            x = round(i * self.blockW)
            y = self.procH-1
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(self.ledH-1, i, r, g, b)
            self.strip.setPixelColor(self.bottomStart + i, Color(r,g,b))
        self.strip.show()

        for i in range(self.ledH-1, -1, -1):    #LEFT
            x = 0
            y = round(i * self.blockH)
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(i, 0, r, g, b)
            self.strip.setPixelColor(self.leftStart + i, Color(r,g,b))
        self.strip.show()
        if DEBUG:
            self.report()

    def printAt(self, y, x, r, g, b, t):
        print(f'\033[{y+1};{x+1}H\033[38;2;{r};{g};{b}m{t}', end='')

    def printLED(self, y, x, r, g, b):
        if DEBUG:
            self.printAt(y, x*2, r, g, b, '██')

    def report(self):
        if (time.time()-self.lastreport)>1.0:
            self.lastreport = time.time()
            self.printAt(23, 0, 255, 255, 255, self.counts)
            self.counts = 0
        self.counts +=1
    
    @property
    def ledWidth(self):
        return self.ledW

    @ledWidth.setter
    def ledWidth(self, value):
        self.ledW = value
        self.blockW = self.procW / self.ledW

    @property
    def ledHeight(self):
        return self.ledH

    @ledHeight.setter
    def ledHeight(self, value):
        self.ledH = value
        self.blockH = self.procH / self.ledH


def changeBrightness(value, db, strip):
    db.setSetting("brght", int(value))
    strip.setBrightness(int(value))

def changeLEDResolution(value, key, db, frameProc: FrameProcessor):
    if key == "ledW":
        frameProc.ledWidth = value
    elif key == "ledH":
        frameProc.ledHeight = value
    db.setSetting(key, int(value))

def changeLEDDirection(value, key, db):
    db.setSetting(key, int(value))

def changeLEDPositioning(value, key, db, frameProc: FrameProcessor, strip: Adafruit_NeoPixel):
    if key == "ts":
        frameProc.topStart = value
    elif key == "rs":
        frameProc.rightStart = value
    elif key == "bs":
        frameProc.vottomStart = value
    elif key == "ls":
        frameProc.leftStart = value
    for i in range(0, LED_COUNT):
        strip.setPixelColorRGB(i,0,0,0)
    db.setSetting(key, int(value))

with PiCamera(resolution=INPUT_RES, framerate=30) as camera:


    lcd = CharLCD(pin_rs=22, pin_rw=None, pin_e=27, pins_data=[6,13,19,26], numbering_mode=GPIO.BCM, cols=16, rows=2)

    up = Button(17)
    down = Button(16)
    left = Button(20)
    right = Button(21)

    db = AmbiPiDB()

    db.initSetting("brght", 255)
    db.initSetting("ledW", 35)
    db.initSetting("ledH", 21)
    db.initSetting("dir", 0)
    db.initSetting("ts", 90)
    db.initSetting("rs", 65)
    db.initSetting("bs", 25)
    db.initSetting("ls", 129)


    brght = db.getSetting("brght")
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, db.getSetting("brght"), LED_CHANNEL)
    strip.begin()

    menu = LCDMenu(lcd, up, down, left, right)
    menu.addItem("brght", "Brightness", range(0,256), onChange=(changeBrightness, (db, strip)), initValue=db.getSetting("brght"))

    frameProc = FrameProcessor(camera, PROC_RES, strip, 
        (db.getSetting("ledW"), db.getSetting("ledH")), 
        (
            db.getSetting("ts"),
            db.getSetting("rs"),
            db.getSetting("bs"),
            db.getSetting("ls")
        ))

    menu.addItem("ledW", "LED res. width",    range(0,301), onChange=(changeLEDResolution, ("ledW", db, frameProc)), initValue=db.getSetting("ledW"))
    menu.addItem("ledH", "LED res. height",  range(0,301), onChange=(changeLEDResolution, ("ledH", db, frameProc)), initValue=db.getSetting("ledH"))
    menu.addItem("dir",  "LED direction", ("Clockwise", "Counter clockw."), onChange=(changeLEDDirection, ("dir", db, frameProc)), initValue=db.getSetting("dir"))

    menu.addItem("ts", "Top Start",    range(0,301), onChange=(changeLEDPositioning, ("ts", db, frameProc, strip)), initValue=db.getSetting("ts"))
    menu.addItem("rs", "Right Start",  range(0,301), onChange=(changeLEDPositioning, ("rs", db, frameProc, strip)), initValue=db.getSetting("rs"))
    menu.addItem("bs", "Bottom Start", range(0,301), onChange=(changeLEDPositioning, ("bs", db, frameProc, strip)), initValue=db.getSetting("bs"))
    menu.addItem("ls", "Left Start",   range(0,301), onChange=(changeLEDPositioning, ("ls", db, frameProc, strip)), initValue=db.getSetting("ls"))

    camera.start_recording(frameProc, format='rgb', resize=PROC_RES)
    pause()