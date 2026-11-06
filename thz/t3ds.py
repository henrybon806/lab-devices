"""The T3DS vendor GUI, as the few operations a scan needs.

The GUI has no API, so it is driven the way a person drives it: AHK clicks its
buttons, and its status line and stage position are read back by OCR of the
pixels they are drawn in. Every coordinate here is therefore a calibration,
not a constant.

CALIBRATION
    The window is pinned to a known spot (WINDOW_ORIGIN) and then clicked and
    read at fixed screen pixels, so the display resolution and scaling must
    match the machine these were measured on. If scans stop starting or the
    status never leaves Idle, re-measure HOME_BUTTON, SCAN_BUTTON,
    STATUS_REGION and COORDS_REGION before looking anywhere else.
"""

from __future__ import annotations

import re
import time

import mss
import pytesseract
from ahk import AHK
from PIL import Image


WINDOW = "T3DS-Terahertz Time-Domain Spectroscopy"
# Every click and read below is absolute, so the window goes here first.
WINDOW_ORIGIN = (25, 25)
HOME_BUTTON = (355, 532)
SCAN_BUTTON = (355, 602)
# {left, top, width, height} strips holding the status line and the stage
# position readout.
STATUS_REGION = {"left": 1000, "top": 130, "width": 400, "height": 30}
COORDS_REGION = {"left": 830, "top": 220, "width": 370, "height": 30}
# Windows installs the Tesseract binary outside the venv; override with
# TESSERACT_CMD if it is somewhere else.
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# The GUI needs a beat to come to the front before its pixels are worth
# clicking or reading.
FOCUS_SETTLE_S = 0.25
# OCR on a 30px strip misreads now and then, so a failed parse is retried
# rather than failing the scan.
OCR_ATTEMPTS = 3
OCR_RETRY_S = 0.5

IDLE = "Idle"


class ScreenReadError(RuntimeError):
    """OCR could not make sense of the strip it read (the GUI moved, or the
    display scaling changed, or a window is covering it)."""


class T3DS:

    def __init__(self, tesseract_cmd=TESSERACT_CMD):
        # One AHK instance, held: each one starts an AutoHotkey process.
        self.ahk = AHK()
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def home(self):
        """Click "home stages". Returns as soon as the click lands."""
        self._click(HOME_BUTTON)

    def start_scan(self):
        """Click "start". Returns as soon as the click lands."""
        self._click(SCAN_BUTTON)

    def status(self):
        """The GUI's status line, as words, "Status:" dropped."""
        words = self._read(STATUS_REGION)
        if not words or words[0] != "Status:":
            raise ScreenReadError(f"status strip did not read as a status line: {words}")
        return words[1:]

    def is_idle(self):
        status = self.status()
        return bool(status) and status[0] == IDLE

    def coordinates(self):
        """The stage position the GUI is showing, in its own millimetres."""
        for attempt in range(OCR_ATTEMPTS):
            words = self._read(COORDS_REGION)
            # The readout is "<label> X: <x> ... Y: <y>", so the numbers are
            # the one after the label and the one at the end.
            numbers = [re.search(r"\d+", word) for word in (words[2:3] + words[-1:])]
            if len(numbers) == 2 and all(numbers):
                return {"x": int(numbers[0][0]), "y": int(numbers[1][0])}
            if attempt + 1 < OCR_ATTEMPTS:
                time.sleep(OCR_RETRY_S)
        raise ScreenReadError(f"could not read a stage position from: {words}")

    def _focus(self):
        """Bring the GUI up and put it where the pixel geometry expects it."""
        window = self.ahk.find_window(title=WINDOW)
        if window is None:
            raise RuntimeError(f"no {WINDOW!r} window: is T3DS running?")
        window.activate()
        window.move(x=WINDOW_ORIGIN[0], y=WINDOW_ORIGIN[1])
        time.sleep(FOCUS_SETTLE_S)

    def _click(self, position):
        self._focus()
        self.ahk.mouse_move(x=position[0], y=position[1])
        self.ahk.click()

    def _read(self, region):
        """OCR one strip of the screen into words."""
        self._focus()
        with mss.MSS() as screen:
            shot = screen.grab(region)
        strip = Image.frombytes("RGB", shot.size, shot.rgb)
        return pytesseract.image_to_string(strip).split()


if __name__ == "__main__":
    # Hardware check, no node involved: is the calibration still good?
    t3ds = T3DS()
    print(f"status: {t3ds.status()}")
    print(f"coordinates: {t3ds.coordinates()}")
