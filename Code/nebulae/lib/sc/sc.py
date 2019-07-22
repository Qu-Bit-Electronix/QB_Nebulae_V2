import time, os, sys
import scsynth, scosc


server = 0 # reference to app's sc server process
sndLoader = 0

synthon = 0 # did we start the scsythn process?

##workingpath = os.getcwd() # must be set to the right path in case something special is need
sndpath = os.path.join( os.getcwd() , 'sounds' )
synthdefpath = os.path.join( os.getcwd() , 'synthdefs' )


def start( exedir='', port=57110, inputs=2, outputs=2, samplerate=44100, verbose=0,
           spew=0, startscsynth=0 ) :
    """ starts scsynth process. interfaces scsynth module.
    Inits the OSC communication and classes that handle it
    exe='', exedir='', port=57110, inputs=2, outputs=2, samplerate=44100, verbose=0, spew=0
    """
    global server, sndLoader # because they are init in this func

    exe = 'scsynth'

    # if none is set take workingdir as exedir on mac and windows
    if sys.platform == 'win32' :
        exe += '.exe' # add extension
        if exedir == '' : exedir = 'C:\Program Files\SuperCollider' 
    elif os.uname()[0] == 'Linux' :
        if exedir == '' : exedir = '/usr/bin'
        if not os.path.isfile(os.path.join(exedir, exe)): # in case it is in /usr/bin/local
            print 'Error : /usr/bin/scsynth does not exist. Trying to find scsnth in /usr/local/bin...'
            exedir = '/usr/local/bin'
    elif sys.platform == 'darwin':
        if exedir == '' : exedir = '/Applications/SuperCollider'

    print "trying to run scsynth from :", exedir

    server = scsynth.start(
                #exe = exe,
                #exedir = exedir,
                port = port,
                #inputs = inputs,
                #outputs = outputs,
                #samplerate = samplerate,
                verbose = verbose,
                spew = spew,
                )
    
    if startscsynth : # starts scsynth server process
        global synthon 
        synthon = 1
        server.instance = scsynth.startServer(   
                    exe = exe,
                    exedir = exedir,
                    port = port,
                    inputs = inputs,
                    outputs = outputs,
                    samplerate = samplerate,
                    verbose = verbose,
                    #spew = spew,
                    )

    time.sleep(1) # wait to start up
    
    sndLoader = scsynth.Loader(server) # manages sound files



def quit() :
    if synthon : # it was started
        try :
            server.quit()
            server.ensure_dead()
        except :
            print 'server was not running'


def register(address, fun) :
    """ bind OSC address to function callback
    """
    server.listener.register( address, fun ) 





# sound buffer related utilities.

def loadSnd(filename, wait=False) :
    """ load sound buffer from current sound folder (sc.sndpath) and return buffer's id
        sends back /b_info labeled OSC message. The arguments to /b_info are as
        follows:
        int - buffer number
        int - number of frames
        int - number of channels
    """
    abspath = os.path.join( sndpath, filename )
    return loadSndAbs(abspath, wait)

def unloadSnd(buf_id) :
    """ unload sound buffer from server memory by buffer id
    """
    sndLoader.unload( buf_id, wait=False ) 

def loadSndAbs(path, wait=False) :
    """ same as loadSnd but takes absolute path to snd file
    """
    if os.path.isfile(path) :
        return sndLoader.load( path, wait, b_query=True )
    else :
        print "file %s does NOT exist" % path
        return 0






# classes


class Synth(object) :
    """ wraps supercollider synthdefs
        /s_new args : stringdefname, synth ID (nodeID), addaction, addtargetID, args:[controlindexorname, control value]
        Create a new synth from a synth definition, give it an ID, and add it to the tree of
        nodes. There are four ways to add the node to the tree as determined by the add action
        argument which is defined as follows:
        add actions:
        0 - add the new node to the the head of the group specified by the add target ID.
        1 - add the new node to the the tail of the group specified by the add target ID.
        2 - add the new node just before the node specified by the add target ID.
        3 - add the new node just after the node specified by the add target ID.
        4 - the new node replaces the node specified by the add target ID. The target node is
        freed.
        Controls may be set when creating the synth. The control arguments are the same as
        for the n_set command.
        If you send /s_new with a synth ID of -1, then the server will generate an ID for you.
        The server reserves all negative IDs. Since you don't know what the ID is, you cannot
        talk to this node directly later. So this is useful for nodes that are of finite duration
        and that get the control information they need from arguments and buses or messages
        directed to their group. In addition no notifications are sent when there are changes of
        state for this node, such as /go, /end, /on, /off.
        If you use a node ID of -1 for any other command, such as /n_map, then it refers to
        the most recently created node by /s_new (auto generated ID or not). This is how you
        can map the controls of a node with an auto generated ID. In a multi-client situation,
        the only way you can be sure what node -1 refers to is to put the messages in a bundle.
    """
    loadedSynthdefs = []
    
    def __init__(self, stringdefname='', nodeID=-1, addAction=1, addTargetID=0) : #, args=[] ) :
        
        if nodeID == -1 :
            server.synthpool.check()
            self.nodeID = server.synthpool.get()
            print self.nodeID, '< created node id'
        else :
            self.nodeID = nodeID
            
        self.defpath = os.path.join( synthdefpath, stringdefname+'.scsyndef' ) # the sc synth abs path
        
        if Synth.loadedSynthdefs.count(self.defpath) == 0 : # already loaded?
            if os.path.isfile( self.defpath ) :
                server.sendMsg('/d_load', self.defpath)
                time.sleep(0.5) #wait till loaded
                self.position = len(Synth.loadedSynthdefs)
                Synth.loadedSynthdefs.append(self.defpath)
            else :
                print 'error : synthdef %s file does NOT exist' % self.defpath
            
        server.sendMsg('/s_new', stringdefname, self.nodeID, addAction, addTargetID)
        
        
    def __setattr__(self, item, value):
        """ set a property and send it to the scsynth automatically via OSC
        """
        object.__setattr__(self, item, value)
        server.sendMsg('/n_set', self.nodeID, item, value)
        

##    def __getattr__(self, item, value):
##        """ set a property and send it to the scsynth automatically via OSC
##        """
##        def dothis(msg) :
##            print 'play head at ', msg[3]
##
##        server.listener.register( '/tr', doThis ) # call dothis function when a /tr message arrives
            
    def free(self) :
##        if Synth.loadedSynthdefs.count(self.defpath) : # if there
##            i = Synth.loadedSynthdefs.index(self.defpath) # only me
##            Synth.loadedSynthdefs.pop(i)
        if self.position :
            Synth.loadedSynthdefs.pop(self.position)
        server.sendMsg("/n_free", self.nodeID)

    def run(self, b=1) :
        """ If the run flag set to zero then the node will not be executed.
        If the run flag is set back to one, then it will be executed.
        Using this method to start and stop nodes can cause a click if the node is not silent at
        the time run flag is toggled.
        """
        server.sendMsg('/n_run', self.nodeID, b)










class Group(object) :
    """  Create a new group and add it to the tree of nodes.
                There are four ways to add the group to the tree as determined by the add action argu-
                ment which is defined as follows (the same as for "/s_new"):
                add actions:
                0 - add the new group to the the head of the group specified by the add target ID.
                1 - add the new group to the the tail of the group specified by the add target ID.
                2 - add the new group just before the node specified by the add target ID.
                3 - add the new group just after the node specified by the add target ID.
                4 - the new node replaces the node specified by the add target ID. The target node is
                freed.
                Multiple groups may be created in one command by adding arguments.
    """
    def __init__(self, groupID=-1, addAction=1, addTargetID=0) :
        if groupID == -1 :
            server.synthpool.check()
            self.groupID = server.synthpool.get()
        else :
            self.groupID = groupID
            
        server.sendMsg('/g_new',  self.groupID, addAction, addTargetID)

    def __setattr__(self, item, value):
        object.__setattr__(self, item, value)
        server.sendMsg('/n_set', self.groupID, item, value)
        
    def addToHead(self, node) :
        """ add node to head of group
        """
        server.sendMsg('/g_head', self.groupdID, node.nodeID)

    def addToTail(self, node) :
        """  add node to tail of group
        """
        server.sendMsg('/g_tail',  self.groupdID, node.nodeID)

    def freeAll(self) :
        """ Frees all nodes in the group. A list of groups may be specified.
        """
        server.sendMsg('/g_freeAll', self.groupID ) 

    def deepFree(self) :
        """ traverses all groups below this group and frees all the synths. Sub-groups are not freed.
        """
        server.sendMsg('/g_deepFree ', self.groupID)




