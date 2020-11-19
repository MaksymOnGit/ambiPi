import numpy
from picamera import PiCamera
from picamera.array import PiRGBArray, PiRGBAnalysis
from picamera.color import Color
import time
from signal import pause
from threading import Thread

from RPLCD.gpio import CharLCD
from gpiozero import Button
from LCDMenu import LCDMenu

from AmbiPiDB import AmbiPiDB

from rpi_ws281x import Adafruit_NeoPixel

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
DEBUG = False

gamma8: tuple = (
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,
    1,  1,  1,  1,  1,  1,  1,  1,  1,  2,  2,  2,  2,  2,  2,  2,
    2,  3,  3,  3,  3,  3,  3,  3,  4,  4,  4,  4,  4,  5,  5,  5,
    5,  6,  6,  6,  6,  7,  7,  7,  7,  8,  8,  8,  9,  9,  9, 10,
   10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16,
   17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25,
   25, 26, 27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 35, 36,
   37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50,
   51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68,
   69, 70, 72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 87, 89,
   90, 92, 93, 95, 96, 98, 99,101,102,104,105,107,109,110,112,114,
  115,117,119,120,122,124,126,127,129,131,133,135,137,138,140,142,
  144,146,148,150,152,154,156,158,160,162,164,167,169,171,173,175,
  177,180,182,184,186,189,191,193,196,198,200,203,205,208,210,213,
  215,218,220,223,225,228,231,233,236,239,241,244,247,249,252,255)

class FrameProcessor(PiRGBAnalysis):
    def __init__(self, camera: PiCamera, resolution: tuple, strip: Adafruit_NeoPixel, ledRes: tuple, sideStartIndexes: tuple, colorStrengths: tuple, gammaCorrection: bool):
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

        self.redLvl = colorStrengths[0]
        self.greenLvl = colorStrengths[1]
        self.blueLvl = colorStrengths[2]

        self.gamma = gammaCorrection

        print(chr(27)+'[2j')
        print('\033c')
        print('\x1bc')
        print("\033[?25l")

        self.counts = 0
        self.framerate = 0
        self.lastreport = time.time()

    def analyze(self, data):
        for i in range(1, self.ledW):   #TOP
            x = round(i * self.blockW)
            y = 0
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(0, i, r, g, b)
            self.strip.setPixelColorRGB(self.topStart + self.ledW - i, *self.processColor(r,g,b))

        for i in range(1, self.ledH):   #RIGHT
            x = self.procW-1
            y = round(i * self.blockH)
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(i, self.ledW-1, r, g, b)
            self.strip.setPixelColorRGB(self.rightStart + self.ledH - i, *self.processColor(r,g,b))

        for i in range(self.ledW-2, -1, -1):    #BOTTOM
            x = round(i * self.blockW)
            y = self.procH-1
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(self.ledH-1, i, r, g, b)
            self.strip.setPixelColorRGB(self.bottomStart + i, *self.processColor(r,g,b))

        for i in range(self.ledH-1, -1, -1):    #LEFT
            x = 0
            y = round(i * self.blockH)
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(i, 0, r, g, b)
            self.strip.setPixelColorRGB(self.leftStart + i, *self.processColor(r,g,b))

        self.strip.show()

        self.report()

    def processColor(self, r,g,b):
        if(self.gamma):
            r = gamma8[r]
            g = gamma8[g]
            b = gamma8[b]
        
        return (int(r * self.redLvl), int(g * self.greenLvl), int(b * self.blueLvl))

    def printAt(self, y, x, r, g, b, t):
        print(f'\033[{y+1};{x+1}H\033[38;2;{r};{g};{b}m{t}', end='')

    def printLED(self, y, x, r, g, b):
        if DEBUG:
            self.printAt(y, x*2, r, g, b, '██')

    def report(self):
        if (time.time()-self.lastreport)>1.0:
            self.lastreport = time.time()
            self.framerate = self.counts
            if DEBUG:
                self.printAt(23, 0, 255, 255, 255, self.counts)
            self.counts = 0
        self.counts +=1
    
    def getFramerate(self):
        return self.framerate
    
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

def changeLEDDirection(value, key, db, frameProc: FrameProcessor):
    db.setSetting(key, int(value))

def changeLEDPositioning(value, key, db, frameProc: FrameProcessor, strip: Adafruit_NeoPixel):
    if key == "ts":
        frameProc.topStart = value
    elif key == "rs":
        frameProc.rightStart = value
    elif key == "bs":
        frameProc.bottomStart = value
    elif key == "ls":
        frameProc.leftStart = value
    for i in range(0, LED_COUNT):
        strip.setPixelColorRGB(i,0,0,0)
    db.setSetting(key, int(value))

def changeLEDColorStrength(value, key, db, framProc: FrameProcessor):
    if key == "redlvl":
        frameProc.redLvl = value/100
    elif key == "greenlvl":
        frameProc.greenLvl = value/100
    elif key == "bluelvl":
        frameProc.blueLvl = value/100
    db.setSetting(key, int(value))

def switchGammaCorrection(value, key, db, framProc: FrameProcessor):
    frameProc.gamma = True if value == "On" else False
    db.setSetting(key, int(1 if value == "On" else 0))

with PiCamera(resolution=INPUT_RES, framerate=30) as camera:


    lcd = CharLCD(pin_rs=22, pin_rw=None, pin_e=27, pins_data=[6,13,19,26], numbering_mode=11, cols=16, rows=2)

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
    db.initSetting("redlvl", 60)
    db.initSetting("greenlvl", 60)
    db.initSetting("bluelvl", 60)
    db.initSetting("gamma", 1)


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
        ),
        (db.getSetting("redlvl")/100, db.getSetting("greenlvl")/100, db.getSetting("bluelvl")/100),
        bool(db.getSetting("gamma"))
    )

    menu.addItem("ledW", "LED res. width",    range(0,301), onChange=(changeLEDResolution, ("ledW", db, frameProc)), initValue=db.getSetting("ledW"))
    menu.addItem("ledH", "LED res. height",  range(0,301), onChange=(changeLEDResolution, ("ledH", db, frameProc)), initValue=db.getSetting("ledH"))
    menu.addItem("dir",  "LED direction", ("Clockwise", "Counter clockw."), onChange=(changeLEDDirection, ("dir", db, frameProc)), initValue=db.getSetting("dir"))

    menu.addItem("ts", "Top Start",    range(0,301), onChange=(changeLEDPositioning, ("ts", db, frameProc, strip)), initValue=db.getSetting("ts"))
    menu.addItem("rs", "Right Start",  range(0,301), onChange=(changeLEDPositioning, ("rs", db, frameProc, strip)), initValue=db.getSetting("rs"))
    menu.addItem("bs", "Bottom Start", range(0,301), onChange=(changeLEDPositioning, ("bs", db, frameProc, strip)), initValue=db.getSetting("bs"))
    menu.addItem("ls", "Left Start",   range(0,301), onChange=(changeLEDPositioning, ("ls", db, frameProc, strip)), initValue=db.getSetting("ls"))

    menu.addItem("redlvl", "Red strength",  range(0,101), onChange=(changeLEDColorStrength, ("redlvl", db, frameProc)), initValue=db.getSetting("redlvl"))
    menu.addItem("greenlvl", "Green strength", range(0,101), onChange=(changeLEDColorStrength, ("greenlvl", db, frameProc)), initValue=db.getSetting("greenlvl"))
    menu.addItem("bluelvl", "Blue strength",   range(0,101), onChange=(changeLEDColorStrength, ("bluelvl", db, frameProc)), initValue=db.getSetting("bluelvl"))

    menu.addItem("gamma", "Gamma correction",   ("Off", "On"), onChange=(switchGammaCorrection, ("gamma", db, frameProc)), initValue=db.getSetting("gamma"))
    menu.addMonitorItem("fps", "Framerate", sampleFrom=(frameProc.getFramerate, 0.5))

    camera.start_recording(frameProc, format='rgb', resize=PROC_RES)
    pause()