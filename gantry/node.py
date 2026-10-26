"""The gantry node: the Zaber XYZ gantry on the gantry computer. For now it
only reports position; move() and the rest are not implemented yet.

    .venv/bin/python gantry/node.py --port 8100
    LABNODE_TOKEN=... .venv/bin/python gantry/node.py --host 0.0.0.0 --port 8100 --serial-port COM6

Listening on anything other than localhost (so a manager on another computer
can reach it) needs LABNODE_TOKEN set, and the manager must use the same token.
Coordinates are the gantry's own millimetres; the manager converts from bed
coordinates through its calibration.
"""

from __future__ import annotations

import argparse
import os

from labnode import Gantry
from labnode.server import LOOPBACK_HOSTS, TOKEN_ENV, create_app
from zaber_motion import Units
from zaber_motion.ascii import Connection


NAME = "gantry"
# Zaber chain layout, as in gantry-communication's pollGantry(): the XYZ
# gantry is the second device; x is lockstep group 1 (two motors), y and z
# are axes 3 and 4.
GANTRY_DEVICE_INDEX = 1
X_LOCKSTEP = 1
Y_AXIS = 3
Z_AXIS = 4


class MotionController(Gantry):
    name = NAME

    def __init__(self, serial_port):
        self.connection = Connection.open_serial_port(serial_port)
        self.device = self.connection.detect_devices()[GANTRY_DEVICE_INDEX]
        # A lockstep group reports its primary (first) axis.
        x_axis = self.device.get_lockstep(X_LOCKSTEP).get_axis_numbers()[0]
        self.axes = {"x": x_axis, "y": Y_AXIS, "z": Z_AXIS}
        # Native position units are linear, so convert once here and reuse
        # the scale instead of asking the library on every read.
        self.mm_per_step = {
            name: self.device.get_axis(number).settings.convert_from_native_units(
                "pos", 1, Units.LENGTH_MILLIMETRES)
            for name, number in self.axes.items()
        }

    def move(self, x, y, z, params):
        raise NotImplementedError

    def position(self):
        # One "get pos" to the whole device answers with every axis in one
        # reply, one serial round trip instead of one per axis.
        steps = self.device.generic_command("get pos").data.split()
        return {name: float(steps[number - 1]) * self.mm_per_step[name] for name, number in self.axes.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8100)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--serial-port", default="COM6", help="serial port of the Zaber chain")
    args = parser.parse_args()
    token = os.environ.get(TOKEN_ENV) or None
    if token is None and args.host not in LOOPBACK_HOSTS:
        parser.error(f"set {TOKEN_ENV} before listening on {args.host}")

    import uvicorn

    print(f"{NAME} listening on http://{args.host}:{args.port}", flush=True)
    # The manager polls several times a second, so skip per-request logs.
    uvicorn.run(create_app(MotionController(args.serial_port), token), host=args.host, port=args.port, access_log=False)


if __name__ == "__main__":
    main()
