from flask import Blueprint, render_template, Response

videoStreamBp = Blueprint("video_stream", __name__)

# Raspberry Pi camera module (requires picamera package)
from camera_pi import Camera


def gen(camera):
    # Video streaming generator function.
    while True:
        frame = camera.get_frame()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


@videoStreamBp.route("/videopi")
def video_stream():
    return Response(gen(Camera()), mimetype="multipart/x-mixed-replace; boundary=frame")
