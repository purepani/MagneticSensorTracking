from magneticsensortracking import sensors

try:
    import lsm303d
except:
    lsm303d = None

class PIM(sensors.base.Sensor):
    def __init__(self, i2c, address=0x1D, i2c_dev=1):
        if lsm303d:
            self.sensor = lsm303d.LSM303D(address, i2c_dev=i2c)
        else:
            print("This module will not function without the lsm303d package.")

    def get_magnetometer(self):  # return tuple
        x, y, z = self.sensor.magnetometer()
        return x / 10, y / 10, z / 10
