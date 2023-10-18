from collections.abc import MutableSequence


class Sensor:
    def __init__(self):
        raise NotImplementedError()

    def get_magnetometer(self):
        raise NotImplementedError()


class SensorGroup:
    """
    Represents a group of sensors.

    ...

    Attributes:
    ----------
    sensors : list[nx1 of Sensor]
    positions: list[nx3 in mm]
    orientations: list[nx3] in rotations
    """

    def __init__(
        self,
        sensors: MutableSequence[Sensor] = [],
        positions: MutableSequence = [],
        orientations: MutableSequence = [],
    ):
        n = len(sensors)
        if orientations == []:
            orientations=[[0,0,1]]*4
        if not (len(positions) == n and len(orientations) == n):
            raise ValueError(
                "Lists not equal length: Make sure there is a corresponding position and orientation for each sensor"
            )
        self.sensors = sensors
        self.positions = positions
        self.orientations = orientations

    def add_sensor(
        self, sensor: Sensor, position: MutableSequence, orientation: MutableSequence
    ):
        if not (len(position) == 3 and len(orientation) == 3):
            raise ValueError("Positions and Orientations not length 3")
        self.sensors.append(sensor)

    def remove_sensor(self, id):
        del self.sensors[id]
        del self.positions[id]
        del self.orientations[id]

    def get_magnetometer(self):
        return list(map(lambda x: x.get_magnetometer(), self.sensors))

    def get_positions(self):
        return self.positions

    def get_orientations(self):
        return self.orientations
