from network import WLAN # type: ignore the line
from datetime import datetime
import uping # type: ignore the line
import socket
import json
import machine # type: ignore the line

# Changing print to a print with the time in front
# is in Wifi.py because of import errors and Wifi does not import Server or main. So it will not give any import errors here
old_print = print

def new_print(*args, **kwargs):
    old_print(datetime.now().strftime("%H:%M:%S |"), *args, **kwargs)

print = new_print

class NotAbleToConnectError(Exception):
    pass

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
        self.target_host = "driel.rh.nl"
        self.target_port = 65532

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
        This function checks if the server with can reach the host at a port
    """ 
    def has_reach(self, host, port, quiet=True):
        try:
            response = uping.ping(host=socket.getaddrinfo(host, port)[0][4][0], quiet=quiet)
            return True if response[0] >= 1 and response[1] >= 1 else False
        except OSError:
            print("Not able to reach {}".format(host))
            return False

    def init_socket(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, host, port):
        try:
            self.client.connect(socket.getaddrinfo(host, port)[0][4])
        except OSError:
            raise(NotAbleToConnectError)
    
    def disconnect(self, max_msg_length):
        close_message = json.dumps({"DISCONNECT": True}) # This is the message used to close the connection
        length_close_message = pad_msg_length(max_msg_length, len(close_message))

        # Disconnect
        self.client.send(length_close_message)
        self.client.send(close_message.encode())

        # Close the socket
        self.client.close()

    """
        This function sends the confirmation to driel.rh.nl using Wifi. 
    """
    def send(self, confirmation, max_msg_length):
        # Prepare the messages
        confirmation = json.dumps(confirmation)
        length_confirmation = pad_msg_length(max_msg_length, len(confirmation))

        # Send the messages
        self.client.send(length_confirmation)
        self.client.send(confirmation.encode())

        # Receive the confirmation from the server
        reply_length = self.client.recv(max_msg_length).decode()
        
        if len(reply_length) == 0:
            return False

        reply = self.client.recv(int(reply_length)).decode()
        reply = json.loads(reply)

        return reply

"""
    pad the var msg_length to the padding size. 
    So that the message containing the msg_length has a fixed size of padding size.
"""
def pad_msg_length(padding_size, msg_length):
    msg_length = str(msg_length).encode()
    msg_length += b' ' * (padding_size - len(msg_length))
    return msg_length

