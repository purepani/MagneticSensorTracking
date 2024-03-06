import numpy as np
import einops as eo
import scipy as sp

def B_dipole(position, rotation, M0, shape):
    R = np.sqrt(np.sum(position**2, axis=1))
    B = (M0 * (shape[0]) ** 2 * shape[1] / (16)) * (
        (
            3
            * position
            / R[:, np.newaxis] ** 5
            * (eo.einsum(position, rotation, "sensor dim,  dim -> sensor"))[
                :, np.newaxis
            ]
        )
        - rotation[np.newaxis, :] / (R[:, np.newaxis] ** 3)
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
    axis = x[3:]
    # axis = np.array([0.0, 0.0, 1.0])
    # phi = x[3]
    # theta = x[4]
    # axis = np.array([np.sin(theta)*np.cos(phi), np.sin(theta)*np.sin(phi), np.cos(theta)])
    return B_dipole(positions - position, axis, M0, shape)


def cost_dipole(x, B, positions, M0, shape):
    diff = getField_dipole(x, positions, M0, shape) - B
    return np.sum((diff) ** 2)


def minimize(x0, args):
    print("Starting mimimization")
    # x0 = [x, y, z, th_x, th_y, th_z]
    cons = [{"type": "eq", "fun": lambda x: x[3] ** 2 + x[4] ** 2 + x[5] ** 2 - 1}]
    bounds = [(-100, 100), (-100, 100), (0, 100), (-1, 1), (-1, 1), (-1, 1)]
    res = sp.optimize.minimize(
        fun=cost_dipole, x0=x0, args=args, tol=1e-100, constraints=cons, bounds=bounds
    ).x  # , options={'maxiter': 1000}).x
    print(f"Finished mimimization with shape {args[3]} at {res}")
    return res
