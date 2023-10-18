from magneticsensortracking import positioning


class VIRTUAL(positioning.base.Path):
    def __init__(self, *args):
        super().__init__(*args)

    def __move__(self, pos, rot):
        pass
