"""Template for a real experiment node. Copy this folder, rename it after the
instrument, and fill in NAME and run().

    .venv/bin/python <instrument>/node.py --port 8001
    LABNODE_TOKEN=... .venv/bin/python <instrument>/node.py --host 0.0.0.0 --port 8001

Listening on anything other than localhost (so the gantry computer can reach
it) needs LABNODE_TOKEN set, and the gantry must use the same token.
"""

from __future__ import annotations

import argparse
import os

from labnode import Experiment
from labnode.server import LOOPBACK_HOSTS, TOKEN_ENV, create_app


NAME = "my_instrument"


class Instrument(Experiment):
    name = NAME

    def estimate(self, params):
        # Expected seconds per sample, or None if unknown.
        return None

    def run(self, sample_id, params):
        # Do the measurement here. Check self.stop_requested often and return
        # early when it is set. The returned dict is reported in /status.
        raise NotImplementedError

    def stop(self):
        # Optional: halt the hardware right away on an emergency stop.
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    token = os.environ.get(TOKEN_ENV) or None
    if token is None and args.host not in LOOPBACK_HOSTS:
        parser.error(f"set {TOKEN_ENV} before listening on {args.host}")

    import uvicorn

    print(f"{NAME} listening on http://{args.host}:{args.port}", flush=True)
    # The GUI and gantry poll several times a second, so skip per-request logs.
    uvicorn.run(create_app(Instrument(), token), host=args.host, port=args.port, access_log=False)


if __name__ == "__main__":
    main()
