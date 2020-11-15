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
    def __init__(self, camera, resolution, strip):
        super(FrameProcessor, self).__init__(camera, size=resolution)

        self.strip = strip

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

        for i in range(1, self.ledW):   #TOP
            x = round(i * self.blockW)
            y = 0
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(0, i, r, g, b)
            self.strip.setPixelColor(90 + i, Color(r,g,b))
        self.strip.show()

        for i in range(1, self.ledH):   #RIGHT
            x = self.procW-1
            y = round(i * self.blockH)
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(i, self.ledW-1, r, g, b)
            self.strip.setPixelColor(65 + i, Color(r,g,b))
        self.strip.show()

        for i in range(self.ledW-2, -1, -1):    #BOTTOM
            x = round(i * self.blockW)
            y = self.procH-1
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(self.ledH-1, i, r, g, b)
            self.strip.setPixelColor(25 + i, Color(r,g,b))
        self.strip.show()

        for i in range(self.ledH-1, -1, -1):    #LEFT
            x = 0
            y = round(i * self.blockH)
            r=int(data[y, x, 0])
            g=int(data[y, x, 1])
            b=int(data[y, x, 2])
            self.printLED(i, 0, r, g, b)
            self.strip.setPixelColor(129 + i, Color(r,g,b))
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



with PiCamera(resolution=INPUT_RES, framerate=30) as camera:
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    lcd = CharLCD(pin_rs=22, pin_rw=None, pin_e=27, pins_data=[6,13,19,26], numbering_mode=GPIO.BCM, cols=16, rows=2)

    up = Button(17)
    down = Button(16)
    left = Button(20)
    right = Button(21)

    def changeBrightness(value):
        strip.setBrightness(int(value))

    menu = LCDMenu(lcd, up, down, left, right)
    menu.addItem("brght", "Brightness", range(0,255), onChange=changeBrightness, initValue=100)
    menu.addItem("clr", "Colors", ("Red", "Green", "Blue", "Black", "White", "Grey", "Yellow", "Pink"), initValue="Black")
    menu.addItem("ne", "First non exist", ("First", "Second", "Third", "Fourth"))
    menu.addItem("ne", "First non exist", ("First", "Second", "Third", "Fourth"))

    camera.start_recording(FrameProcessor(camera, PROC_RES, strip), format='rgb', resize=PROC_RES)
    pause()