
'''
project: half-duplex, slimmer maken multiconnectivity modem
author: Alfred Espinosa Encarnación, Frank Montenij
Description: This class is able to connect to TheThingsNetwork and send messages to using LoRaWAN.

Changelog: Alfred created the file.
           Frank added everything except for the __init__ method and the getWLAN method.
           But the __init__ method he did change. For example, Frank added the fields target_host, target_port and max_msg_length.
'''

from network import WLAN # type: ignore the line
import uping # type: ignore the line
import socket
import json
import machine # type: ignore the line

class NotAbleToConnectError(Exception):
    """This Error is raised when a socket object is not able to connect to a target."""


class WiFi:
    """Class to utilize WiFi to connect with the network on board of the ship."""

    def __init__(self):
        self.wlan = WLAN(mode=WLAN.STA)
        self.ssid = 'NETWORK_SSID'
        self.pswd = 'NETWORK_PASSWORD'
        self.static_address = ('ASSIGN_STATIC_IP', 'SUBENTMASK', 'DEFAULT_GATEWAY', 'DNS')
        # example self.static_address = ('192.168.178.81', '255.255.255.0', '192.168.1.10', '8.8.8.8')
        self.client = socket.socket()
        self.target_host = "test1.cfns.nl"
        self.target_port = 65532
        self.max_msg_length = 10

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
        This method checks if the server can reach the host at a port with the option to do this without printing the ping result on the screen.
    """ 
    def has_reach(self):
        try:
            response = uping.ping(host=socket.getaddrinfo(self.target_host, self.target_port)[0][4][0], quiet=True)
            return True if response[0] >= 1 and response[1] >= 1 else False
        except OSError:
            print("Not able to reach {}".format(self.target_host))
            return False

    """
        This method is used to initialise a socket. But also to reset the socket so that it can connect again. 
    """
    def init_socket(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    """
        This method tries to connect to the target with host=host and port=port. 
        If that fails it raises an NotAbleToConnectError
    """
    def connect(self, host, port):
        try:
            self.client.connect(socket.getaddrinfo(host, port)[0][4])
        except OSError:
            raise(NotAbleToConnectError)
    
    """
        This method sends a DISCONNECT message to the target to close the connection without causing any errors.
    """
    def disconnect(self, max_msg_length):
        close_message = json.dumps({"DISCONNECT": True}) # This is the message used to close the connection
        length_close_message = pad_msg_length(max_msg_length, len(close_message))

        # Disconnect
        self.client.send(length_close_message)
        self.client.send(close_message.encode())

        # Close the socket
        self.client.close()

    """
        This method sends a message to the target specified in the init of WiFi.
        And returns the reply of the host.
    """
    def send(self, dict):
        # Prepare the messages
        message = json.dumps(dict)
        message_length = pad_msg_length(self.max_msg_length, len(message))

        # Send the messages
        self.client.send(message_length)
        self.client.send(message.encode())

        # Receive the confirmation from the server
        reply_length = self.client.recv(self.max_msg_length).decode()
        
        if len(reply_length) == 0:
            return False

        reply = self.client.recv(int(reply_length)).decode()
        reply = json.loads(reply)

        return reply

    """
        Is responsible for the complete confirmation proces when Wifi is being used.
    """
    def acknowledge(self, confirmation):
        # Check if there is an internet connection established
        if not self.wlan.isconnected(): # If not try to reconnect. If that fails return False
            if not self.getWLAN():
                return False

        # Create a new socket
        self.init_socket()

        # Try to connect otherwise return False
        try:
            self.connect(self.target_host, self.target_port) 
        except NotAbleToConnectError:
            return False

        reply = self.send(confirmation)
        self.disconnect(self.max_msg_length)

        return reply

"""
    pad the var msg_length to the padding size. 
    So that the message containing the msg_length has a fixed size of padding size.
"""
def pad_msg_length(padding_size, msg_length):
    msg_length = str(msg_length).encode()
    msg_length += b' ' * (padding_size - len(msg_length))
    return msg_length

