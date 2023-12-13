from quart import Blueprint, render_template, Response, jsonify, request
import socketio

from magneticsensortracking import positioning

import argparse
import asyncio
import json
import logging
import io
import os
import platform
import ssl


class PrinterRouting(socketio.AsyncNamespace):
    def __init__(self, printer: positioning.base.Path, *args, **kwargs):
        self.printer = printer
        self.send_vals = asyncio.create_task(self.send_printer_vals())
        super().__init__(*args, **kwargs)

    def on_printerMove(self, sid, x, y, z):
        self.printer.move([x, y, z])

    async def send_printer_vals(self):
        while True:
            pos = await self.get_printer_vals()
            data = {"data": {"pos": pos}}
            await self.emit("printerPos", data)
            # print("Sent Printer data")
            await asyncio.sleep(0.1)

    async def get_printer_vals(self):
        pos = self.printer.getPos()
        return pos.tolist()
