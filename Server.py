import usocket
import json
import _thread
from main import acknowledge
from main import pad_msg_length
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
        thread_id = 0
        print("[SERVER] Running...")
        while True:
            # Accept the connection of the clients
            (clientsocket, address) = self.serversocket.accept()
            # Start a new thread to handle the client
            _thread.start_new_thread(client_thread, (clientsocket, thread_id))
            thread_id = thread_id + 1


"""
    Receives data from a client (Raspberry Pi). It sends back a number, just for debugging purpose.
"""
# Thread for handling a client
def client_thread(clientsocket, thread_id):
    max_msg_length = 10 # The value is the amount of bytes the first message will be

    # Receive the length of the message
    confirmation_length = clientsocket.recv(max_msg_length).decode()

    if len(confirmation_length) == 0: # If recv() returns with 0 the other end closed the connection
        clientsocket.close()
        return 
        
    # Receive the message with the confirmation information
    confirmation = clientsocket.recv(int(confirmation_length)).decode()

    # Unpack the received information
    confirmation = json.loads(confirmation)
    print("[THREAD {}] Received: {}".format(thread_id, confirmation))

    # send the confirmation with the specified technology
    succes = acknowledge(thread_id, confirmation, max_msg_length)

    # Sends back True or False to notify the raspberry pi if the confirmation was a succes or not
    reply = json.dumps({"reply": succes}).encode() 
    clientsocket.send(pad_msg_length(max_msg_length, len(reply)))
    clientsocket.send(reply)

    # Notify the terminal user of the succes
    if succes:
        print("[THREAD {}] Confirmation SUCCESSFUL!".format(thread_id))
    else:
        print("[THREAD {}] Confirmation FAILED!".format(thread_id))

    # Close the socket and terminate the thread
    clientsocket.close()