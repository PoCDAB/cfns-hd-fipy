'''
project: Half-Duplex
author: Alfred Espinosa Encarnación
date: 06-05-2021
Description: Software for the FiPy to send an acknowledgement over the LoRaWAN and 4G (CAT-M1) network of KPN.
'''

from network import LoRa, WLAN, LTE
import uping
import socket
import time
import json
import _thread
import machine
import ubinascii
import usocket
import pycom
import json
from LIS2HH12 import LIS2HH12
from L76GNSV4 import L76GNSS
from machine import ADC
from pycoproc_1 import Pycoproc


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
    Class to utilize CAT-M1
"""
class CATM1:
    def __init__(self):
        self.lte = LTE()
        self.phonebook = []
        self.phonebook.append("PHONENUMBER")  # example +31612345678

    """
        Make connection to the mobile network
    """
    def getLTE(self):
        if not self.lte.isattached():
            print('lte attaching ')
            self.lte.attach(band=20, apn="item.webtrial.m2m")
            while 1:
                if self.lte.isattached(): print(' OK'); break
                print('. ', end='')
                time.sleep(1)

        print('configuring for sms', end=' ')
        ans = self.lte.send_at_cmd('AT+CMGF=1').split('\r\n')
        print(ans, end=' ')
        ans = self.lte.send_at_cmd('AT+CPMS="SM", "SM", "SM"').split('\r\n')
        print(ans)
        ans = self.lte.send_at_cmd('AT+CSQ').split('\r\n')
        print(ans, end=' ')
        print()

    """
        Send an SMS over the mobile network
    """
    def sendLTE(self, dab_id, mstype):
        
        if mstype == 1:
            msg = "ack:" + str(dab_id) + ", mstype:" + str(mstype) + ""
        if mstype == 2 or mstype == 3:
            data = []
            data.append(dab_id)
            data.append(mstype)
            data.append(52.6529)
            data.append(4.746133)
            data.append(1)
            data.append(1)

            msg = "ack:" + str(dab_id) + ", mstype:" + str(mstype) + ", data:" + str(data) + ""
        if mstype == 4:
            msg = "ack:" + str(dab_id) + ", mstype:" + str(mstype) + ""
        for number in self.phonebook:
            print('sending an sms', end=' ');
            ans = self.lte.send_at_cmd('AT+SQNSMSSEND="' + number + '", "' + msg + '"').split('\r\n');
            print(ans)
            time.sleep(1)


"""
    Class to utilize WiFi to connect with the network on board of the ship
"""
class WiFi:
    def __init__(self):
        self.wlan = WLAN(mode=WLAN.STA)
        self.ssid = 'NETWORK_SSID'
        self.pswd = 'NETWORK_PASSWORD'
        self.static_address = ('ASSIGN_STATIC_IP', 'SUBENTMASK', 'DEFAULT_GATEWAY', 'DNS')
        # example self.static_address = ('192.168.178.81', '255.255.255.0', '192.168.1.10', '8.8.8.8')
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    """
        This function tries to connect to a network within 10 seconds. If it succeeds it will return True otherwise it will return False.
    """
    def getWLAN(self):
        networks = self.wlan.scan()
        for network in networks:
            print(network)
            if network.ssid == self.ssid:
                print('Network found!')
                self.wlan.ifconfig(config=self.static_address)
                try:
                    self.wlan.connect(network.ssid, auth=(network.sec, self.pswd), timeout=10000)
                    while not self.wlan.isconnected():
                        machine.idle()  # save power while waiting
                    print('WLAN connection succeeded!')
                    return True
                except Exception as e:
                    print(e)
                    print("Failed to connect!")
                    return False
        return False
    
    """
        This function checks if the server with url driel.rh.nl is reachable or not.
    """ 
    def has_reach(self):
        try:
            response = uping.ping(socket.getaddrinfo("driel.rh.nl", 65533)[0][4][0])
            return True if response == (4, 4) else False
        except OSError:
            print("Not able to reach")
            return False
        return False
    
    """
        This function sends the confirmation to driel.rh.nl using Wifi. 
    """
    def send(self, dab_id, mstype, msg_length):
        close_message = json.dumps({"DISCONNECT": True}) # This is the message used to close the connection
        
        self.client.connect(socket.getaddrinfo("driel.rh.nl", 65533)[0][4])
        
        # Prepare the messages
        confirmation = json.dumps({"ACK": dab_id, "MSTYPE": mstype})
        length_confirmation = str(len(confirmation)).encode() + (b' ' * (msg_length - len(confirmation)))
        length_close_message = str(len(close_message)).encode() + (b' ' * (msg_length - len(close_message)))

        # Send the messages
        self.client.send(length_confirmation)
        self.client.send(confirmation.encode())

        # Receive the confirmation from the server
        ack_length = self.client.recv(msg_length).decode()
        ack = self.client.recv(int(ack_length)).decode()
        data = json.loads(ack)

        # # Disconnect
        self.client.send(length_close_message)
        self.client.send(close_message.encode())
        return True if data.get("received") == True else False

"""
    Class to setup a server on the FiPY.
"""
class Server:
    def __init__(self):
        self.serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)

    """
        Setup server with the use of an static IP assigned in the WiFi class
    """
    def setup_server(self):
        # Set up server socket
        self.serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
        self.serversocket.bind(("192.168.178.11", 8000))
        # self.serversocket.bind(("STATIC_IP", "PORT"))

        # Accept maximum of 5 connections at the same time
        self.serversocket.listen(5)
    
    """
        Runs the server
    """
    def run(self):
        # Unique data to send back
        c = 0
        print("[SERVER] Running...")
        while True:
            # Accept the connection of the clients
            (clientsocket, address) = self.serversocket.accept()
            # Start a new thread to handle the client
            _thread.start_new_thread(client_thread, (clientsocket, c))
            c = c + 1

"""
    Receives data from a client (Raspberry Pi). It sends back a number, just for debugging purpose.
"""
# Thread for handling a client
def client_thread(clientsocket, n):
    msg_length = 20 # The value is the amount of bytes the first message will be

    # Receive the length of the message
    confirmation_length = clientsocket.recv(msg_length).decode()

    # If recv() returns with 0 the other end closed the connection
    if len(confirmation_length) == 0:
        clientsocket.close()
        return
    else:
        # Receive the message with the confirmation information
        confirmation = clientsocket.recv(int(confirmation_length)).decode()

        # Do something wth the received data...
        confirmation = json.loads(confirmation)
        print("[THREAD {}] Received: {}".format(n, confirmation))
        ack = confirmation.get("ack")
        msg = confirmation.get("msg")
        technology = confirmation.get("tech")

        """
            Send a acknowledgement over the 4G network, LoRaWAN or Wifi6
        """
        if technology == "Wifi6" and ship_wifi.has_reach():
            print("[THREAD {}] Wifi6 within range.".format(n))
            print("[THREAD {}] Transmitting...".format(n))
            succes = ship_wifi.send(ack, msg, msg_length)
        elif technology == "LoRaWAN" and fipy.has_reach():
            print("[THREAD {}] LoRaWAN within range.".format(n))
            print("[THREAD {}] Transmitting...".format(n))
            succes = fipy.send(ack, msg)
        elif technology == "LTE" and kpn.has_reach():
            print("[THREAD {}] CAT-M1 within range".format(n))
            print("[THREAD {}] Transmitting...".format(n))
            succes = kpn.sendLTE(ack, msg)
        else:
            succes = False


    # Sends back True or False to notify the raspberry pi if the confirmation was a succes or not
    reply = json.dumps({"reply": succes}).encode() 
    clientsocket.send(str(len(reply)).encode() + (b' ' * (msg_length - len(reply))))
    clientsocket.send(reply)
    
    # Notify the terminal user of the succes
    print("[THREAD {}] Confirmation SUCCESSFUL!".format(n))

    # Close the socket and terminate the thread
    clientsocket.close()

if __name__ == '__main__':
    try:        
        #py = os.fsformat('/flash')
        

        # fipy = LoRaWAN()
        ship_wifi = WiFi()
        # kpn = CATM1()

        # fipy.initLoRa()
        print(ship_wifi.getWLAN())
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

        server.run()

    except RuntimeError:
        print("exit")