# lab-experiments

The real instrument nodes for the gantry. Each folder is one instrument and
runs as a [labnode](https://github.com/henrybon806/labnode) HTTP node on the
computer attached to that instrument. The gantry
([gantry-manager](../gantry-manager)) talks to them only over HTTP.

## Layout

```text
_template/        copy this to start a new instrument
<instrument>/     one folder per instrument
  node.py           the labnode Experiment subclass and its entry point
  requirements.txt  optional: drivers or SDKs only this instrument needs
requirements.txt  shared dependencies (labnode, pinned to a tag)
```

## Set up a lab computer

```bash
git clone <this repo> && cd lab-experiments
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -r <instrument>/requirements.txt   # if it has one
```

## Run a node

```bash
LABNODE_TOKEN=... .venv/bin/python <instrument>/node.py --host 0.0.0.0 --port 8001
```

Listening beyond localhost needs `LABNODE_TOKEN`; the gantry uses the same
token. Open `http://<host>:<port>/docs` to try the node by hand.

## Add an instrument

1. Copy `_template/` to a folder named after the instrument.
2. Set `NAME` and implement `run()` (and `stop()` if the hardware can halt).
3. Add the node's name, address and bed position to the gantry's presets.

## Upgrading labnode

Bump the tag in `requirements.txt` and reinstall. To try unreleased labnode
changes, install from the sibling clone: `.venv/bin/pip install ../labnode`.
