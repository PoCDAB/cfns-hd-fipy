'''
project: Half-Duplex
author: Alfred Espinosa Encarnación
date: 06-05-2021
Description: Software for the FiPy to send an acknowledgement over the LoRaWAN and 4G (CAT-M1) network of KPN.
'''

import pycom # type: ignore the line
# from LIS2HH12 import LIS2HH12 # type: ignore the line
# from pycoproc_1 import Pycoproc # type: ignore the line

from LoraWAN import LoRaWAN
from LTE import CATM1
from Wifi import WiFi
from Server import Server
import test

testing = False

if __name__ == '__main__':
    # If testing is true start the testscript otherwise start the server
    if testing:
        test.main()
    else:
        try:
            #py = os.fsformat('/flash')

            # Creating the connection objects
            ship_wifi = WiFi()
            fipy = LoRaWAN()
            kpn = CATM1()
            technologies = {
                "Wifi": ship_wifi,
                "LTE": kpn,
                "LoRa": fipy
            }

            # Initializing the connection objects
            while not ship_wifi.wlan.isconnected():
                ship_wifi.getWLAN()
            # fipy.initLoRa()
            kpn.getLTE()

            pycom.heartbeat(False)

            # Initialise the GPS and accelerometer that are on the pytrack
            # py = Pycoproc(Pycoproc.PYTRACK)
            # L76 = L76GNSS(pytrack=py)
            # L76.setAlwaysOn()
            #acc = LIS2HH12(py)

            """
                Note: Use GPS only when in outdoor environment. It will get stuck in a loop when used inside to get a fix.
            """
            # L76.get_fix(force=True, debug=False)
            # if L76.fixed():
            #     print('fixed gps')
            #     pycom.rgbled(0x000f00)
            # else:
            #     L76.get_fix(force=True, debug=False)

            # print("coordinates")
            # # returns the coordinates
            # # with debug true you see the messages parsed by the
            # # library until you get a the gps is fixed
            # print(L76.coordinates(debug=False))
            # print(L76.getUTCDateTime(debug=False))

            # Create, setup and run the server
            server = Server()
            server.setup_server()
            server.run(technologies)

        except RuntimeError:
            print("exit")