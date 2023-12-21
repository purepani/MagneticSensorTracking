from quart import Blueprint, render_template, Response, jsonify, request
import socketio

from magneticsensortracking import positioning, sensors

import argparse
import asyncio
import json
import logging
import io
import os
import platform
import ssl


class Logging(socketio.AsyncNamespace):
    def __init__(
        self,
        sensor_group: sensors.base.SensorGroup,
        printer: positioning.base.Path,
        samples: int = 10,
        *args,
        **kwargs,
    ):
        self.measurement_index = 0
        self.printer = printer
        self.sensor_group = sensor_group
        self.samples = samples
        self.save_path = "~/measurements"
        self.current_folder = "";
        super().__init__(*args, **kwargs)

    async def on_start_measurement(self, sid, folder):
        self.measurement_index = 0
        self.current_folder=folder
        path = f"{self.save_path}/{self.current_folder}"
        if not os.path.exists(path):
            os.makedirs(path)
        

    async def on_record_measurement(self, sid):
        pos = self.printer.getPos()
        mags = [await self.get_sensor_vals() for _ in range(self.samples)]
        with open(f"{self.save_path}/{self.current_folder}/{self.measurement_index}.data", "w") as f:
            f.write("Position\n")
            f.write(f"{",".join(map(str, pos))}")
            f.write("Magentizations\n")
            f.writelines(map(lambda l: ", ".join(map(lambda p: str(tuple(p)), l)), mags))
        self.measurement_index += 1
        self.emit("finished_measurement")

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

    async def get_sensor_vals(self):
        mags_task = asyncio.to_thread(self.sensor_group.get_magnetometer)
        pos_task = asyncio.to_thread(self.sensor_group.get_positions)
        mags, pos = await asyncio.gather(mags_task, pos_task)  # , asyncio.sleep(0.1))
        # await asyncio.sleep(0.1)
        return (pos, mags)
