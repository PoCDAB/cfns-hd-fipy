from network import LoRa
import socket
import time
import pycom
import machine
import ubinascii
from L76GNSV4 import L76GNSS

"""
    Class to utilize LoRaWAN
"""
class LoRaWAN:
    def __init__(self):
        self.lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
        
        # create a LoRa socket
        self.lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

    def initLoRa(self):
        # create an OTAA authentication parameters, change them to the provided credentials
        app_eui = ubinascii.unhexlify('INSERT_APP_EUI')
        app_key = ubinascii.unhexlify('INSERT_APP_KEY')
        #uncomment to use LoRaWAN application provided dev_eui
        dev_eui = ubinascii.unhexlify('INSERT_DEVICE_EUI')

        self.lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0)

        # wait until the module has joined the network
        pycom.heartbeat(False)

        while not self.lora.has_joined():
            print(ubinascii.hexlify(LoRa().mac()).upper())
            pycom.rgbled(0x000000)
            time.sleep(2.5)
            pycom.rgbled(0x7f0000)
            time.sleep(0.5)
            print('Not yet joined...')

        print('Joined')
        pycom.rgbled(0x000000)

        # set the LoRaWAN data rate
        self.lora_socket.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

        # make the socket blocking
        # (waits for the data to be sent and for the 2 receive windows to expire)
        self.lora_socket.setblocking(True)

    def send(self, dab_id, mstype):

        data = []
        if mstype == 1:
            data.append(dab_id)
            data.append(mstype)
            payload = convert_payload(data)
            self.lora_socket.send(bytes(payload))

        if mstype == 2 or mstype == 3:
            #location = L76.get_location(debug=False)
            #payload = convert_payload(dab_id, mstype, location["latitude"], location["longitude"], location["altitude"], location["HDOP"])
            data.append(dab_id)
            data.append(mstype)
            data.append(52.6529)
            data.append(4.746133)
            data.append(1)
            data.append(1)
            payload = convert_payload(data)

            print("Message type two")
            self.lora_socket.send(bytes(payload))

        if mstype == 4:
            #location = L76.get_location(debug=False)
            #payload = convert_payload(dab_id, mstype, location["latitude"], location["longitude"], location["altitude"], location["HDOP"])
            data.append(dab_id)
            data.append(mstype)
            data.append(30)
            data.append(1)
            payload = convert_payload(data)

            print("Message type four")
            self.lora_socket.send(bytes(payload))


"""
    A method that converts data to the format used by ttnmapper.org
"""
def convert_payload(data):

    
    payload = []

    if data[1] == 1: 
        dab_id = data[0]
        mstype = data[1]
        payload.append(int(dab_id))
        payload.append(int(mstype))
        return payload

    elif data[1] == 2 or data[1] == 3: 

        dab_id = data[0]
        mstype = data[1]
        lat = data[2]
        lon = data[3]
        alt = data[4]
        hdop = data[5]

        latb = int(((lat + 90) / 180) * 0xFFFFFF)
        lonb = int(((lon + 180) / 360) * 0xFFFFFF)
        #altb = int(round(float(alt), 1))
        altb = int(float(alt) * 10)
        hdopb = int(float(hdop) * 10)

        payload.append(int(dab_id))
        payload.append(int(mstype))

        payload.append(((latb >> 16) & 0xFF))
        payload.append(((latb >> 8) & 0xFF))
        payload.append((latb & 0xFF))
        payload.append(((lonb >> 16) & 0xFF))
        payload.append(((lonb >> 8) & 0xFF))
        payload.append((lonb & 0xFF))
        payload.append(((altb  >> 8) & 0xFF))
        payload.append((altb & 0xFF))
        payload.append(hdopb & 0xFF)    
        return payload

    elif data[1] == 4: 
        dab_id = data[0]
        mstype = data[1]
        rssi = data[2]
        srn = data[3]

        payload.append(int(dab_id))
        payload.append(int(mstype))
        payload.append(int(rssi))
        payload.append(int(srn))
        return payload
