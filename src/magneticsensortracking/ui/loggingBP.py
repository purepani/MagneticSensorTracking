from quart import Blueprint, render_template, Response, jsonify, request
import socketio

from magneticsensortracking import positioning, sensors
from datetime import datetime

import argparse
import asyncio
import json
import logging
import io
import os
import platform
import ssl

import numpy as np


class Logging(socketio.AsyncNamespace):
    def __init__(
        self,
        sensor_group: sensors.base.SensorGroup,
        printer: positioning.base.Path,
        samples: int = 10,
        *args,
        **kwargs,
    ):
        self.printer = printer
        self.sensor_group = sensor_group
        self.samples = samples
        self.save_path = "/home/raspberrypi/measurements"
        self.current_folder = "";
        self.measuring = False
        super().__init__(*args, **kwargs)

    async def on_start_measurement(self, sid):
        path = f"{self.save_path}/{self.current_folder}"
        if not os.path.exists(path):
            os.makedirs(path)
            print("Created Path")
        print("Ready For Measurements")
        

    async def on_record_measurement(self, sid):
        self.measuring=True
        print("Recording Measurement")
        pos = self.printer.getPos()
        vals = [await self.get_sensor_vals() for _ in range(self.samples)]
        mags = np.array([m for _, m, _ in vals])
        pos = np.array([p for p, _, _ in vals])
        temp = np.array([t for _, _, t in vals])
        time = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        file_path = f"{self.save_path}/{self.current_folder}/{time}.npz"
        data_to_save = {f'mags': mags,f'pos': pos, f'temp': temp}
        with open(file_path, "wb") as f:
            np.savez(f, **data_to_save)
        self.measuring=False
        print("Finished Recording")
        await self.emit("finished_measurement")

    async def on_get_settings(self, sid):
        await self.emit("settings", 
                            {
                            "samples": self.samples,
                            "folder": f"{self.save_path}/{self.current_folder}"
                            }
                        )


    async def on_set_settings(self, sid, folder, samples):
        self.current_folder = folder
        self.samples = int(samples)
        await self.emit("settings", 
                            {
                            "samples": self.samples,
                            "folder": f"{self.save_path}/{self.current_folder}"
                            }
                        )
    async def get_sensor_vals(self):
        mags_task = asyncio.to_thread(self.sensor_group.get_magnetometer)
        pos_task = asyncio.to_thread(self.sensor_group.get_positions)

        mags_and_temp, pos = await asyncio.gather(
            mags_task, pos_task, return_exceptions=True
        )  # , asyncio.sleep(0.1))
        for m in mags_and_temp:
            if m is Exception:
                raise m
        temp = [m[3] for m in mags_and_temp]
        mags = [m[:3] for m in mags_and_temp]
        await asyncio.sleep(0.1)
        return (pos, mags, temp)
