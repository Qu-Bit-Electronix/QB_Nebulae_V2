import sys
sys.path.insert(0, '/home/alarm/QB_Nebulae_V2/Code/nebulae/lib')
import sc
import os
import time
import subprocess

class SuperCollider():
    def __init__(self):
        self.path = "/home/alarm/"
        self.exedir = "/usr/bin/" #linux
        self.synth = None
        self.s = None
        self.buffersID = None
        self.nodeID = 1023 #can be whatever, we'll just be limited to one synth at a time, at this nodeID, which can be enough for most applications
        self.started = False


    def loadBuffers(self):
        self.buffersID = []
        sounds = os.listdir(self.path + "audio") #i get the list of all the .wav files in path+audio
        for i in sounds:
            try:
                self.buffersID.append(sc.loadSndAbs(self.path + "audio/" + i, True))
            except:
                print "something went wrong with " + i

    def boot(self):
        sc.start(self.exedir, 57110, 2, 2, 48000, 0, 0, 1) #remove verbosity and spew of scsynth
        self.s = sc.sc.server 
        sc.sc.synthdefpath = self.path + "scsyndef"
        sc.sc.sndpat = self.path + "audio"
        self.started = True #it's alive!
        self.loadBuffers()
        print "server has started"

    def instantiate_synth(self, which): #creates an instance of the chosen synth
        print which
        self.s = sc.sc.server
        time.sleep(0.1)
        self.s.sendMsg('/d_load', self.path + 'scsyndef/' + which + '.scsyndef')
        time.sleep(0.1)
        self.s.sendMsg('s_new', which, self.nodeID)
        

    def free_synth(self): #kills the synth
        self.s.sendMsg("/n_free", self.nodeID) 

    def setSynth(self, what, value): #what happens here is that I pass in the name of the parameter I want to change and the value
                                     #and keep on sending them 
        self.s = sc.sc.server
        
        if what == "start":
            self.s.sendMsg("/n_set", self.nodeID, "start", value)

        elif what == "reset":
            self.s.sendMsg("/n_set", self.nodeID, "reset", value)

        elif what == "density":
            self.s.sendMsg("/n_set", self.nodeID, "density", value)

        elif what == "blend":
            self.s.sendMsg("/n_set", self.nodeID, "blend", value)
        
        elif what == "speed":
            self.s.sendMsg("/n_set", self.nodeID, "speed", value)

        elif what == "pitch":
            self.s.sendMsg("/n_set", self.nodeID, "pitch", value)

        elif what == "size":
            self.s.sendMsg("/n_set", self.nodeID, "size", value)

        elif what == "overlap":
            self.s.sendMsg("/n_set", self.nodeID, "overlap", value)

        elif what == "window":
            self.s.sendMsg("/n_set", self.nodeID, "window", value)
        
        elif what == "file":
            self.s.sendMsg("/n_set", self.nodeID, "bufnum", value+1)
        
        elif what == "source":
            self.s.sendMsg("/n_set", self.nodeID, "source", value)

        elif what == "record":
            self.s.sendMsg("/n_set", self.nodeID, "record", value)

        elif what == "freeze":
            self.s.sendMsg("/n_set", self.nodeID, "freeze", value)

    def exit(self):
        cmd = "sudo killall jackd" 
        os.system(cmd)
        sc.quit()
        self.started = False #is dead
        

    def is_started(self): #is it there?
        return self.started

