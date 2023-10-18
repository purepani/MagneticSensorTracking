from magneticsensortracking import sensors
import os
import random
from flask import Flask
from flask_sock import Sock
from flask_socketio import SocketIO, emit
from time import sleep

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


# create and configure the app
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)


fake = sensors.base.SensorGroup(
    [sensors.Sensors.VIRTUAL() for _ in range(4)],
    [[0.0, 0.0, 0.0], [1.1, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]],
)


def main(sensor_group: sensors.base.SensorGroup = fake):
    @app.route("/")
    def hello_world():
        return render_template("base.html")
        # a simple page that says hello

    @socketio.on("connect")
    def test_connect(auth):
        print("Connected to client.")
        socketio.start_background_task(send_sensor_vals)
        # send_test()

    def send_sensor_vals():
        while True:
            pos, mag = get_sensor_vals()
            data = {"data": [{"pos": pos[i], "mag": mag[i]} for i in range(len(mag))]}
            socketio.emit("sensors", data)
            print("Sent data")
            socketio.sleep(0.1)

    def get_sensor_vals():
        mags = sensor_group.get_magnetometer()
        pos = sensor_group.get_positions()
        return (pos, mags)

    socketio.run(app)
