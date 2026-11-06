# thz

The T3DS terahertz time-domain spectrometer. The vendor GUI has no API, so
this node drives it the way a person does: AHK clicks its buttons, and the
status line and stage position are read back by OCR of the pixels they are
drawn in.

```text
node.py   the labnode node: one scan = home, wait, start, wait
t3ds.py   the GUI itself: the clicks, the screen reads, and their calibration
```

Because it clicks and reads fixed screen pixels, the node must run **on the
Windows computer wired to the instrument**, with the T3DS window open and
nothing covering it.

## Before the first run

On that Windows computer:

1. **AutoHotkey** installed and on `PATH` (the `ahk` package drives it, it
   does not ship it).
2. **Tesseract** installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`.
   Elsewhere is fine, pass `--tesseract-cmd` or set `TESSERACT_CMD`.
3. The venv, from the repo root:

   ```bash
   python -m venv .venv
   .venv/Scripts/pip install -r requirements.txt
   .venv/Scripts/pip install -r thz/requirements.txt
   ```

4. **T3DS open, with the scan already set up**: step size, interval,
   integration time, and the imaging parameters if you are imaging. The GUI
   owns all of that, so a run means "whatever is currently configured", and
   the GUI also names the output file. Collect your reference scan first.

## Check the calibration

Before involving the node at all, confirm the screen reads still work:

```bash
.venv/Scripts/python thz/t3ds.py
```

Expect something like:

```text
status: ['Idle']
coordinates: {'x': 0, 'y': 0}
```

A `ScreenReadError` or a nonsense number means the GUI is not where the pixel
geometry expects it. Re-measure `HOME_BUTTON`, `SCAN_BUTTON`,
`STATUS_REGION` and `COORDS_REGION` at the top of `t3ds.py` before looking
anywhere else; display resolution or scaling changes break them silently.

## Run the node

```bash
.venv/Scripts/python thz/node.py --port 8001
```

For the gantry on another computer to reach it, listen wider and set a token
(the gantry must use the same one):

```bash
LABNODE_TOKEN=secret .venv/Scripts/python thz/node.py --host 0.0.0.0 --port 8001
```

`http://127.0.0.1:8001/docs` is the whole API in a browser, if you would
rather click than curl.

## A simple test

One command: start a scan, poll until it settles, print the result. From your
Mac against the Windows box, or with `127.0.0.1:8001` on the machine itself:

```bash
curl -sX POST 128.3.106.212:8001/start -H 'content-type: application/json' -d '{"sample_id":"test","params":{}}' >/dev/null && until curl -s 128.3.106.212:8001/status | grep -qE '"state":"(done|stopped|error)"'; do sleep 5; done; curl -s 128.3.106.212:8001/status
```

Add `-H "authorization: Bearer $LABNODE_TOKEN"` to both curls if you set a
token. This is bash/zsh, so run it from the Mac or Git Bash, not PowerShell.

A finished scan ends with `"state":"done"` and:

```json
"result":{"completed":true,"coordinates":{"x":0,"y":0}}
```

The same thing with friendlier output, and it runs in PowerShell too
(`smoke_test.py` is at the repo root and works against any node):

```bash
.venv/Scripts/python smoke_test.py 8001                     # start, watch, collect
.venv/Scripts/python smoke_test.py 8001 --status-only        # just look
.venv/Scripts/python smoke_test.py 8001 -p home=false        # skip homing
.venv/Scripts/python smoke_test.py 8001 --stop-after 10      # exercise /stop
```

```text
thz (experiment, labnode 0.2.0) supports {'stop': True, 'position': False}
  idle

starting test with {}
  busy  sample=test  elapsed=0s
  busy  sample=test  elapsed=5s
  done  sample=test  elapsed=312s

finished in done after 312s
result: {"completed": true, "coordinates": {"x": 0, "y": 0}}
collected, node is idle again
```

For a first test, keep it short so you are not waiting an hour on a mistake:
`-p home=false -p timeout_s=600`.

## What the gantry does

The same three calls, which is the whole contract:

```python
node.start("sample_1", {})   # POST /start, returns at once; run() is a thread
# poll node.status()["state"] until it leaves "busy"
node.taken("sample_1")       # POST /taken, once the sample is physically back
```

The node stays `occupied` until `/taken`, which is what stops a second sample
being loaded onto an unemptied stage.

## Params

All optional, all in `params`:

| param | default | effect |
|---|---|---|
| `home` | `true` | Home the stages and wait for Idle before scanning. |
| `timeout_s` | `3600` | How long to wait for Idle, per stage. Exceeding it puts the node in `error`. |
| `poll_s` | `5` | Seconds between status reads. Each one activates and repositions the window, so keep it a few seconds. |
| `estimate_s` | none | Expected duration, only used to fill in `remaining` in `/status`. |

## Known gaps

- **The scan settings are not params.** Step size, interval, integration time
  and the imaging parameters are set by hand in the GUI. The old
  `Gantry-Communication/stations/terahertz.py` typed them in with AHK
  (`ahk_text()`); that is the code to port if they should be per-sample.
- **`sample_id` is accepted but unused.** The GUI names its own output files,
  so nothing ties a labnode sample to the saved dataset yet.
- **`stop()` cannot abort a scan.** The GUI has no abort button, so `/stop`
  makes the node stop waiting and report `stopped`; the instrument finishes
  the scan by itself.
