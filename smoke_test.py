"""Drive one node by hand, the way the gantry will: start a sample, watch
/status until it settles, collect it. Works against any experiment node.

    .venv/bin/python smoke_test.py 8001                                      # one scan, localhost
    .venv/bin/python smoke_test.py http://127.0.0.1:8001 --status-only       # just look
    .venv/bin/python smoke_test.py http://127.0.0.1:8001 -p home=false -p timeout_s=600
    .venv/bin/python smoke_test.py http://192.168.1.50:8001 --token secret   # remote node

Params are node-specific; the THz node takes home, timeout_s, poll_s and
estimate_s. --stop-after exercises the emergency stop instead of waiting.
Exits 0 only if the node finished in "done".
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from labnode import NodeClient, NodeError, NodeUnreachable


BUSY_STATES = {"busy", "stopping"}


def parse_param(text):
    """k=v into a typed pair, so timeout_s=600 is a number and home=false a bool."""
    key, sep, raw = text.partition("=")
    if not sep:
        raise argparse.ArgumentTypeError(f"--param wants key=value, got {text!r}")
    try:
        # JSON covers numbers, true/false/null, and quoted or bracketed values.
        return key, json.loads(raw)
    except json.JSONDecodeError:
        return key, raw


def show_status(status):
    bits = [status["state"]]
    if status.get("sample_id"):
        bits.append(f"sample={status['sample_id']}")
    if status.get("elapsed") is not None:
        bits.append(f"elapsed={status['elapsed']:.0f}s")
    if status.get("remaining") is not None:
        bits.append(f"remaining={status['remaining']:.0f}s")
    print("  " + "  ".join(bits), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("address", help="e.g. http://127.0.0.1:8001")
    parser.add_argument("--token", default=os.environ.get("LABNODE_TOKEN"), help="defaults to $LABNODE_TOKEN")
    parser.add_argument("--sample-id", default="smoke-test")
    parser.add_argument("-p", "--param", action="append", type=parse_param, default=[],
                        metavar="KEY=VALUE", help="repeatable; passed through to run()")
    parser.add_argument("--poll", type=float, default=5.0, help="seconds between /status reads")
    parser.add_argument("--timeout", type=float, default=3900.0, help="give up watching after this long")
    parser.add_argument("--status-only", action="store_true", help="print /status and stop")
    parser.add_argument("--stop-after", type=float, metavar="SECONDS",
                        help="POST /stop this far into the run, to test stopping")
    parser.add_argument("--keep", action="store_true", help="skip /taken, leaving the node occupied")
    args = parser.parse_args()

    # Long enough that a node busy with the hardware still answers.
    node = NodeClient(args.address, args.token, timeout=10.0)

    try:
        status = node.status()
    except (NodeError, NodeUnreachable) as exc:
        print(f"could not reach {args.address}: {exc}", file=sys.stderr)
        return 1
    print(f"{status['name']} ({status['kind']}, labnode {status['labnode']}) supports {status['supports']}")
    show_status(status)
    if args.status_only:
        return 0

    if status["state"] != "idle":
        print(f"node is {status['state']}, not idle -- POST /taken first, or --status-only", file=sys.stderr)
        return 1

    params = dict(args.param)
    print(f"\nstarting {args.sample_id} with {params or '{}'}")
    status = node.start(args.sample_id, params)
    show_status(status)

    started = time.monotonic()
    stopped = False
    while status["state"] in BUSY_STATES:
        if time.monotonic() - started > args.timeout:
            print(f"still {status['state']} after {args.timeout:g}s, giving up watching", file=sys.stderr)
            return 1
        if args.stop_after is not None and not stopped and time.monotonic() - started >= args.stop_after:
            print(f"\nstopping after {args.stop_after:g}s")
            status = node.stop()
            stopped = True
            show_status(status)
            continue
        time.sleep(args.poll)
        status = node.status()
        show_status(status)

    print(f"\nfinished in {status['state']} after {status['elapsed']:.0f}s")
    if status.get("error"):
        print(f"error: {status['error']}", file=sys.stderr)
    if status.get("result") is not None:
        print(f"result: {json.dumps(status['result'])}")

    if not args.keep:
        # The gantry does this once it has physically taken the sample back;
        # without it the node stays occupied and refuses the next start.
        node.taken(args.sample_id)
        print("collected, node is idle again")

    return 0 if status["state"] == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
