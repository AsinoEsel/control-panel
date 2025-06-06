from machine import Pin, SPI
import time
from micropython import const

from .seven_segment_ascii import get_char2


_MAX7219_DIGITS = const(8)

_MAX7219_REG_NOOP = const(0x0)
_MAX7219_REG_DIGIT0 = const(0x1)
_MAX7219_REG_DIGIT1 = const(0x2)
_MAX7219_REG_DIGIT2 = const(0x3)
_MAX7219_REG_DIGIT3 = const(0x4)
_MAX7219_REG_DIGIT4 = const(0x5)
_MAX7219_REG_DIGIT5 = const(0x6)
_MAX7219_REG_DIGIT6 = const(0x7)
_MAX7219_REG_DIGIT7 = const(0x8)
_MAX7219_REG_DECODEMODE = const(0x9)
_MAX7219_REG_INTENSITY = const(0xA)
_MAX7219_REG_SCANLIMIT = const(0xB)
_MAX7219_REG_SHUTDOWN = const(0xC)
_MAX7219_REG_DISPLAYTEST = const(0xF)

_SPI_BUS = const(1)  # hardware SPI
_SPI_BAUDRATE = const(100000)
_SPI_CS = const(0)  # D3


class SevenSegment:
    def __init__(self, digits=8, scan_digits=_MAX7219_DIGITS, baudrate=_SPI_BAUDRATE, cs=_SPI_CS, spi_bus=_SPI_BUS, reverse=False):
        """
        Constructor:
        `digits` should be the total number of individual digits being displayed
        `scan_digits` is the number of digits each individual max7219 displays
        `baudrate` defaults to 100KHz, note that excessive rates may result in instability (and is probably unnecessary)
        `cs` is the GPIO port to use for the chip select line of the SPI bus - defaults to GPIO 0 / D3
        `spi_bus` is the SPI bus on the controller to utilize - defaults to SPI bus 1
        `reverse` changes the write-order of characters for displays where digits are wired R-to-L instead of L-to-R
        """

        self.digits = digits
        self.devices = -(-digits // scan_digits)  # ceiling integer division
        self.scan_digits = scan_digits
        self.reverse = reverse
        self._buffer = [0] * digits
        self._spi = SPI(spi_bus, baudrate=baudrate, polarity=0, phase=0)
        self._cs = Pin(cs, Pin.OUT, value=1)

        self.command(_MAX7219_REG_SCANLIMIT, scan_digits - 1)  # digits to display on each device  0-7
        self.command(_MAX7219_REG_DECODEMODE, 0)   # use segments (not digits)
        self.command(_MAX7219_REG_DISPLAYTEST, 0)  # no display test
        self.command(_MAX7219_REG_SHUTDOWN, 1)     # not blanking mode
        self.brightness(7)                        # intensity: range: 0..15
        self.clear()

    def command(self, register, data):
        """Sets a specific register some data, replicated for all cascaded devices."""
        self._write([register, data] * self.devices)

    def _write(self, data):
        """Send the bytes (which should be comprised of alternating command, data values) over the SPI device."""
        self._cs.off()
        self._spi.write(bytes(data))
        self._cs.on()

    def clear(self, flush=True):
        """Clears the buffer and if specified, flushes the display."""
        self._buffer = [0] * self.digits
        if flush:
            self.flush()

    def flush(self):
        """For each digit, cascade out the contents of the buffer cells to the SPI device."""
        buffer = self._buffer.copy()
        if self.reverse:
            buffer.reverse()

        for dev in range(self.devices):
            if self.reverse:
                current_dev = self.devices - dev - 1
            else:
                current_dev = dev

            for pos in range(self.scan_digits):
                self._write([pos + _MAX7219_REG_DIGIT0, buffer[pos + (current_dev * self.scan_digits)]] + ([_MAX7219_REG_NOOP, 0] * dev))

    def brightness(self, intensity):
        """Sets the brightness level of all cascaded devices to the same intensity level, ranging from 0..15."""
        self.command(_MAX7219_REG_INTENSITY, intensity)

    def letter(self, position, char, dot=False, flush=True):
        """Looks up the appropriate character representation for char and updates the buffer, flushes by default."""
        value = get_char2(char) | (dot << 7)
        self._buffer[position] = value

        if flush:
            self.flush()

    def text(self, text):
        """Outputs the text (as near as possible) on the specific device."""
        self.clear(False)
        text = text[:self.digits]  # make sure we don't overrun the buffer
        for pos, char in enumerate(text):
            self.letter(pos, char, flush=False)

        self.flush()

    def number(self, val):
        """Formats the value according to the parameters supplied, and displays it."""
        self.clear(False)
        strval = ''
        if isinstance(val, (int, float)):
            strval = str(val)
        elif isinstance(val, str):
            if val.replace('.', '', 1).strip().isdigit():
                strval = val

        if '.' in strval:
            strval = strval[:self.digits + 1]
        else:
            strval = strval[:self.digits]

        pos = 0
        for char in strval:
            dot = False
            if char == '.':
                continue
            else:
                if pos < len(strval) - 1:
                    if strval[pos + 1] == '.':
                        dot = True
                self.letter(pos, char, dot, False)
                pos += 1

        self.flush()

    def scroll(self, rotate=True, reverse=False, flush=True):
        """Shifts buffer contents left or right (reverse), with option to wrap around (rotate)."""
        if reverse:
            tmp = self._buffer.pop()
            if rotate:
                self._buffer.insert(0, tmp)
            else:
                self._buffer.insert(0, 0x00)
        else:
            tmp = self._buffer.pop(0)
            if rotate:
                self._buffer.append(tmp)
            else:
                self._buffer.append(0x00)

        if flush:
            self.flush()

    def message(self, text, delay=0.4):
        """Transitions the text message across the devices from left-to-right."""
        self.clear(False)
        for char in text:
            time.sleep(delay)
            self.scroll(rotate=False, flush=False)
            self.letter(self.digits - 1, char)
