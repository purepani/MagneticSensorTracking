from magneticsensortracking import sensors
import board
import numpy as np
import einops as eo
import scipy as sp

from itertools import product

from concurrent.futures import ProcessPoolExecutor


def B_dipole(position, rotation, M0, shape):
    R = np.sqrt(np.sum(position**2, axis=1))
    B = (M0 * (shape[0] / 2) ** 2 * shape[1] * np.pi / (4 * np.pi)) * (
        (
            3
            * (position.T/R**5).T
            * (eo.einsum(position, rotation, "sensor dim,  dim -> sensor"))[
                :, np.newaxis
            ]
            
        )
        - rotation[np.newaxis, :] / (R[:, np.newaxis]**3)
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


def minimize(x0, args):
    print("Starting mimimization")
    #args = list(map(np.asarray, args))
    cons = [{'type': 'eq', 'fun': lambda x: x[3]**2+x[4]**2+x[5]**2-1}]
    res = sp.optimize.minimize(fun=cost_dipole, x0=x0, args=args, tol=1e-50, options={'maxiter': 1000}, constraints=cons).x
    print("Finished mimimization")
    return res

def get_sensor(a):
    print(f"Starting sensor {hex(a)}")
    s = sensors.Sensors.MLX90393(i2c=board.I2C(), address=a, oversampling=2, filt=2)
    print(f"Connected to sensor {hex(a)}")
    return s

def get_sensors(addresses):
    sensors = [get_sensor(a) for a in addresses]
    return sensors 

if __name__=="__main__":
    s = get_sensors(range(0x0c, 0x1c))
    positions = [[a, b, 0.] for b,a in product(list(np.linspace(0,13.5, 4, endpoint=True)), list(np.linspace(0,-13.5,4, endpoint=True)))]
    sensor_group = sensors.base.SensorGroup(sensors=s, positions=positions)
    shape = np.array([25.4*3/16, 25.4*3/16])
    M0 = np.array([1210])
    x0 = np.array([0,0,30, 0, 0, 1])
    mags = np.array(sensor_group.get_magnetometer())
    pos = np.array(sensor_group.get_positions())
    predicted = minimize(x0, (mags, pos, M0, shape))
    print(predicted)
