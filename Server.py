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

        # Enables the serversocket to accept connections
        self.serversocket.listen()
    
    """
        Runs the server and creates a new thread for every connection
    """
    def run(self, technologies):
        # Unique data to send back
        thread_id = 0
        print("[SERVER] Running...")
        while True:
            # Accept the connection of the clients
            (clientsocket, address) = self.serversocket.accept()
            # Start a new thread to handle the client
            _thread.start_new_thread(client_thread, (clientsocket, thread_id, technologies))
            thread_id = thread_id + 1

def get_technology_to_use(technologies, technology_to_use):
    return technologies.get(technology_to_use)

"""
    Receives data from a client (Raspberry Pi). It sends back the dict received from the server if the confirmation was a succes.
    Otherwise send back a dict to notify the client the confirmation failed.
"""
def client_thread(clientsocket, thread_id, technologies):
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

    if confirmation.get("has_reach"):
        # Retrieve the tech to use by using the confirmation message with key has_reach
        technology = get_technology_to_use(technologies, confirmation.get("has_reach"))
        send_reply(clientsocket=clientsocket, reply={"reply": technology.has_reach()}, max_msg_length=max_msg_length)
    else:
        technology_to_use = get_technology_to_use(technologies, confirmation.get("technology"))
        if technology_to_use:
            # Send the confirmation with the specified technology
            reply = acknowledge(thread_id, technology_to_use, confirmation)
        else:
            reply = False

        # Send the reply. If it was succesful send the retrieved dict. Otherwise send False back to the rpi
        if reply:
            print("[THREAD {}] Confirmation SUCCESSFUL!".format(thread_id))
            send_reply(clientsocket, reply, max_msg_length)
        else:
            print("[THREAD {}] Confirmation FAILED!".format(thread_id))
            send_reply(clientsocket=clientsocket, reply={"reply": False}, max_msg_length=max_msg_length)

    clientsocket.close()

def send_reply(clientsocket, reply, max_msg_length):
    # Sends back True or False to notify the raspberry pi if the confirmation or the has_reach was a succes or not
    reply = json.dumps(reply)
    reply = reply.replace('"', "'") # change to single otherwise the python interpreter on the rpi will add \ characters wich causes the length to mismatch and the program to crash
    clientsocket.send(pad_msg_length(max_msg_length, len(reply)))
    clientsocket.send(reply.encode())

"""
    Send a acknowledgement over the 4G network, LoRaWAN or Wifi6
"""
def acknowledge(thread_id, technology, confirmation):
    if confirmation.get("technology") == "Wifi":
        print("[THREAD {}] Transmitting with {}...".format(thread_id, technology))
        reply = technology.acknowledge(confirmation)
    elif confirmation.get("technology") == "LoRaWAN":
        print("[THREAD {}] Transmitting with {}...".format(thread_id, technology))
        reply = technology.send(confirmation)
    elif confirmation.get("technology") == "LTE":
        print("[THREAD {}] Transmitting with {}...".format(thread_id, technology))
        reply = technology.sendLTE(confirmation)
    else:
        return False

    return reply