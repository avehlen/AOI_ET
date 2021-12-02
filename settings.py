import configparser
import tkinter as tk
import os
from datetime import datetime
import pandas as pd

def saveConfig():
    global config
    cfg = getCfg("aoiSettings")
    config["aoiSettings"]["leftEye"] = cfg.lefteye
    config["aoiSettings"]["rightEye"] = cfg.righteye
    config["aoiSettings"]["nose"] = cfg.nose
    config["aoiSettings"]["mouth"] = cfg.mouth
    config["aoiSettings"]["forehead"] = cfg.forehead
    config["aoiSettings"]["ellipse"] = cfg.ellipse
    
    cfg = getCfg("simulation")
    config["simulation"]["leftEye"] = cfg.lefteye
    config["simulation"]["rightEye"] = cfg.righteye
    config["simulation"]["nose"] = cfg.nose
    config["simulation"]["mouth"] = cfg.mouth
    config["simulation"]["forehead"] = cfg.forehead

    with open('cfg.ini', 'w') as configfile:
        config.write(configfile)

def get(key):
    tmp = ""
    sections = ["generalSettings", "setupSettings", "dataSettings", "simulationSettings", "settings", "aoiSettings", "analyzeSettings"]
    for section in sections:
        try:   
            tmp = config[section][key]
            break
        except KeyError:
            continue
    
    return tmp
            
def getDefaultSettings():
    global config
    config["generalSettings"] = {}
    config["generalSettings"]["title"] = "Title"
    config["generalSettings"]["axis"] = "1"
    config["generalSettings"]["xLim"] = ""
    config["generalSettings"]["yLim"] = ""
    
    config["dataSettings"] = {}
    config["dataSettings"]["alpha"] = "1.0"
    config["dataSettings"]["color"] = "#000000"
    config["dataSettings"]["size"] = "5"
    config["dataSettings"]["delimiter"] = ","
    config["dataSettings"]["xColumn"] = "X"
    config["dataSettings"]["yColumn"] = "Y"
    config["dataSettings"]["originColumn"] = "Original_AOI"
    
    config["settings"] = {}
    config["settings"]["image"] = ""
    config["settings"]["saveImage"] = ""
    config["settings"]["openFace"] = ""
    config["settings"]["gazeData"] = ""
    config["settings"]["targetPoints"] = ""

    config["aoiSettings"] = {}
    config["aoiSettings"]["color"] = "#000000"
    config["aoiSettings"]["colorEllipse"] = "#000000"
    config["aoiSettings"]["colorCenterpoints"] = "#000000"
    config["aoiSettings"]["leftEye"] = "1"
    config["aoiSettings"]["rightEye"] = "1"
    config["aoiSettings"]["nose"] = "1"
    config["aoiSettings"]["mouth"] = "1"
    config["aoiSettings"]["forehead"] = "1"
    config["aoiSettings"]["ellipse"] = "1"
    config["aoiSettings"]["radius"] = "2"
    config["aoiSettings"]["lineWidth"] = "1"
    config["aoiSettings"]["centerSize"] = "5"
    config["aoiSettings"]["distanceAOI"] = "131"

    
    config["simulation"] = {}
    config["simulation"]["leftEye"] = "1"
    config["simulation"]["rightEye"] = "1"
    config["simulation"]["nose"] = "1"
    config["simulation"]["mouth"] = "1"
    config["simulation"]["forehead"] = "1"
    
    config["simulationSettings"] = {}
    config["simulationSettings"]["sampleSize"] = "30"
    config["simulationSettings"]["runsPerSample"] = "10"
    config["simulationSettings"]["accuracy"] = "0.5"
    config["simulationSettings"]["sd"] = "0.25"
    config["simulationSettings"]["precision"] = "0.3"
    config["simulationSettings"]["skew"] = "0.6"
    config["simulationSettings"]["fps"] = "120"
    config["simulationSettings"]["durationSeconds"] = "1"
    config["simulationSettings"]["distribution"] = "Gamma"
    config["simulationSettings"]["distanceSim"] = "131"

    config["analyzeSettings"] = {}
    config["analyzeSettings"]["radiusAnalyze"] = "2.0"
    
        
def setConfig():
    global config
    config.read("cfg.ini")

    try:
        title = config["generalSettings"]["title"]
        axisInfo = config["generalSettings"]["axis"]
        xLim = config["generalSettings"]["xLim"]
        yLim = config["generalSettings"]["yLim"]

        transparency = config["dataSettings"]["alpha"]
        markerSize = config["dataSettings"]["size"]
        color = config["dataSettings"]["color"]
        delimiter = config["dataSettings"]["delimiter"]
        xName = config["dataSettings"]["xColumn"]
        yName = config["dataSettings"]["yColumn"]
        tmp = config["dataSettings"]["originColumn"]
        
        imagePath = config["settings"]["image"]
        dataPath = config["settings"]["gazeData"]
        savePath = config["settings"]["saveImage"]
        ofPath = config["settings"]["openFace"]
        targetPoints = config["settings"]["targetPoints"]

        color = config["aoiSettings"]["color"]
        color_elli = config["aoiSettings"]["colorEllipse"]
        color_centerpoints = config["aoiSettings"]["colorCenterpoints"]
        lineWidth = config["aoiSettings"]["lineWidth"]
        centerSize = config["aoiSettings"]["centerSize"]

        tmp = config["aoiSettings"]["leftEye"]
        tmp = config["aoiSettings"]["rightEye"]
        tmp = config["aoiSettings"]["nose"]
        tmp = config["aoiSettings"]["mouth"]
        tmp = config["aoiSettings"]["forehead"]
        tmp = config["aoiSettings"]["ellipse"]
        tmp = config["aoiSettings"]["radius"]
        tmp = config["aoiSettings"]["distanceAOI"]

        tmp = config["simulation"]["leftEye"]
        tmp = config["simulation"]["rightEye"]
        tmp = config["simulation"]["nose"]
        tmp = config["simulation"]["mouth"]
        tmp = config["simulation"]["forehead"]

        tmp = config["simulationSettings"]["sampleSize"]
        tmp = config["simulationSettings"]["runsPerSample"]
        tmp = config["simulationSettings"]["accuracy"]
        tmp = config["simulationSettings"]["sd"]
        tmp = config["simulationSettings"]["precision"]
        tmp = config["simulationSettings"]["skew"]
        tmp = config["simulationSettings"]["fps"]
        tmp = config["simulationSettings"]["durationSeconds"]
        tmp = config["simulationSettings"]["distribution"]
        tmp = config["simulationSettings"]["distanceSim"]

        tmp = config["analyzeSettings"]["radiusAnalyze"]

    
    except KeyError:
        getDefaultSettings()
        
    
def setCheckbox(section, key, chk):
    cfg = getCfg(section)

    if cfg.getKey(key) == "1":
        chk.select()
    else:
        chk.deselect()


def check(section, key):
    cfg = getCfg(section)
    
    if cfg.getKey(key) == "1":
        cfg.setKey(key, "0")
    else:
        cfg.setKey(key, "1")


class vCfg():
    def __init__(self, section):
        self.lefteye = config[section]["leftEye"]
        self.righteye = config[section]["rightEye"]
        self.nose = config[section]["nose"]
        self.mouth = config[section]["mouth"]
        self.forehead = config[section]["forehead"]
        
        if section == "aoiSettings":
            self.ellipse = config[section]["ellipse"]
    
    def getKey(self, key):
        if key.lower() == "lefteye":
            return self.lefteye
        if key.lower() == "righteye":
            return self.righteye
        if key.lower() == "nose":
            return self.nose
        if key.lower() == "mouth":
            return self.mouth
        if key.lower() == "forehead":
            return self.forehead
        if key.lower() == "ellipse":
            return self.ellipse
        
    def setKey(self, key, val):
        if key.lower() == "lefteye":
            self.lefteye = val
        if key.lower() == "righteye":
            self.righteye = val
        if key.lower() == "nose":
            self.nose = val
        if key.lower() == "mouth":
            self.mouth = val
        if key.lower() == "forehead":
            self.forehead = val
        if key.lower() == "ellipse":
            self.ellipse = val
        
        
def getCfg(section):
    global simCfg
    global aoiCfg
    if section == "aoiSettings":
        return aoiCfg
    elif section == "simulation":
        return simCfg


def saveConfigFile():
    global outputDir
    global config
    today = datetime.today()
    date = today.strftime("%d.%m.%Y_%H_%M_%S")

    f = open(outputDir + '\\logfile_' + date + '.txt', 'w+')

    with open('cfg.ini', 'r') as configfile:
        f.write(configfile.read())

def loadConfigFile():
    global outputDir
    global config

    configPath = tk.filedialog.askopenfilename(initialdir=outputDir, title="Open settings file",
                                            filetypes=(("Text file", "*.ini;*.txt;"), ("All files", "*.*")))
    

    if configPath == "":
        return
    
    config.read(configPath)


def getRadiusAOI():
    radiStr = config["aoiSettings"]["radius"]
    radi = str.split(radiStr, ";")

    for i in range(0, len(radi)):
        radi[i] = float(radi[i])
    
    return radi


def setSaveDir():
    global outputDir
    global saveDir
    
    today = datetime.today()
    timeStamp = today.strftime("%d.%m.%Y_%H_%M_%S")
    saveDir = outputDir + "\\" + timeStamp
    os.makedirs(saveDir, exist_ok=True)
    
def saveSession(targetPoints):
    global config
    global saveDir
    
    """ set save directory """
    setSaveDir()
    
    """ save config file """
    saveConfig()
    with open(saveDir + '\\cfg.ini', 'w') as configfile:
        config.write(configfile)
    
    """ save target points """
    df = pd.DataFrame(data=targetPoints, columns=["X", "Y"])
    df.to_csv(saveDir + '\\targetpoints.csv', index= False)


global outputDir
global saveDir
global config
global simCfg
global aoiCfg

''' Create output directory if it doesn't exist '''
timeStamp = "0"
dir_path = os.path.dirname(os.path.realpath(__file__))
outputDir = dir_path + "\\output"
os.makedirs(outputDir, exist_ok=True)

''' Initialize configuration '''
config = configparser.ConfigParser()
setConfig()

simCfg = vCfg("simulation")
aoiCfg = vCfg("aoiSettings")
