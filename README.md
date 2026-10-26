# lab-devices

The real lab hardware: each instrument, and later the gantry itself. Each
folder is one device and runs as a [labnode](https://github.com/henrybon806/labnode) HTTP node on the
computer attached to that device. The gantry
([gantry-manager](../gantry-manager)) talks to them only over HTTP.

## Layout

```text
templates/
  experiment/       copy to start a new instrument
  gantry/           copy to gantry/ to start the gantry node
<device>/         one folder per device (an instrument, or gantry/)
  node.py           the labnode node and its entry point
  requirements.txt  optional: drivers or SDKs only this device needs
requirements.txt  shared dependencies (labnode, pinned to a tag)
```

## Set up a lab computer

```bash
git clone <this repo> && cd lab-devices
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -r <device>/requirements.txt   # if it has one
```

## Run a node

```bash
LABNODE_TOKEN=... .venv/bin/python <device>/node.py --host 0.0.0.0 --port 8001
```

Listening beyond localhost needs `LABNODE_TOKEN`; the gantry uses the same
token. Open `http://<host>:<port>/docs` to try the node by hand.

## Add an instrument

1. Copy `templates/experiment/` to a folder named after the instrument.
2. Set `NAME` and implement `run()` (and `stop()` if the hardware can halt).
3. Add the node's name, address and bed position to the gantry's presets.

## Add the gantry

1. Copy `templates/gantry/` to `gantry/`.
2. Implement `move()` and `position()` with calls to the motion controller,
   plus `pick()`, `place()`, `home()` and `stop()` if the hardware has them.
3. Run it on the computer wired to the controller (port 8100 by default).

## Upgrading labnode

Bump the tag in `requirements.txt` and reinstall. To try unreleased labnode
changes, install from the sibling clone: `.venv/bin/pip install ../labnode`.
