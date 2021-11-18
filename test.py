import unittest
import Wifi
import uping # type: ignore the line

class WifiTester(unittest.TestCase):
    def __init__(self):
        self.wifi_instance = Wifi.WiFi()
        self.prepare_tests()

    def prepare_tests(self):
        while not self.wifi_instance.wlan.isconnected():
            self.wifi_instance.getWLAN()
    
    def prepare_connection(self):
        self.wifi_instance.init_socket()

    def restore_wifi(self):
        self.wifi_instance = Wifi.WiFi()

    def test_ping(self):
        # Test in perfect condition
        expected_result = True
        result = self.wifi_instance.has_reach(host=self.wifi_instance.target_host, port=self.wifi_instance.target_port)
        self.assertEqual(result, expected_result)

        # Test when the FiPy has no connection
        self.restore_wifi()
        expected_result = False
        result = self.wifi_instance.has_reach(host=self.wifi_instance.target_host, port=self.wifi_instance.target_port)
        self.assertNotEqual(result, expected_result)

    def test_connect_to_server(self):
        # Prepare the test
        self.prepare_connection()

        # Test if the FiPy can succesfully connect. So connect returns None
        expected_result = None
        result = self.wifi_instance.connect(self.wifi_instance.target_host, self.wifi_instance.target_port)
        self.assertEqual(result, expected_result)

        # Test if the connect function raises an NotAbleToConnectError if it cannot connect to the target
        expected_result = Wifi.NotAbleToConnectError
        wrong_host = "192.168.178.2"
        wrong_port = 70000
        with self.assertRaises(Wifi.NotAbleToConnectError):
            self.wifi_instance.connect(wrong_host, wrong_port)

        max_msg_length = 10
        self.wifi_instance.disconnect(max_msg_length)

    def test_disconnect(self):
        # Prepare the test
        self.prepare_connection()
        self.wifi_instance.connect(self.wifi_instance.target_host, self.wifi_instance.target_port)
        max_msg_length = 10

        # Test if the FiPy can succesfully close the connection with the server
        expected_result = None
        result = self.wifi_instance.disconnect(max_msg_length)
        self.assertEqual(result, expected_result)

        # Test if the socket is really closed
        expected_error = Wifi.NotAbleToConnectError
        with self.assertRaises(expected_error):
            self.wifi_instance.connect(self.wifi_instance.target_host, self.wifi_instance.target_port)

    def test_send(self):
        # Prepare the test
        self.wifi_instance.init_socket()
        self.wifi_instance.connect(self.wifi_instance.target_host, self.wifi_instance.target_port)
        confirmation = {"test": True}
        max_msg_length = 10

        """
        Test if the FiPy can send information to a server. By sending the information to a test_server which sends back the same data to the FiPy. 
        The FiPy passes the test when the data sent and the data received match. 
        """
        expected_result = confirmation
        result = self.wifi_instance.send(confirmation, max_msg_length)
        self.wifi_instance.disconnect(max_msg_length)
        self.assertEqual(result, expected_result) 


def main():
    unittest.main(module="test")


