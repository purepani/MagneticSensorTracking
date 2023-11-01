from magneticsensortracking import sensors, positioning
import os
import random
from quart import Quart
import socketio
from time import sleep

from quart import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
import numpy as np

# from .videoStream import videoStreamBp
from .sensorBP import SensorRouting
from .printerBP import PrinterRouting

# create and configure the app

# socketio = SocketIO(app)
# create a Socket.IO server


# wrap with ASGI application

fake_sensor = sensors.base.SensorGroup(
    [sensors.Sensors.VIRTUAL() for _ in range(4)],
    [[0.0, 0.0, 0.0], [1.1, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]],
)

fake_printer = positioning.devices.VIRTUAL(np.array([[1, 0, 0]]))


def main(
    sensor_group: sensors.base.SensorGroup = fake_sensor,
    printer: positioning.base.Path = fake_printer,
):
    qapp = Quart(__name__)
    sio = socketio.AsyncServer(async_mode="asgi")

    app = socketio.ASGIApp(sio, qapp)

    @qapp.route("/")
    async def hello_world():
        return await render_template("base.html")
        # a simple page that says hello

    sio.register_namespace(SensorRouting(sensor_group))
    sio.register_namespace(PrinterRouting(printer))

    async def send_sensor_vals():
        j = 0
        while True:
            pos, mag = await get_sensor_vals()
            data = {"data": [{"pos": pos[i], "mag": mag[i]} for i in range(len(mag))]}
            await sio.emit("sensors", data)
            j += 1
            # print("Sent Sensor data")
            await sio.sleep(0.1)

    async def send_printer_vals():
        j = 0
        while True:
            pos = await get_printer_vals()
            data = {"data": {"pos": pos}}
            await sio.emit("printerPos", data)
            j += 1
            # print("Sent Printer data")
            await sio.sleep(0.1)

    # qapp.register_blueprint(videoStreamBp)

    async def get_sensor_vals():
        mags = sensor_group.get_magnetometer()
        pos = sensor_group.get_positions()
        return (pos, mags)

    async def get_printer_vals():
        pos = printer.getPos()
        return pos.tolist()

    return app
