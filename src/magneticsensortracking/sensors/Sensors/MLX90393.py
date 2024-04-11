import struct

import magneticsensortracking.sensors.base as base

try:
    import adafruit_mlx90393
except ImportError:
    adafruit_mlx90393 = None
import time
from typing import Tuple

from busio import I2C
from circuitpython_typing import ReadableBuffer


class MLX90393(base.Sensor):
    def __init__(self, i2c, address, **kwargs):
        if adafruit_mlx90393:
            self.sensor = adafruit_mlx90393.MLX90393(i2c, address=address, **kwargs)
        else:
            print("This class needs the package adafruit_circuitpython_mlx90393")

    def get_magnetometer(self):
        x, y, z, t = self.magnetic_and_temp
        return x / 1000, y / 1000, z / 1000

    def get_temperature(self):
        return self.sensor.temperature

    @property
    def read_data(self) -> Tuple[int, int, int, int]:
        """
        Reads a single X/Y/Z/T sample from the magnetometer.
        """
        # Set conversion delay based on filter and oversampling
        delay = (
            adafruit_mlx90393._TCONV_LOOKUP[self.sensor._filter][self.sensor._osr]
            / 1000
        )  # per datasheet
        delay *= 1.1  # plus a little

        # Set the device to single measurement mode
        self.sensor_transceive(bytes([adafruit_mlx90393._CMD_SM | 0xF]))

        # Insert a delay since we aren't using INTs for DRDY
        time.sleep(delay)

        # Read the 'XYZ' data
        data = self.sensor._transceive(bytes([adafruit_mlx90393._CMD_RM | 0xF]), 8)

        # Unpack status and raw int values
        self.sensor.sensor_status_last = data[0]
        m_x = self.sensor._unpack_axis_data(self.sensor._res_x, data[1:3])
        m_y = self.sensor._unpack_axis_data(self.sensor._res_y, data[3:5])
        m_z = self.sensor._unpack_axis_data(self.sensor._res_z, data[5:7])
        t = struct.unpack(">H", data[7:9])[0]

        # Return the raw int values if requested
        return m_x, m_y, m_z, t

    @property
    def magnetic_and_temp(self) -> Tuple[float, float, float, float]:
        """
        The processed magnetometer sensor values.
        A 4-tuple of X, Y, Z, T axis values in microteslas that are signed floats.
        """
        treference = self.sensor.read_reg(0x24)
        x, y, z, tvalue = self.read_data

        # Check for valid HALLCONF value and set _LSB_LOOKUP index
        if adafruit_mlx90393._HALLCONF == 0x0C:
            hallconf_index = 0
        elif adafruit_mlx90393._HALLCONF == 0x00:
            hallconf_index = 1
        else:
            raise ValueError("Incorrect HALLCONF value, must be '0x0C' or '0x00'.")

        # Convert the raw integer values to uT based on gain and resolution
        x *= adafruit_mlx90393._LSB_LOOKUP[hallconf_index][self.sensor._gain_current][
            self.sensor._res_x
        ][0]
        y *= adafruit_mlx90393._LSB_LOOKUP[hallconf_index][self.sensor._gain_current][
            self.sensor._res_y
        ][0]
        z *= adafruit_mlx90393._LSB_LOOKUP[hallconf_index][self.sensor._gain_current][
            self.sensor._res_z
        ][1]
        t = 35 + ((tvalue - treference) / 45.2)

        return x, y, z, t

    @property
    def filter(self):
        return self.sensor.filter

    @filter.setter
    def filter(self, val):
        self.sensor.filter = val

    @property
    def gain(self):
        return self.sensor.gain

    @gain.setter
    def gain(self, val):
        self.sensor.gain = val

    @property
    def oversampling(self):
        return self.sensor.oversampling

    @oversampling.setter
    def oversampling(self, val):
        self.sensor.oversampling = val

    @property
    def resolution_x(self):
        return self.sensor.resolution_x

    @resolution_x.setter
    def resolution_x(self, val):
        self.sensor.resolution_x = val

    @property
    def resolution_y(self):
        return self.sensor.resolution_y

    @resolution_y.setter
    def resolution_y(self, val):
        self.sensor.resolution_y = val

    @property
    def resolution_z(self):
        return self.sensor.resolution_z

    @resolution_z.setter
    def resolution_z(self, val):
        self.sensor.resolution_z = val

    @property
    def temperature_compensation(
        self,
    ):
        return self.sensor.temperature_compensation

    @temperature_compensation.setter
    def temperature_compensation(self, val):
        self.sensor.temperature_compensation = val
