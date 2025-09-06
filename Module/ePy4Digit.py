"""RL 4-digit 7-segment display driver (Richlink-tech)

This module provides a small, documented API to drive the Richlink-tech
4-digit display over I2C. The device uses a simple command protocol:
- 0x03 SHOW_FOUR_DIGITAL: [0x03, position(1-4), value]
- 0x02 SHOW_TIME:         [0x02, hour, minute]
- 0x04 SHOW_COLON:        [0x04, on_off]

Notes:
- The module attempts to use either `i2c.send(buf, addr)` (pyboard-style)
  or `i2c.writeto(addr, buf)` (common MicroPython API). If both fail an
  error message is printed.
- The display appears to accept numeric codes 0-9. The decimal point is set
  by OR'ing the digit value with 0x80 (e.g. value | 0x80).
- The driver uses `0x0C` (12) as a degree-symbol placeholder because that
  value was present in the original implementation. If your module uses
  a different code for the degree symbol, change `DEGREE_SYMBOL`.
"""

import math


class FourDigit:
    """Driver for the Richlink-tech 4-digit I2C display.

    Public methods:
    - set_digit(pos, value, dot=False)
    - set_colon(on)
    - show4number(number)
    - show_temper(temperature)
    - show_time(hour, minute)
    - clear()
    """

    # Command bytes used by the device
    SHOW_FOUR_DIGITAL = 0x03
    SHOW_TIME = 0x02
    SHOW_COLON = 0x04

    # Default I2C address used by the hardware
    DEFAULT_I2C_ADDR = 0x3D

    # Common special codes used by example firmware (keeps compatibility)
    DEGREE_SYMBOL = 12

    def __init__(self, i2c_port, i2c_addr=DEFAULT_I2C_ADDR):
        """Create a driver instance.

        i2c_port: an initialized I2C object from MicroPython port (has
                  either `send` or `writeto` method)
        i2c_addr: 7-bit I2C address of the display (default 0x3D)
        """
        self.i2c = i2c_port
        self.addr = i2c_addr

    def i2c_write(self, write_data):
        """Write raw bytes to the device, with compatibility for common
        MicroPython I2C implementations.

        write_data: an iterable of integers (0-255)
        """
        buf = bytearray(write_data)
        # Try pyboard-style send first, then fallback to writeto
        try:
            send = getattr(self.i2c, 'send', None)
            if callable(send):
                send(buf, self.addr)
                return
        except OSError:
            # fall through to try writeto
            pass

        try:
            writeto = getattr(self.i2c, 'writeto', None)
            if callable(writeto):
                writeto(self.addr, buf)
                return
        except OSError:
            pass

        # If neither method succeeded we show an error (no exception thrown
        # to keep driver lightweight on microcontrollers)
        print('I2C write failed to 0x{:02X}'.format(self.addr))

    def set_digit(self, position, value, dot=False):
        """Set a single digit on the display.

        position: 1..4 (1 = leftmost, 4 = rightmost)
        value: integer code for the digit (commonly 0-9)
        dot: when True OR the value with 0x80 to light the decimal point
        """
        if position < 1 or position > 4:
            raise ValueError('position must be 1..4')
        val = int(value) & 0xFF
        if dot:
            val |= 0x80
        self.i2c_write([FourDigit.SHOW_FOUR_DIGITAL, position, val])

    def set_colon(self, on):
        """Turn the colon on or off.

        on: truthy to enable, falsy to disable
        """
        self.i2c_write([FourDigit.SHOW_COLON, 1 if on else 0])

    def show4number(self, number):
        """Display an integer 0..9999 across the four digits.

        The driver writes each digit separately using the device command.
        Leading zeros are shown as 0 (keeps compatibility with original
        behaviour). If you prefer suppressing leading zeros, implement
        a small wrapper that replaces leading zeros with a blank code.
        """
        number = int(number)
        if 0 <= number <= 9999:
            self.set_digit(1, number // 1000)
            self.set_digit(2, (number % 1000) // 100)
            self.set_digit(3, (number % 100) // 10)
            self.set_digit(4, number % 10)
            self.set_colon(False)

    def show_temper(self, temper):
        """Display a temperature with single decimal place (e.g. 24.1).

        The display layout used here (keeps original behaviour):
        [tens] [units with decimal point] [fraction] [degree symbol]
        """
        tempe = round(float(temper), 1)
        if 0 <= tempe < 100:
            # tens (0..9)
            self.set_digit(1, int(tempe // 10))
            # units with decimal point
            self.set_digit(2, (int(math.floor(tempe)) % 10), dot=True)
            # fractional digit (tenths)
            self.set_digit(3, int(round(tempe * 10)) % 10)
            # degree symbol placeholder (keeps original code's 12)
            self.set_digit(4, FourDigit.DEGREE_SYMBOL)
            self.set_colon(False)

    def show_time(self, hr, minute):
        """Display hour and minute using the device time command.

        The device provides an explicit SHOW_TIME command which takes two
        bytes (hour, minute) and typically enables the colon. Bounds are
        not strictly enforced here (driver trusts caller), but a caller
        should provide 0<=hr<24 and 0<=minute<60.
        """
        self.i2c_write([FourDigit.SHOW_TIME, int(hr)
                       & 0xFF, int(minute) & 0xFF])
        # Suggest device will control colon when using SHOW_TIME, but
        # keep explicit behaviour compatible with original driver.
        self.set_colon(True)

    def clear(self):
        """Clear the display by writing 0 to all digits and turning colon off."""
        for pos in (1, 2, 3, 4):
            self.set_digit(pos, 0)
        self.set_colon(False)


if __name__ == '__main__':
    # Simple sanity example (runs on MicroPython ports). Wrapped in try/except
    # so importing this module on a host/python linter won't fail.
    try:
        # Dynamic import to avoid import-time errors on host/python linters
        machine = __import__('machine')
        I2C = getattr(machine, 'I2C')

        i2c1 = I2C(1, I2C.MASTER, baudrate=100000)
        four_digi = FourDigit(i2c1)
        four_digi.show4number(1999)
        four_digi.show_temper(24.1)
        four_digi.show_time(23, 59)
    except Exception:
        # Running on non-MicroPython host or missing hardware: skip live demo
        pass
