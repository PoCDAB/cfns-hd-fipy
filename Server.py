import usocket # type: ignore the line
import json
import _thread
from Wifi import pad_msg_length, NotAbleToConnectError

"""Class to setup a server on the FiPY."""
class Server:
    """Class to setup a server on the FiPY."""

    def __init__(self):
        self.serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)

    """
        Setup server with the use of an static IP
    """
    def setup_server(self):
        # Set up server socket
        self.serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
        self.serversocket.bind(("192.168.178.11", 8000))
        # self.serversocket.bind(("STATIC_IP", "PORT"))

        # Accept maximum of 5 connections at the same time
        self.serversocket.listen(5)
    
    """
        Runs the server and creates a new thread for every connection
    """
    def run(self, device):
        # Unique data to send back
        thread_id = 0
        print("[SERVER] Running...")
        while True:
            # Accept the connection of the clients
            (clientsocket, address) = self.serversocket.accept()
            # Start a new thread to handle the client
            _thread.start_new_thread(client_thread, (clientsocket, thread_id, device))
            thread_id = thread_id + 1


"""
    Receives data from a client (Raspberry Pi). It sends back the dict received from the server if the confirmation was a succes.
    Otherwise send back a dict to notify the client the confirmation failed.
"""
def client_thread(clientsocket, thread_id, device):
    max_msg_length = 10 # The value is the amount of bytes the first message will be

    # Receive the length of the message
    confirmation_length = clientsocket.recv(max_msg_length).decode()

    # If recv() returns with 0 the other end closed the connection
    if len(confirmation_length) == 0: 
        clientsocket.close()
        return 
        
    # Receive the message with the confirmation information
    confirmation = clientsocket.recv(int(confirmation_length)).decode()

    # Unpack the received information
    confirmation = json.loads(confirmation)
    print("[THREAD {}] Received: {}".format(thread_id, confirmation))

    # Send the confirmation with the specified technology
    reply = acknowledge(thread_id, device, confirmation, max_msg_length)

    # If the reply failed send this alternative reply
    if not reply:
        reply  = {"reply": False}

    # Sends back True or False to notify the raspberry pi if the confirmation was a succes or not
    reply = json.dumps(reply)
    reply = reply.replace('"', "'") # change to single otherwise the python interpreter on the rpi will add \ characters wich causes the length to mismatch and the program to crash
    clientsocket.send(pad_msg_length(max_msg_length, len(reply)))
    clientsocket.send(reply.encode())

    # Notify the terminal user of the succes
    if reply:
        print("[THREAD {}] Confirmation SUCCESSFUL!".format(thread_id))
    else:
        print("[THREAD {}] Confirmation FAILED!".format(thread_id))

    # Close the socket and terminate the thread
    clientsocket.close()


"""
    Send a acknowledgement over the 4G network, LoRaWAN or Wifi6
"""
def acknowledge(thread_id, device, confirmation, max_msg_length):
    for technology in confirmation.get("technology"):
        if technology == "Wifi" and device.has_reach(host=device.target_host, port=device.target_port, quiet=True):
            print("[THREAD {}] Wifi6 within range.".format(thread_id))
            print("[THREAD {}] Transmitting...".format(thread_id))
            
            # Check if there is an internet connection established
            if not device.wlan.isconnected(): # If not try to reconnect. If that fails return False
                if not device.getWLAN():
                    return False

            # Send the confirmation using the ship wifi
            device.init_socket()

            # Try to connect otherwise return False
            try:
                device.connect(device.target_host, device.target_port) 
            except NotAbleToConnectError:
                return False

            reply = device.send(confirmation, max_msg_length)
            device.disconnect(max_msg_length)
        elif technology == "LoRaWAN" and device.has_reach():
            print("[THREAD {}] LoRaWAN within range.".format(thread_id))
            print("[THREAD {}] Transmitting...".format(thread_id))

            reply = device.send(confirmation)
        elif technology == "LTE" and device.has_reach():
            print("[THREAD {}] CAT-M1 within range".format(thread_id))
            print("[THREAD {}] Transmitting...".format(thread_id))

            reply = device.sendLTE(confirmation)
        else:
            return False

    return reply