"""The THz node: the T3DS terahertz time-domain spectrometer.

One scan is a sequence of clicks and waits in the vendor GUI; t3ds.py does the
clicking and reading, and this turns it into a labnode node the gantry can
start over HTTP. It has to run on the Windows computer wired to the
instrument, with the T3DS window open and the scan settings already dialled
in: the GUI owns the step size, interval, integration time and output
filename, so a run here means "whatever is currently configured".

    .venv/bin/python thz/node.py --port 8001
    LABNODE_TOKEN=... .venv/bin/python thz/node.py --host 0.0.0.0 --port 8001

Listening on anything other than localhost (so the gantry computer can reach
it) needs LABNODE_TOKEN set, and the gantry must use the same token. On a lab
network where that is more trouble than it is worth, --insecure drops it.
"""

from __future__ import annotations

import argparse
import os
import time

from labnode import Experiment
from labnode.server import LOOPBACK_HOSTS, TOKEN_ENV, create_app

from t3ds import TESSERACT_CMD, T3DS


NAME = "thz"
# A scan takes minutes and homing is slower than it looks, so give each stage
# plenty of room; the gantry's own timeout is the real limit.
DEFAULT_TIMEOUT_S = 3600.0
DEFAULT_POLL_S = 5.0
# The GUI needs a moment to leave Idle after a click. Polling before it does
# would read the status from before the click and call the scan finished.
START_SETTLE_S = 5.0


class Timeout(RuntimeError):
    """The GUI never went back to Idle, so the scan's outcome is unknown."""


class THZ(Experiment):
    name = NAME

    def __init__(self, tesseract_cmd=TESSERACT_CMD):
        self.t3ds = T3DS(tesseract_cmd)

    def estimate(self, params):
        # Only the T3DS scan settings know how long a scan takes, and they
        # live in the GUI, so the caller tells us if it knows.
        seconds = params.get("estimate_s")
        return None if seconds is None else float(seconds)

    def run(self, sample_id, params):
        home = bool(params.get("home", True))
        timeout_s = float(params.get("timeout_s", DEFAULT_TIMEOUT_S))
        poll_s = float(params.get("poll_s", DEFAULT_POLL_S))

        if home:
            self.t3ds.home()
            if not self._wait_until_idle(timeout_s, poll_s):
                return {"completed": False, "stage": "home"}

        self.t3ds.start_scan()
        if not self._wait_until_idle(timeout_s, poll_s):
            return {"completed": False, "stage": "scan"}

        return {"completed": True, "coordinates": self.t3ds.coordinates()}

    def stop(self):
        # The GUI has no abort button to click, so there is nothing to send.
        # run() sees stop_requested while polling and returns on its own,
        # leaving the scan to finish by itself.
        pass

    def _wait_until_idle(self, timeout_s, poll_s):
        """Poll until the GUI reports Idle. False if we were asked to stop."""
        deadline = time.monotonic() + timeout_s
        time.sleep(min(START_SETTLE_S, timeout_s))
        while True:
            if self.stop_requested:
                return False
            if self.t3ds.is_idle():
                return True
            if time.monotonic() >= deadline:
                raise Timeout(f"T3DS was still busy after {timeout_s:g}s")
            time.sleep(poll_s)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--tesseract-cmd", default=os.environ.get("TESSERACT_CMD", TESSERACT_CMD))
    parser.add_argument("--insecure", action="store_true",
                        help=f"listen beyond localhost without {TOKEN_ENV}: anything that can "
                             "reach the port can start and stop scans")
    args = parser.parse_args()
    token = os.environ.get(TOKEN_ENV) or None
    if token is None and args.host not in LOOPBACK_HOSTS and not args.insecure:
        parser.error(f"set {TOKEN_ENV} before listening on {args.host}, or pass --insecure")

    import uvicorn

    print(f"{NAME} listening on http://{args.host}:{args.port}", flush=True)
    if token is None and args.host not in LOOPBACK_HOSTS:
        print("  no token: anything on the network can start a scan", flush=True)
    # The gantry polls several times a second, so skip per-request logs.
    uvicorn.run(create_app(THZ(args.tesseract_cmd), token), host=args.host, port=args.port, access_log=False)


if __name__ == "__main__":
    main()
