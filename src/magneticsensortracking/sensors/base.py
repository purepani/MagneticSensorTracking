from collections.abc import MutableSequence
from abc import ABC, abstractmethod


class Sensor(ABC):
    @abstractmethod
    def get_magnetometer(self):
        return


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
            orientations = [[0, 0, 1]] * n
        if not (len(positions) == n and len(orientations) == n):
            raise ValueError(
                "Lists not equal length: Make sure there is a corresponding position and orientation for each sensor"
            )
        self.sensors = sensors
        self.positions = positions
        self.orientations = orientations

    def add_sensor(
        self,
        sensor: Sensor,
        position: MutableSequence,
        orientation: MutableSequence = [0, 0, 1],
    ):
        if not (len(position) == 3 and len(orientation) == 3):
            raise ValueError("Positions and Orientations not length 3")
        self.sensors.append(sensor)
        self.positions.append(position)
        self.orientations.append(orientation)
        return self

    def remove_sensor(self, id):
        del self.sensors[id]
        del self.positions[id]
        del self.orientations[id]
        return self

    def get_magnetometer(self, *args):
        return list(map(lambda x: x.get_magnetometer(*args), self.sensors))

    def get_positions(self):
        return self.positions

    def get_orientations(self):
        return self.orientations
