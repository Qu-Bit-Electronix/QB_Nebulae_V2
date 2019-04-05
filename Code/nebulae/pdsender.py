# Courtesy of hecanjob/pippi.pd
import socket
class PdSend():
    pdhost = 'localhost'
    #pdhost = "192.168.0.33"
    sport = 3000
    rport = 3001
    pd = None
    connected = False

    def __init__(self):
        self.connect()

    def connect(self):
        print 'connecting to pd'
        try:
            self.pd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print "created socket."
            self.pd.connect((self.pdhost, self.sport))
            self.connected = True
            print 'Sending to PD on port ' + str(self.sport)

        except:
            print 'Connection failed - open PD with [netreceive ' + str(self.sport) + '] at least!'

    def send(self, msgs):
        try:
            for msg in msgs:
                msg = str(msg) + ';'
                self.pd.send(msg)
        except:
            print 'Could not send. Did you open a connection?'

    def close(self):
        print 'Closing connection to PD'
        self.pd.close()
        self.connected = False

    def format(self, target, val):
        msg = target + ' ' + str(val) 
        return msg

    def is_connected(self):
        return self.connected
