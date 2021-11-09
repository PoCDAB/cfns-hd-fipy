'''
project: Half-Duplex
author: Alfred Espinosa Encarnación
date: 06-05-2021
Description: Software for the FiPy to send an acknowledgement over the LoRaWAN and 4G (CAT-M1) network of KPN.
'''

import pycom
from LIS2HH12 import LIS2HH12
from pycoproc_1 import Pycoproc

from LoraWAN import LoRaWAN
from LTE import CATM1
from Wifi import WiFi
from Server import Server

if __name__ == '__main__':
    try:        
        #py = os.fsformat('/flash')

        # fipy = LoRaWAN()
        ship_wifi = WiFi()
        # kpn = CATM1()

        # fipy.initLoRa()
        while not ship_wifi.wlan.isconnected():
            ship_wifi.getWLAN()
        # kpn.getLTE()

        pycom.heartbeat(False)
        
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
        
        server = Server()

        server.setup_server()

        server.run(ship_wifi)

    except RuntimeError:
        print("exit")