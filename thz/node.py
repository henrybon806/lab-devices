"""THZ experiment. Run it, then open http://127.0.0.1:8000/docs.

    python thz/node.py
"""

import time

from labnode import Experiment, serve


class THZ(Experiment):
    name = "|THz|"

    def estimate(self, params):
        return -1

    def run(self, sample_id, params):

    def stop(self):
        # A real instrument would send its abort command here. run() sees
        # stop_requested and returns on its own.
        pass

if __name__ == "__main__":
    serve(THZ(), host="127.0.0.1", port=8000)
