from RPLCD.gpio import CharLCD
from RPi import GPIO
from gpiozero import Button
from time import sleep
from threading import Thread

class LCDMenuItem:
    def __init__(self, text: str, values: tuple=None, initValue=None, callback=None):
        self.text = text
        self.values = values
        self.callbackFnc = callback
        self.value = initValue if initValue != None else 0

    def next(self):
        if self.values == None:
            self.value += 1
            return self.value
        self.value = self.value + 1 if self.value < len(self.values) - 1 else 0
        return self.values[self.value]
        
    def prev(self):
        if self.values == None:
            self.value -= 1
            return self.value
        self.value = self.value - 1 if self.value > 0 else len(self.values) - 1
        return self.values[self.value]

    def get(self):
        if self.values == None:
            return self.value
        return self.values[self.value]

    def callback(self, val):
        if self.callbackFnc == None:
            return
        if type(self.callbackFnc) is tuple:
            self.callbackFnc[0](val, *(self.callbackFnc[1]))
        else:
            self.callbackFnc(val)

class LCDMenuMonitorItem:
    def __init__(self, text: str, sample):
        self.text = text
        self.sample = sample[0]
        self.sleep = sample[1]

    def get(self):
        return self.sample()

    def next(self):
        return self.sample()

    def prev(self):
        return self.sample()

    def callback(self, val):
        return None


class LCDMenu:
    def __init__(self, lcd: CharLCD, btnUp: Button, btnDown: Button, btnLeft: Button, btnRight: Button):
        self.lcd: CharLCD = lcd
        self.up: Button = btnUp
        self.down: Button = btnDown
        self.left: Button = btnLeft
        self.right: Button = btnRight
        self.up.when_deactivated = self._onUp
        self.down.when_deactivated = self._onDown
        self.left.when_deactivated = self._onLeft
        self.right.when_deactivated = self._onRight
        self.left.when_held = self._onHoldLeft
        self.right.when_held = self._onHoldRight
        self._selected = None
        self._selectedItem = None
        self._items = {}
        self._itemKeys: list = []
    
    def _onUp(self):
        self._selected = self._selected - 1 if self._selected > 0 else len(self._itemKeys) - 1
        self._onSelect()

    def _onDown(self):
        self._selected = self._selected + 1 if self._selected < len(self._itemKeys) - 1 else 0
        self._onSelect()

    def _onSelect(self):
        self.lcd.clear()
        self.lcd.cursor_pos = (0,0)
        self._selectedItem = self._items[self._itemKeys[self._selected]]
        self.lcd.write_string(f'{self._selectedItem.text}')
        self.lcd.cursor_pos = (1,0)
        self.lcd.write_string(f'{self._selectedItem.get()}')

        if(type(self._selectedItem) == LCDMenuMonitorItem):
            def task():
                while type(self._selectedItem) == LCDMenuMonitorItem:
                    self._clearLine(1)
                    self.lcd.write_string(f'{self._selectedItem.get()}')
                    sleep(self._selectedItem.sleep)
            t = Thread(target=task)
            t.start()

        

    def _onLeft(self, withCallback=True):
        if(type(self._selectedItem) == LCDMenuItem):
            self._clearLine(1)
            val = self._selectedItem.prev()
            self.lcd.write_string(f'{val}')
            if withCallback:
                self._selectedItem.callback(val)

    def _onHoldLeft(self):
        self.left.when_deactivated = None
        while self.left.is_held:
            self._onLeft(False)
            sleep(0.1)
        self._onLeft()
        self.left.when_deactivated = self._onLeft

    def _onRight(self, withCallback=True):
        if(type(self._selectedItem) == LCDMenuItem):
            self._clearLine(1)
            val = self._selectedItem.next()
            self.lcd.write_string(f'{val}')
            if withCallback:
                self._selectedItem.callback(val)

    def _onHoldRight(self):
        self.right.when_deactivated = None
        while self.right.is_held:
            self._onRight(False)
            sleep(0.1)
        self._onRight()
        self.right.when_deactivated = self._onRight

    def _clearLine(self, line):
        self.lcd.cursor_pos = (line,0)
        self.lcd.write_string("                ")
        self.lcd.cursor_pos = (line,0)

    
    def addItem(self, key, name, values: tuple=None, initValue=None, onChange: tuple=None):
        self._items[key] = LCDMenuItem(text=name, values=values, initValue=initValue, callback=onChange)
        self._itemKeys.append(key)
        if self._selected == None:
            self._selected = 0
            self._onDown()
    
    def addMonitorItem(self, key, name, sampleFrom: tuple):
        self._items[key] = LCDMenuMonitorItem(text=name, sample=sampleFrom)
        self._itemKeys.append(key)
        if self._selected == None:
            self._selected = 0
            self._onDown()

    def __getitem__(self, key):
        return self._items[key].get()