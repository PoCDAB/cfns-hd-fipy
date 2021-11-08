from network import WLAN
import uping
import socket
import json
import machine
from main import pad_msg_length

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
        self.client = socket.socket()

    """
        This function tries to connect to a network within 10 seconds. If it succeeds it will return True otherwise it will return False.
    """
    def getWLAN(self):
        networks = self.wlan.scan()
        for network in networks:
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
            response = uping.ping(socket.getaddrinfo("driel.rh.nl", 65532)[0][4][0])
            return True if response[0] == 4 and response[1] > 1 else False
        except OSError:
            print("Not able to reach")
            return False
        return False
    
    """
        This function sends the confirmation to driel.rh.nl using Wifi. 
    """

    def init_socket(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.client.connect(socket.getaddrinfo("driel.rh.nl", 65532)[0][4])
    
    def disconect(self, max_msg_length):
        close_message = json.dumps({"DISCONNECT": True}) # This is the message used to close the connection
        length_close_message = pad_msg_length(max_msg_length, len(close_message))

        # Disconnect
        self.client.send(length_close_message)
        self.client.send(close_message.encode())

    def send(self, confirmation, max_msg_length):
        # Prepare the messages
        confirmation = json.dumps(confirmation)
        length_confirmation = pad_msg_length(max_msg_length, len(confirmation))

        # Send the messages
        self.client.send(length_confirmation)
        self.client.send(confirmation.encode())

        # Receive the confirmation from the server
        ack_length = self.client.recv(max_msg_length).decode()
        ack = self.client.recv(int(ack_length)).decode()
        ack = json.loads(ack)

        print(ack)
        return True if data.get("received") == True else False
