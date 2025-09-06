"""HTU21D temperature & humidity sensor driver for MicroPython.

This module provides a compact, safer and slightly higher-level API
for the HTU21D sensor while keeping backward compatibility with
older method names.

Main improvements:
- clearer method names: read_temperature(), read_humidity()
- proper CRC8 check (datasheet polynomial)
- exceptions on CRC failure with optional retries
- helper methods: reset(), read_user_register(), write_user_register()
- small docstrings and default address parameter

Usage (MicroPython):
	from machine import I2C
	from htu21d import HTU21D
	i2c = I2C(0, I2C.MASTER, freq=100000)
	sensor = HTU21D(i2c)
	t = sensor.read_temperature()
	h = sensor.read_humidity()
"""

import utime as time


def sleep_ms(ms):
    """Sleep for ms milliseconds. Works on both MicroPython and CPython."""
    func = getattr(time, 'sleep_ms', None)
    if callable(func):
        func(ms)
    else:
        time.sleep(ms / 1000.0)


class HTU21D:
    """HTU21D sensor class.

    Methods are written to be small and compatible with MicroPython.
    """

    # Default I2C address
    DEFAULT_ADDRESS = 0x40

    # Commands
    TRIGGER_TEMP_MEASURE_HOLD = 0xE3
    TRIGGER_HUMD_MEASURE_HOLD = 0xE5
    TRIGGER_TEMP_MEASURE_NOHOLD = 0xF3
    TRIGGER_HUMD_MEASURE_NOHOLD = 0xF5
    WRITE_USER_REG = 0xE6
    READ_USER_REG = 0xE7
    SOFT_RESET = 0xFE

    def __init__(self, i2c, address=DEFAULT_ADDRESS, *, retries=2, delay_ms=50):
        """Create HTU21D instance.

        i2c: an initialized machine.I2C instance
        address: device address (default 0x40)
        retries: number of retries on CRC failure
        delay_ms: delay between retries in milliseconds
        """
        self.i2c = i2c
        self.address = address
        self.retries = int(retries)
        self.delay_ms = int(delay_ms)

    # --- low level helpers ---
    def reset(self):
        """Soft reset the sensor."""
        try:
            self.i2c.writeto(self.address, bytes([self.SOFT_RESET]))
            # datasheet: typically < 15 ms
            sleep_ms(20)
        except Exception:
            # be tolerant on write errors (bus busy)
            sleep_ms(20)

    def read_user_register(self):
        """Return the user register as int."""
        data = self.i2c.mem_read(1, self.address, self.READ_USER_REG)
        return int(data[0])

    def write_user_register(self, value):
        """Write one byte to user register."""
        self.i2c.writeto(self.address, bytes(
            [self.WRITE_USER_REG, value & 0xFF]))

    # --- CRC and parsing ---
    def _check_crc(self, raw):
        """Check CRC8 for three-byte result (msb, lsb, crc).

        Uses polynomial 0x31 (x^8 + x^5 + x^4 + 1) as in datasheet.
        """
        # raw expected to be a bytes-like object of length >=3
        POLY = 0x131  # 0x31 shifted for 8-bit algorithm implementation
        crc = 0
        for byte in raw[0:2]:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ POLY) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc == (raw[2] & 0xFF)

    def _raw_to_temperature(self, msb, lsb):
        raw = ((msb << 8) | lsb) & 0xFFFC
        return -46.85 + (175.72 * raw / 65536.0)

    def _raw_to_humidity(self, msb, lsb):
        raw = ((msb << 8) | lsb) & 0xFFFC
        return -6.0 + (125.0 * raw / 65536.0)

    # --- public reading methods ---
    def read_temperature(self):
        """Read temperature in Celsius and return float.

        Raises ValueError on repeated CRC failures.
        """
        for attempt in range(self.retries + 1):
            data = self.i2c.mem_read(
                3, self.address, self.TRIGGER_TEMP_MEASURE_HOLD)
            if self._check_crc(data):
                return self._raw_to_temperature(data[0], data[1])
            if attempt < self.retries:
                sleep_ms(self.delay_ms)
        raise ValueError("HTU21D CRC check failed for temperature")

    def read_humidity(self):
        """Read relative humidity (0-100 %) and return float.

        Raises ValueError on repeated CRC failures.
        """
        for attempt in range(self.retries + 1):
            data = self.i2c.mem_read(
                3, self.address, self.TRIGGER_HUMD_MEASURE_HOLD)
            if self._check_crc(data):
                return self._raw_to_humidity(data[0], data[1])
            if attempt < self.retries:
                sleep_ms(self.delay_ms)
        raise ValueError("HTU21D CRC check failed for humidity")

    # --- backward compatibility wrappers ---
    def readTemperatureData(self):
        return self.read_temperature()

    def readHumidityData(self):
        return self.read_humidity()


# Example usage (MicroPython):
if __name__ == "__main__":
    from machine import I2C
    i2c = I2C(0, I2C.MASTER, freq=100000)
    sensor = HTU21D(i2c)
    t = sensor.read_temperature()
    h = sensor.read_humidity()
    print("Temperature: {:.2f} C".format(t))
    print("Humidity: {:.2f} %".format(h))
