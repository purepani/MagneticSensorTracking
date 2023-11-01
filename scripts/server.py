from magneticsensortracking import sensors, ui
import board
import uvicorn
import asyncio

sensors = sensors.base.SensorGroup([sensors.Sensors.MLX90393(i2c=board.I2C(), address=a) for a in range(0x10, 0x14)], positions=[[0., 0., 0.], [25., 0., 0.], [0., 25., 0.], [25., 25., 0.]])

def app_factory():
    return ui.main(sensor_group=sensors)

if __name__=="__main__":
    uvicorn.run("server:app_factory", host="0.0.0.0", port=5000, factory=True)



