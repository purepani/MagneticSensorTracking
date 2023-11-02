from magneticsensortracking import sensors, positioning
import os
import random
from quart import Quart
import socketio
from time import sleep
import board

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

from .videoStream import videoStreamBp
from .sensorBP import SensorRouting
from .printerBP import PrinterRouting


class AppFactory:
    def __init__(self, sensor_group=None, printer=None):
        if not sensor_group:
            sensor_group = sensors.base.SensorGroup(
                [],
                [],
            )
        self.sensor_group = sensor_group
        self.printer = printer

    def setFakeSensor(self):
        self.sensor_group = sensors.base.SensorGroup(
            [sensors.Sensors.VIRTUAL() for _ in range(4)],
            [[0.0, 0.0, 0.0], [1.1, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]],
        )
        return self

    def setFakePrinter(self):
        self.printer = positioning.devices.VIRTUAL(np.array([[1, 0, 0]]))
        return self

    def setPrinter(self, printer):
        self.printer = printer
        return self

    def addSensor(self, sensor: sensors.base.Sensor, pos=[0,0,0], rot=[0, 0, 1]):
        self.sensor_group.add_sensor(sensor, pos, rot)
        return self

    def create_app(self):
        qapp = Quart(__name__)
        sio = socketio.AsyncServer(async_mode="asgi")

        app = socketio.ASGIApp(sio, qapp)

        @qapp.route("/")
        async def base():
            return await render_template("base.html")
            # a simple page that says hello

        sio.register_namespace(SensorRouting(self.sensor_group))
        sio.register_namespace(PrinterRouting(self.printer))

        qapp.register_blueprint(videoStreamBp)

        return app


main = AppFactory().setFakeSensor().setFakePrinter().create_app
