# creates the remote object
# will start THZ Imaging by clicking the button

#run me in terminal
import Pyro5
import numpy as np
import ahk
from ahk import AHK
import time
from datetime import datetime
import readCoordinates
import readStatus

from Pyro5 import api

@Pyro5.api.expose
class RemoteTHZ():
    
    def __init__(self):
        super().__init__()
        self.ahk = AHK()

    def findButtonPic(self,imagePath):
    #         "C:\\Users\\TeamD\\Desktop\\kyle\\ahk\\browseButton.png"
        #self.ahk = AHK()
        return self.ahk.image_search(imagePath)

    def getWindow(self,windowName):
        self.win = ahk.find_window(title=windowName)
        self.win.activate()
        return self.win

    def findButtonText(self,buttonName):
        buttonList = self.win.list_controls()
        button = [x for x in buttonList if x.get_text()==buttonName]

        return button[0]

    def clickButton(self,buttonName,windowName):
        self.ahk.control_click(
            button='L',  # Left mouse button
            click_count=1,
            control=buttonName,  # Control name (e.g., Button1)
            title=windowName,  # Window title
        )
        
    def startTDS(self):
        self.getWindow('T3DS-Terahertz Time-Domain Spectroscopy')
        self.win.move(x=25,y=25)
        time.sleep(0.25)
        self.ahk.mouse_move(x=355,y=602)
        self.ahk.click()
        print("started")

    def homeStages(self):
        self.getWindow('T3DS-Terahertz Time-Domain Spectroscopy')
        self.win.move(x=25,y=25)
        time.sleep(0.25)
        self.ahk.mouse_move(x=355,y=532)
        self.ahk.click()
        print("homed")
    
    def ping(self):
        print("pinged")
        return "pinged"
    
    def checkCoordinates(self):
        self.getWindow('T3DS-Terahertz Time-Domain Spectroscopy')
        self.win.move(x=25,y=25)
        time.sleep(0.25)
        coords = readCoordinates.main()
        #print(coords)
        return(coords)

    def checkStatus(self):
        self.getWindow('T3DS-Terahertz Time-Domain Spectroscopy')
        self.win.move(x=25,y=25)
        time.sleep(0.25)
        status = readStatus.main()
        return status

def start_server():
    # Create the Pyro5 daemon (the server that listens for remote calls)
    # host="0.0.0.0" means it accepts connections from any IP on your network
    # Change the port if needed
    daemon = Pyro5.server.Daemon(host="0.0.0.0", port=9090)

    # Register your class with the daemon, giving it a simple name
    uri = daemon.register(RemoteTHZ, objectId="ahk.thz")

    print(f"Server is running. URI: {uri}")
    print("Waiting for remote calls...")

    # This blocks and keeps the server alive, listening for connections
    daemon.requestLoop()

if __name__ == "__main__":
    start_server()