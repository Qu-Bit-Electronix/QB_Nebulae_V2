# Instr File Parser

class InstrParser(object):
    def __init__(self):
        self.configDict = dict() # Container for Config Data
        self.instrString = ""

    def parse(self, filename, path):
        self.clearConfigDict()
        withinConfigChunk = False
        configList = []
        orcString = ""
        with open(path + filename + '.instr', 'r') as myfile:
            for line in myfile:
                if line.startswith("nebconfigbegin"):
                    withinConfigChunk = True
                if withinConfigChunk is True:
                    if line.startswith("nebconfigend"):
                        withinConfigChunk = False
                    elif not line.startswith("nebconfigbegin"):
                        configList.append(line)
                else:
                    orcString += line
            self.configList = configList
            self.instrString = orcString
        self.populateDict()

    def populateDict(self):
        tempList = []
        for line in self.configList:
            strippedLine = line.rstrip()
            tempList = strippedLine.split(",")
            newKey = tempList[0]
            tempList.pop(0)
            self.configDict[newKey] = tempList

    def getInstrString(self):
        return self.instrString

    def configEntry(self, name):
        if self.configDict.has_key(name):
            return self.configDict.get(name)
        else:
            return None
    
    def clearConfigDict(self):
        self.configDict.clear()

    def getConfigDict(self):
        return self.configDict

    def printConfigList(self):
        print "Printing Config Chunk Now"
        for configItem in self.configList:
            print configItem
        print "Done printing config chunk"

    def printInstrString(self):
        print "printing orchestra string"
        print self.instrString
        print "done printing orchestra string"
