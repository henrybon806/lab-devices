import datetime
import math
import time
from turtle import done

import Pyro5.api

# The IP address of the AHK computer on your network
SERVER_IP = "128.3.106.212"  # Replace with the actual IP of the AHK machine
# SERVER_IP = "198.128.206.244"
PORT = 9090
uri = f"PYRO:ahk.thz@{SERVER_IP}:{PORT}"

def homeStages():
    uri = f"PYRO:ahk.thz@{SERVER_IP}:{PORT}"

    with Pyro5.api.Proxy(uri) as thz:
        thz.homeStages()

def startTDS():
    uri = f"PYRO:ahk.thz@{SERVER_IP}:{PORT}"

    with Pyro5.api.Proxy(uri) as thz:
        thz.startTDS()

def checkHomed():
    with Pyro5.api.Proxy(uri) as thz:
        coords = thz.checkCoordinates()
        return bool(coords == [0,0])

def waitUntilIdle(timeoutMins=60,checkIntervalSec = 5):
    print(f"start at: {datetime.datetime.now()}")
    numChecks = math.ceil((timeoutMins * 60)/checkIntervalSec)
    idle = False
    i=0
    with Pyro5.api.Proxy(uri) as thz:
        while (not idle) & (i < numChecks):
            status = thz.checkStatus()
            if status[0] == 'Idle':
                idle = True
                break
            i+=1
            time.sleep(checkIntervalSec)

    if idle:
        time.sleep(0.5)
        print(f"done at: {datetime.datetime.now()}")
        return True
    else:
        return False


if __name__ == "__main__":
    # homeStages()
    # print(checkHomed())
    waitUntilIdle(timeoutMins=5, checkIntervalSec=5)

    # with Pyro5.api.Proxy(uri) as thz:
    #     coords = thz.checkCoordinates()
    #     print(coords)

    # with Pyro5.api.Proxy(uri) as thz:
    #     print(thz.checkCoordinates())

    # with Pyro5.api.Proxy(uri) as thz:
    #     thz.ping()
    # startTDS()

    # main()