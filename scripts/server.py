from magneticsensortracking import sensors, ui, positioning
import board
import uvicorn
import asyncio
from functools import reduce

# sensors = sensors.base.SensorGroup(, positions=)

sensors = [
    sensors.Sensors.MLX90393(i2c=board.I2C(), address=a) for a in range(0x10, 0x14)
]
positions = [[0.0, 0.0, 0.0], [25.0, 0.0, 0.0], [0.0, 25.0, 0.0], [25.0, 25.0, 0.0]]
printer = positioning.devices.PRUSA(
    "/dev/serial/by-id/usb-Prusa_Research__prusa3d.com__Original_Prusa_i3_MK2_CZPX1017X003XC14071-if00",
    115200,
)


app_factory = ui.AppFactory()
app_factory = reduce(
    lambda x, y: x.addSensor(*y), zip(sensors, positions), app_factory
)
app_factory.setPrinter(printer)
#app_factory.setFakePrinter()

create_app = app_factory.create_app

if __name__ == "__main__":
    uvicorn.run("server:create_app", host="0.0.0.0", port=5000, factory=True)
