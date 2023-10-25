import numpy as np
import einops as eo


class Path:
    def __init__(
        self,
        position=np.array([[0.0, 0.0, 0.0]]),
        orientation=np.array([[0.0, 0.0, 1.0]]),
    ):
        self.position = position
        self.orientation = orientation
        if orientation.shape[0] == 1 and position.shape[0] != 1:
            self.orientation = eo.repeat(
                orientation, "i j -> i (repeat j)", repeat=position.shape[0]
            )
        self.time = 0
        self.__move__(position[self.time], orientation[self.time])

    def __iter__(self):
        return self

    def __next__(self):
        if self.time + 1 >= len(self.position):
            raise StopIteration
        self.time = self.time + 1
        self.__move__(self.position[self.time], self.orientation[self.time])
        return self.position[self.time], self.orientation[self.time]

    def add(self, extra_pos, extra_rot):
        self.position = eo.pack([self.position, extra_pos], "* d")
        self.orientation = eo.pack([self.orientation, extra_rot], "* d")

    def __move__(self, pos, rot):
        raise NotImplementedError()

    def getPos(self):
        return self.position[self.time]

    def move(self, pos, rot):
        self.position = eo.pack(
            [
                self.position[: self.time + 1],
                np.array(pos),
                self.position[self.time + 1 :],
            ],
            "* d",
        )
        self.orientation = eo.pack(
            [
                self.orientation[: self.time + 1],
                np.array(pos),
                self.orientation[self.time + 1 :],
            ],
            "* d",
        )
        self.time = self.time + 1
        self.__move__(pos, rot)

    @staticmethod
    def grid(x_min, x_max, x_step, y_min, y_max, y_step, z_min, z_max, z_step):
        coords = np.mgrid[
            x_min : x_max + x_step : x_step,
            y_min : y_max + y_step : y_step,
            z_min : z_max + z_step : z_step,
        ]
        return eo.rearrange(coords, "d i j k -> (k j i) d")
