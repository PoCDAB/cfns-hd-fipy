from network import LTE
import time

"""
    Class to utilize CAT-M1
"""
class CATM1:
    def __init__(self):
        self.lte = LTE()
        self.phonebook = []
        self.phonebook.append("PHONENUMBER")  # example +31612345678

    """
        Test if this tech can reach a receiver. Not implemented yet.
    """
    def has_reach(self):
        ans = self.lte.send_at_cmd('AT+CSQ').split('\r\n')[1]
        if not "ERROR" in ans:
            start = ans.find(":") + len(":")
            end = ans.find(",")
            return True if not int(ans[start:end].strip()) == 99 else False
        else: 
            return False

    """
        Make connection to the mobile network
    """
    def getLTE(self):
        if not self.lte.isattached():
            print('lte attaching ')
            self.lte.attach(band=20, apn="item.webtrial.m2m")
            while 1:
                if self.lte.isattached(): 
                    print(' OK')
                    break
                print('. ', end='')
                time.sleep(1)

        print('configuring for sms', end=' ')
        ans = self.lte.send_at_cmd('AT+CMGF=1').split('\r\n')
        print(ans, end=' ')
        ans = self.lte.send_at_cmd('AT+CPMS="SM", "SM", "SM"').split('\r\n')
        print(ans)
        

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
