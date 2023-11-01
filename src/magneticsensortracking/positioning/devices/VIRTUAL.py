from magneticsensortracking import positioning
import numpy as np

class VIRTUAL(positioning.base.Path):
    def __init__(self, *args):
        super().__init__(*args)

    def __move__(self, pos, rot):
        pass
