from RPLCD.gpio import CharLCD
from RPi import GPIO
from gpiozero import Button
from time import sleep

class LCDMenuItem:
    def __init__(self, text: str, values: tuple=None, initValue=None, callback=None):
        self.text = text
        self.values = values
        self.callback = callback
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
        self._items = {}
        self._itemKeys: list = []
    
    def _onUp(self):
        self.lcd.clear()
        self.lcd.cursor_pos = (0,0)
        self._selected = self._selected - 1 if self._selected > 0 else len(self._itemKeys) - 1
        item = self._items[self._itemKeys[self._selected]]
        self.lcd.write_string(f'{item.text}')
        self.lcd.cursor_pos = (1,0)
        self.lcd.write_string(f'{item.get()}')


    def _onDown(self):
        self.lcd.clear()
        self.lcd.cursor_pos = (0,0)
        self._selected = self._selected + 1 if self._selected < len(self._itemKeys) - 1 else 0
        item = self._items[self._itemKeys[self._selected]]
        self.lcd.write_string(f'{item.text}')
        self.lcd.cursor_pos = (1,0)
        self.lcd.write_string(f'{item.get()}')

    def _onLeft(self, withCallback=True):
        self._clearLine(1)
        item = self._items[self._itemKeys[self._selected]]
        val = item.prev()
        self.lcd.write_string(f'{val}')
        if withCallback and item.callback != None:
            item.callback(val)

    def _onHoldLeft(self):
        self.left.when_deactivated = None
        while self.left.is_held:
            self._onLeft(False)
            sleep(0.1)
        self._onLeft()
        self.left.when_deactivated = self._onLeft

    def _onRight(self, withCallback=True):
        self._clearLine(1)
        item = self._items[self._itemKeys[self._selected]]
        val = item.next()
        self.lcd.write_string(f'{val}')
        if withCallback and item.callback != None:
            item.callback(val)

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

    
    def addItem(self, key, name, values: tuple=None, initValue=None, onChange=None):
        self._items[key] = LCDMenuItem(text=name, values=values, initValue=initValue, callback=onChange)
        self._itemKeys.append(key)
        if self._selected == None:
            self._selected = 0
            self._onDown()

    def __getitem__(self, key):
        return self._items[key].get()