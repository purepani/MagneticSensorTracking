from quart import Blueprint, redirect, render_template, Response, jsonify, request



from time import time

import argparse
import asyncio
import json
import logging
import io
import os
import platform 
import ssl

from threading import Condition
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, MediaStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender






videoStreamBp = Blueprint("video_stream", __name__, url_prefix="/picamera")

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()



@videoStreamBp.route('/video.mp4')
def video_feed():
    return redirect(f"http://0.0.0.0:8000/video.mp4?{int(time())}")

@videoStreamBp.route('/video.m3u')
def video_feed_m3u8():
    return redirect("http://0.0.0.0:8000/video.m3u8")
