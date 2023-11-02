from magneticsensortracking import positioning
import numpy as np
import time


try:
    from printrun.printcore import printcore
except ImportError:
    printcore = None


class PRUSA(positioning.base.Path):
    def __init__(self, printer_path, baud_rate=115200, position=np.array([[0, 0, 0]])):
        if not printcore:
            raise ImportError("Reqires printrun to use 3D printers")

        self.printer = printcore(printer_path, baud_rate)
        while not self.printer.online:
            time.sleep(1)
        self.shift = np.min(position, axis=0)
        self.printer.send(
            f"G92 X{position[0, 0]-self.shift[0]:.1f} Y{position[0, 1]-self.shift[1]:.1f} Z{position[0, 2]-self.shift[2]:.1f}"
        )
        super().__init__(position)

    def __move__(self, pos, rot=[]):
        pos_shift = pos - self.shift
        modify_position_gcode = "G92"
        for e, axis, i in zip(pos_shift, ["X", "Y", "Z"], range(3)):
            if e < 0:
                modify_position_gcode = " ".join(
                    [modify_position_gcode, f"{axis}{-e:.1f}"]
                )
                self.shift[i] = e
        x, y, z = pos - self.shift
        self.printer.send(modify_position_gcode)
        self.printer.send(f"G01 X{x} Y{y} Z{z}")

