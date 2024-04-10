import magneticsensortracking.sensors.base as base
import struct

try:
    import adafruit_mlx90393
except ImportError:
    adafruit_mlx90393 = None





from typing import Tuple

from busio import I2C
from circuitpython_typing import ReadableBuffer

import time



class MLX90393(base.Sensor):
    def __init__(
        self,
        i2c,
        address,
        **kwargs
    ):
        if adafruit_mlx90393:
            self.sensor = adafruit_mlx90393.MLX90393(
                i2c,
                address=address,
                **kwargs
            )
        else:
            print("This class needs the package adafruit_circuitpython_mlx90393")


    def get_magnetometer(self):
        x, y, z = self.sensor.magnetic
        return x/1000, y/1000, z/1000

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
    def temperature_compensation(self,):
        return self.sensor.temperature_compensation

    @temperature_compensation.setter 
    def temperature_compensation(self, val):
        self.sensor.temperature_compensation=val


