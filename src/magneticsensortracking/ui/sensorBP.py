from quart import Blueprint, render_template, Response, jsonify, request
import socketio

from magneticsensortracking import sensors
import numpy as np
import einops as eo
import scipy as sp

import argparse
import asyncio
import json
import logging
import io
import os
import platform
import ssl


class SensorRouting(socketio.AsyncNamespace):
    def __init__(self, sensor_group: sensors.base.SensorGroup, *args, **kwargs):
        self.sensor_group = sensor_group
        self.magnet_shape = np.array([1, 1])
        self.magnet_magnetization = np.array([1240])
        self.val_send = asyncio.create_task(self.send_sensor_vals())
        super().__init__(*args, **kwargs)

    def on_connect(self, sid, enivron):
        pass

    def on_disconnect(self, sid):
        pass

    async def on_sendMagnet(self, sid, radius, height, magnetism):
        self.magnet_shape = np.array([radius, height])
        self.magnet_magnetization = np.array([magnetism])

    async def on_predicted(self, sid):
        pass

    async def send_sensor_vals(self):
        print("Sent Sensor data")
        while True:
            pos, mag = await self.get_sensor_vals()
            data = {"data": [{"pos": p, "mag": m} for p, m in zip(pos, mag)]}
            await self.emit("sensors", data)
            await asyncio.sleep(0.1)

    async def get_sensor_vals(self):
        mags = self.sensor_group.get_magnetometer()
        pos = self.sensor_group.get_positions()
        x0 = np.array([0, 0, 30])
        M0 = self.magnet_magnetization
        shape = self.magnet_shape
        #predicted = minimize(x0, (mags, pos, M0, shape)).x
        return (pos, mags)


def B_dipole(position, rotation, M0, shape):
    R = np.sqrt(np.sum(position**2))
    B = (M0 * (shape[0] / 2) ** 2 * shape[1] * np.pi / (4 * np.pi)) * (
        (
            3
            * position
            * (eo.einsum(position, rotation, "sensor dim,  dim -> sensor"))[
                :, np.newaxis
            ]
            / R**5
        )
        - rotation / R**3
    )
    return B


def getField_dipole(x, positions, M0, shape):
    # magnetization=x[5]
    # magnetization=1210
    position = x[:3]
    axis = x[3:]
    # axis=np.array([0,0,1])
    # phi = x[3]
    # theta = x[4]
    # axis = np.array([np.sin(theta)*np.cos(phi), np.sin(theta)*np.sin(phi), np.cos(theta)])
    return B_dipole(positions - position, axis, M0, shape)


def getField_dipole_fixed(x, positions, M0, shape):
    # magnetization=x[5]
    # magnetization=1210
    position = x[:3]
    # axis=x[3:]
    axis = np.array([0.0, 0.0, 1.0])
    # phi = x[3]
    # theta = x[4]
    # axis = np.array([np.sin(theta)*np.cos(phi), np.sin(theta)*np.sin(phi), np.cos(theta)])
    return B_dipole(positions - position, axis, M0, shape)


def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis = axis / np.sqrt(np.dot(axis, axis))
    a = np.cos(theta / 2.0)
    b, c, d = -axis * np.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array(
        [
            [aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
            [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
            [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc],
        ]
    )


def cost_dipole(x, B, positions, M0, shape):
    diff = getField_dipole(x, positions, M0, shape) - B
    return np.sum((diff) ** 2)


def minimize(x0, args=()):
    return sp.optimize.minimize(cost_dipole, x0, args)