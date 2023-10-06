import magneticsensortracking.sensors.base as base

try:
    import adafruit_mlx90393
except ImportError:
    adafruit_mlx90393 = None


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
