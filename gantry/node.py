"""Template for the real gantry node. Copy this folder to gantry/ and fill in
the methods with calls to the motion controller.

    .venv/bin/python gantry/node.py --port 8100
    LABNODE_TOKEN=... .venv/bin/python gantry/node.py --host 0.0.0.0 --port 8100

Listening on anything other than localhost (so a manager on another computer
can reach it) needs LABNODE_TOKEN set, and the manager must use the same token.
Coordinates are the gantry's own (raw) units; the manager converts from bed
coordinates through its calibration.
"""

from __future__ import annotations

import argparse
import os

from labnode import Gantry
from labnode.server import LOOPBACK_HOSTS, TOKEN_ENV, create_app


NAME = "gantry"


class MotionController(Gantry):
    name = NAME

    def move(self, x, y, z, params):
        # Travel to (x, y), and to z if it is not None. Return once arrived.
        # Check self.stop_requested while waiting and return early when set.
        raise NotImplementedError

    def position(self):
        # Read the controller's current position.
        raise NotImplementedError

    # Optional: delete any you do not need. The manager sees which ones exist
    # under "supports" in /status.

    def pick(self, params):
        # Lower, grip and raise. params may name the station or sample.
        raise NotImplementedError

    def place(self, params):
        # Lower, release and raise.
        raise NotImplementedError

    def home(self, params):
        # Run the controller's homing routine.
        raise NotImplementedError

    def stop(self):
        # Halt motion right away (emergency stop).
        raise NotImplementedError


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8100)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    token = os.environ.get(TOKEN_ENV) or None
    if token is None and args.host not in LOOPBACK_HOSTS:
        parser.error(f"set {TOKEN_ENV} before listening on {args.host}")

    import uvicorn

    print(f"{NAME} listening on http://{args.host}:{args.port}", flush=True)
    # The manager polls several times a second, so skip per-request logs.
    uvicorn.run(create_app(MotionController(), token), host=args.host, port=args.port, access_log=False)


if __name__ == "__main__":
    main()
