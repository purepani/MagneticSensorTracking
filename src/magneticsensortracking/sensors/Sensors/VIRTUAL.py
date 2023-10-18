from magneticsensortracking import sensors
from random import uniform


class VIRTUAL(sensors.base.Sensor):
  def __init__(self):
    pass

  def get_magnetometer(self):  # return tuple
    #x, y, z = j
    return 1.0, 2.0, 0.4
