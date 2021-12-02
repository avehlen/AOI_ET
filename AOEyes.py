# -*- coding: utf-8 -*-
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import matplotlib.patches
import numpy as np
import math
import pandas as pd
from tkinter import colorchooser
import tkinter as tk
from tkinter.filedialog import askopenfilename
import voronoiLR
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
import os
import settings
import simulateAccPrec_ET
import voronoi_functions as vf
import analyzeAccPrec_ET
import sys
from matplotlib import backend_bases
import colorsys


### MISC ###
''' confert hex color to rbg '''
def hex_to_rgb(hex):
    return tuple(int(hex[i:i + 2], 16) for i in (1, 3, 5))

### FILE SELECTION ###
def selectFile():
    global ax
    global canvas
    
    img = selectImageFile()
    try:
        ax.cla()
        ax.imshow(img)
        canvas.draw()
        settings.saveConfig()
    except:
        return None
    

def selectDataFile():
    data_dir = os.path.dirname(settings.config["settings"]["gazeData"])
    file = tk.filedialog.askopenfilename(initialdir=data_dir, title="Open data file",
                                         filetypes=(("Data files", "*.csv;*.txt;"), ("All files", "*.*")))
    if file == "":
        return
    settings.config["settings"]["gazeData"] = file
    settings.saveConfig()


def selectPathExe():
    ''' Get path to openface facial landmark detection for images '''
    data_dir = os.path.dirname(settings.config["settings"]["openFace"])
    file = tk.filedialog.askopenfilename(initialdir=data_dir, title="Open OpenFace executable",
                                         filetypes=(("FaceLandmarkImg", "*.exe"), ("all files", "*.*")))
    if file == "":
        return ""

    ''' Save path '''
    settings.config["settings"]["openFace"] = file
    settings.saveConfig()

    return file


### CHECK FOR CORRECT FILES ###
def getImageFile(path):
    try:
        img = mpimg.imread(settings.config["settings"]["image"])
    except:
        img = selectImageFile()

    return img

def getDataFile():
    try:
        data = settings.config["settings"]["gazeData"]
        gazeDataFile = pd.read_csv(data, delimiter=settings.config["dataSettings"]["delimiter"])
    except:
        data = selectDataFile()

    return data

def getTargetFile():
    try:
        target = settings.get("targetPoints")
        landmarksFile = pd.read_csv(target, delimiter = ',')
        lmArr = pd.DataFrame(landmarksFile).to_numpy()
    except:
        target = selectTargetPoints()

    return target

def selectImageFile():
    data_dir = os.path.dirname(settings.config["settings"]["image"])
    file = tk.filedialog.askopenfilename(initialdir=data_dir, title="Open image file",
                                         filetypes=(("Image files", "*.jpg;*.png;"), ("All files", "*.*")))
    if file == "":
        return None

    try:
        img = mpimg.imread(file)
        settings.config["settings"]["image"] = file
        settings.saveConfig()
        return img
    except:
        return None

def selectTargetPoints():
    target_dir = os.path.dirname(settings.config["settings"]["targetPoints"])
    target = tk.filedialog.askopenfilename(initialdir=target_dir, title="Open target points file",
                                         filetypes=(("Data files", "*.csv;*.txt;"), ("All files", "*.*")))
    if target == "":
        return
    settings.config["settings"]["targetPoints"] = target
    settings.saveConfig()
    
    return target

def selectTargetName():
    nameOrigin = settings.config["dataSettings"]["originColumn"]

    if nameOrigin == "":
        InputWin = tk.Toplevel(root)
        InputWin.title("Required input")
        InputWin.geometry("450x175")  # width x height

        Names = ["originColumn"]
        targetEntry = createEntry(InputWin, "Name of targeted AOI column", 1, 1, "", 10, 15, bg="#f0f0f0",
                                  sticky=tk.W)

        entryList = [targetEntry]
        createButton(InputWin, 'OK', lambda: writeToConfig(InputWin, "dataSettings", Names,
                                                           entryList, plotStackedBar),
                     10, 2, 0, 0, 10, bg="#dbdbdb")

        createButton(InputWin, 'Cancel',
                     lambda: InputWin.destroy(),
                     10, 2, 1, 0, 10, bg="#dbdbdb")
    else:
        plotStackedBar()



### SAVE ###
def saveAsFile():
    myFormats = [('Portable Network Graphics', '*.png'),
                 ('Joint Photographic Experts Group', '*.jpg'),
                 ('Portable Document Format', '*.pdf'),
                 ('Tagged Image File Format', '*.tiff')]
    data_dir = os.path.dirname(settings.config["settings"]["saveImage"])
    file = tk.filedialog.asksaveasfile(initialdir=data_dir, title="Save as", filetypes=myFormats,
                                       defaultextension=".png")
    if file is not None:
        plt.savefig(file.name)
        settings.config["settings"]["saveImage"] = file.name
        settings.saveConfig()

def saveFile():
    filename = settings.config["settings"]["saveImage"]
    if filename is not None:
        plt.savefig(filename)
    else:
        saveAsFile()
        
def saveTargetPoints():
    global originPoints
    settings.saveTargetPoints(originPoints)

'''
def writeToConfig(window, section, keys, values, function = settings.saveConfig()):
    for i in range(0, len(values)):
        entry = values[i].get()
        if keys[i] == "distance" and section == "aoiSettings":
            settings.config["generalSettings"][keys[i]] = entry
        else:
            settings.config[section][keys[i]] = entry
    settings.saveConfig()
    if function is not None:
        function()
    window.destroy()
'''

def writeToConfig(window, section, keys, values, function = settings.saveConfig()):
    for i in range(0, len(values)):
        entry = values[i].get()
        settings.config[section][keys[i]] = entry
    settings.saveConfig()
    if function is not None:
        function()
    window.destroy()


def writeChoiceToConfig(*args):
    global choice
    distribution = choice.get()
    settings.config["simulationSettings"]["distribution"] = distribution
    settings.saveConfig()

def saveAndDestroy(win):
    settings.saveConfig()
    win.destroy()


### TOOLTIPS ###
class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        ''' display text in tooltip window '''
        self.text = text
        if self.tipwindow or not self.text:
            return
        ''' create widget '''
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


### CANVAS ELEMENTS ###
def tellme(s):
    plt.title(s, fontsize=10)
    plt.suptitle("", fontsize=12)
    canvas.draw()

def createButton(window, text, command, width, row, column, padx, pady, bg = "#f0f0f0"):
    buttonName = tk.Button(window, text=text, command=command, width= width, bg = bg)
    buttonName.grid(row= row, column= column, padx= padx, pady=pady)
    return buttonName


def createEntry(window, labelText, row, column, default, padx, pady, bg = "#f0f0f0", sticky = tk.W):
    lableName = tk.Label(master = window, text= labelText, bg = bg).grid(row= row, sticky = sticky)
    entryName = tk.Entry(master = window, bg = bg)
    entryName.insert(0, default)
    entryName.grid(row= row, column= column, padx = padx, pady = pady)
    return entryName

### OPTION WINDOWS ###
''' Setting GUI: General'''
def settingsGUIgeneral():
    generalSettingNames = ["title", "axis", "xLim", "yLim"]

    settingWin = tk.Toplevel(root)
    settingWin.title("Settings: General")
    settingWin.geometry("450x275") #width x height

    tk.Label(settingWin, text = "Settings: General", font='Arial 12 bold').grid(row = 0, pady = 10, sticky = tk.W)
    titleEntry = createEntry(settingWin, "Title", 2, 1, settings.get("title"), 0, 10, sticky = tk.W)

    CreateToolTip(titleEntry, text='Choose plot title...')
    axisEntry = createEntry(settingWin, "Axis [0 = off, 1 = on]", 3, 1, settings.get("axis"), 0, 10,
                            sticky = tk.W)
    CreateToolTip(axisEntry, text='Show axis?')
    xLimEntry = createEntry(settingWin, "Limits X axis [xStart, xStop]", 4, 1, settings.get("xLim"), 0, 10,
                            sticky = tk.W)
    CreateToolTip(xLimEntry, text='Specify X axis limit...')
    yLimEntry = createEntry(settingWin, "Limits Y axis [yStart, yStop]", 5, 1, settings.get("yLim"), 0, 10,
                            sticky = tk.W)
    CreateToolTip(yLimEntry, text='Specify Y axis limit...')
    generalEntryList = [titleEntry, axisEntry, xLimEntry, yLimEntry]

    createButton(settingWin, 'OK', lambda:writeToConfig(settingWin, "generalSettings",
                                                                  generalSettingNames, generalEntryList),
                           10, 6, 0, 0, 10, bg = "#dbdbdb")
    createButton(settingWin, 'Cancel',
                 lambda: settingWin.destroy(),
                 10, 6, 1, 0, 10, bg="#dbdbdb")

''' Setting GUI: Manual target points'''
def settingsGUIsimulationManual():
    global root
    simulationSettingsNames = ["distanceSim", "sampleSize", "runsPerSample", "fps", "durationSeconds", "accuracy", "precision", "sd", "skew"]

    settingWin = tk.Toplevel(root)
    settingWin.title("Settings: Manual target points")
    settingWin.geometry("450x535")  # width x height
    tk.Label(settingWin, text="Settings: Manual target points", font='Arial 12 bold').grid(row=1, pady=10, sticky=tk.W)

    distanceEntry = createEntry(settingWin, 'Viewing distance [cm]', 2, 1, settings.get("distanceSim"), 0, 10,
                                sticky=tk.W)
    CreateToolTip(distanceEntry, text='Specify viewing distance...')

    fpsEntry = createEntry(settingWin, 'Frequency [fps]', 3, 1, settings.get("fps"), 0, 10, sticky=tk.W)
    CreateToolTip(fpsEntry, text='Choose data frequency...')

    sampleSizeEntry = createEntry(settingWin, 'Sample size', 4, 1, settings.get("sampleSize"), 0, 10,
                                  sticky=tk.W)
    CreateToolTip(sampleSizeEntry, text='Choose number of virtual participants...')

    trialEntry = createEntry(settingWin, 'Runs per sample', 5, 1, settings.get("runsPerSample"), 0, 10,
                             sticky=tk.W)
    CreateToolTip(trialEntry, text='Choose number of runs per virtual participants...')

    durationEntry = createEntry(settingWin, 'Trial length [seconds]', 6, 1, settings.get("durationSeconds"), 0, 10,
                                sticky=tk.W)
    CreateToolTip(durationEntry, text='Choose length of run...')

    accuracyEntry = createEntry(settingWin, 'Acurracy [°]', 7, 1, settings.get("accuracy"), 0, 10, sticky=tk.W)
    CreateToolTip(accuracyEntry, text='Choose Accuracy...')

    precisionEntry = createEntry(settingWin, 'Precision [°]', 8, 1, settings.get("precision"), 0, 10, sticky=tk.W)
    CreateToolTip(precisionEntry, text='Choose Precision [SD]...')

    tk.Label(settingWin, text="Distribution:").grid(row=9, pady=10, sticky=tk.W)

    OptionList = ["Gamma", "Normal", "Uniform"]
    choice = tk.StringVar(settingWin)
    choice.set(OptionList[0])
    tk.OptionMenu(settingWin, choice, *OptionList).grid(row=10, sticky=tk.W) # padx=50,
    choice.trace("w", writeChoiceToConfig)

    sdEntry = createEntry(settingWin, 'Standard deviation', 11, 1, settings.get("sd"), 0, 10, sticky=tk.W)
    CreateToolTip(sdEntry, text='Choose standard deviation of data distribution...')

    skewEntry = createEntry(settingWin, 'Skew', 12, 1, settings.get("skew"), 0, 10, sticky=tk.W)
    CreateToolTip(skewEntry, text='Choose skrewness of data distribution...')

    simulationEntryList = [distanceEntry, sampleSizeEntry, trialEntry, fpsEntry, durationEntry, accuracyEntry, precisionEntry, sdEntry, skewEntry]

    createButton(settingWin, 'Start', lambda:writeToConfig(settingWin, "simulationSettings", simulationSettingsNames,
                                                                     simulationEntryList, manualTargetPoints(completeManualTargetPoints)),
                           10, 13, 0, 0, 10, bg = "#dbdbdb")

    createButton(settingWin, 'Cancel',
                 lambda:settingWin.destroy(),
                 10, 13, 1, 0, 10, bg="#dbdbdb")

''' Setting GUI: OF target points'''
def settingsGUIsimulation():
    global root
    simulationSettingsNames = ["distanceSim", "fps", "sampleSize", "runsPerSample", "durationSeconds", "accuracy",
                               "precision", "sd", "skew"]

    settingWin = tk.Toplevel(root)
    settingWin.title("Settings: OpenFace target points")
    settingWin.geometry("450x750")  # width x height
    tk.Label(settingWin, text="Settings: OpenFace target points", font='Arial 12 bold').grid(row=1, pady=10, sticky=tk.W)

    file = settings.config["settings"]["openFace"]
    v = tk.StringVar(root, value= file)
    pathEntry = tk.Entry(settingWin, textvariable=v, width = "40").grid(row=2, sticky=tk.W)
    ofExeButton = createButton(settingWin, 'Select OpenFace\nexecutable', selectPathExe,
                         20, 2, 1, 0, 10, bg="#dbdbdb")
    CreateToolTip(ofExeButton, text='Specify path to OpenFace executable...')

    distanceEntry = createEntry(settingWin, 'Viewing distance [cm]', 3, 1, settings.get("distanceSim"), 0, 10,
                                sticky=tk.W)
    CreateToolTip(distanceEntry, text='Specify viewing distance...')

    fpsEntry = createEntry(settingWin, 'Frequency [fps]', 4, 1, settings.get("fps"), 0, 10, sticky=tk.W)
    CreateToolTip(fpsEntry, text='Choose data frequency...')

    sampleSizeEntry = createEntry(settingWin, 'Sample size', 5, 1, settings.get("sampleSize"), 0, 10,
                                  sticky=tk.W)
    CreateToolTip(sampleSizeEntry, text='Choose number of virtual participants...')

    trialEntry = createEntry(settingWin, 'Runs per sample', 6, 1, settings.get("runsPerSample"), 0, 10,
                             sticky=tk.W)
    CreateToolTip(trialEntry, text='Choose number of runs per virtual participants...')

    durationEntry = createEntry(settingWin, 'Trial length [sec]', 7, 1, settings.get("durationSeconds"), 0, 10,
                                sticky=tk.W)
    CreateToolTip(durationEntry, text='Choose length of run...')

    accuracyEntry = createEntry(settingWin, 'Acurracy [°]', 8, 1, settings.get("accuracy"), 0, 10, sticky=tk.W)
    CreateToolTip(accuracyEntry, text='Choose Accuracy...')

    precisionEntry = createEntry(settingWin, 'Precision [°]', 9, 1, settings.get("precision"), 0, 10, sticky=tk.W)
    CreateToolTip(precisionEntry, text='Choose Precision [SD]...')

    tk.Label(settingWin, text="Distribution:").grid(row=10, pady=10, sticky=tk.W)
    OptionList = ["Gamma", "Normal", "Uniform"]
    choice = tk.StringVar(settingWin)
    choice.set(OptionList[0])
    tk.OptionMenu(settingWin, choice, *OptionList).grid(row=11, padx = 50, sticky=tk.W)
    choice.trace("w", writeChoiceToConfig)

    sdEntry = createEntry(settingWin, 'Standard deviation', 12, 1, settings.get("sd"), 0, 10, sticky=tk.W)
    CreateToolTip(sdEntry, text='Choose standard deviation of data distribution...')

    skewEntry = createEntry(settingWin, 'Skew', 13, 1, settings.get("skew"), 0, 10, sticky=tk.W)
    CreateToolTip(skewEntry, text='Choose skrewness of data distribution...')


    simulationEntryList = [distanceEntry, fpsEntry, sampleSizeEntry, trialEntry, durationEntry, accuracyEntry, precisionEntry, sdEntry, skewEntry]

    tk.Frame(settingWin, bg=['#b8b1ae'], width=450, height=150).grid(row=14, column=0, columnspan=2, rowspan=4)
    tk.Label(settingWin, text="Target points:", font="Arial 12 bold", bg=['#b8b1ae']).grid(row=14, pady=0, sticky=tk.W)

    lefteye = tk.Checkbutton(settingWin, text="LeftEye", anchor="w",
                             command=lambda: settings.check("simulation",
                                                            "leftEye"), bg=['#b8b1ae'])
    CreateToolTip(lefteye, text='Target point on left eye?')

    lefteye.grid(row=15, column=0, pady=0, sticky=tk.W)
    settings.setCheckbox("simulation", "leftEye", lefteye)

    righteye = tk.Checkbutton(settingWin, text="RightEye", command=lambda: settings.check("simulation",
                                                                                                  "rightEye"), bg=['#b8b1ae'])
    CreateToolTip(righteye, text='Target point on right eye?')
    righteye.grid(row=15, column=1, pady=0, sticky=tk.W)
    settings.setCheckbox("simulation", "rightEye", righteye)

    nose = tk.Checkbutton(settingWin, text="Nose", anchor="w", command=lambda: settings.check("simulation",
                                                                                                      "nose"), bg=['#b8b1ae'])
    CreateToolTip(nose, text='Target point on nose?')
    nose.grid(row=16, column=0, pady=0, sticky=tk.W)
    settings.setCheckbox("simulation", "nose", nose)

    mouth = tk.Checkbutton(settingWin, text="Mouth", command=lambda: settings.check("simulation", "mouth"), bg=['#b8b1ae'])
    CreateToolTip(mouth, text='Target point on mouth?')
    mouth.grid(row=16, column=1, pady=0, sticky=tk.W)
    settings.setCheckbox("simulation", "mouth", mouth)

    forehead = tk.Checkbutton(settingWin, text="Forehead", command=lambda: settings.check("simulation",
                                                                                                  "forehead"), bg=['#b8b1ae'])
    CreateToolTip(forehead, text='Target point on forehead?')
    forehead.grid(row=17, column=0, pady=0, sticky=tk.W)
    settings.setCheckbox("simulation", "forehead", forehead)


    createButton(settingWin, 'Start', lambda:writeToConfig(settingWin, "simulationSettings", simulationSettingsNames,
                                                                     simulationEntryList, simulateAccPrec_ET.startAccPrecOF),
                           10, 18, 0, 0, 10, bg = "#dbdbdb")

    createButton(settingWin, 'Cancel',
                 lambda:settingWin.destroy(),
                 10, 18, 1, 0, 10, bg="#dbdbdb")

'''Setting GUI: Load target points'''
def settingsGUIsimulationTarget():
    global root
    global choice
    simulationSettingsNames = ["distanceSim", "fps", "sampleSize", "runsPerSample",  "durationSeconds", "accuracy",
                               "precision", "sd", "skew"]

    settingWin = tk.Toplevel(root)
    settingWin.title("Settings: Load target points")
    settingWin.geometry("450x600")  # width x height
    tk.Label(settingWin, text="Settings: Load target points", font='Arial 12 bold').grid(row=0, pady=10, sticky=tk.W)

    file = settings.config["settings"]["targetPoints"]
    v = tk.StringVar(root, value=file)
    tk.Entry(settingWin, textvariable=v, width="40").grid(row=1, sticky=tk.W)
    ofExeButton = createButton(settingWin, 'Select target point file', selectTargetPoints,
                               20, 1, 1, 5, 20, bg="#dbdbdb")
    CreateToolTip(ofExeButton, text='Specify path to target points file...')

    distanceEntry = createEntry(settingWin, 'Viewing distance [cm]', 2, 1, settings.get("distanceSim"), 0, 10,
                                sticky=tk.W)
    CreateToolTip(distanceEntry, text='Specify viewing distance...')

    fpsEntry = createEntry(settingWin, 'Frequency [fps]', 3, 1, settings.get("fps"), 0, 10, sticky=tk.W)
    CreateToolTip(fpsEntry, text='Choose data frequency...')

    sampleSizeEntry = createEntry(settingWin, 'Sample size', 4, 1, settings.get("sampleSize"), 0, 10,
                                  sticky=tk.W)
    CreateToolTip(sampleSizeEntry, text='Choose number of virtual participants...')

    trialEntry = createEntry(settingWin, 'Runs per sample', 5, 1, settings.get("runsPerSample"), 0, 10,
                             sticky=tk.W)
    CreateToolTip(trialEntry, text='Choose number of runs per virtual participants...')

    durationEntry = createEntry(settingWin, 'Trial length [sec]', 6, 1, settings.get("durationSeconds"), 0, 10,
                                sticky=tk.W)
    CreateToolTip(durationEntry, text='Choose length of run...')

    accuracyEntry = createEntry(settingWin, 'Acurracy [°]', 7, 1, settings.get("accuracy"), 0, 10, sticky=tk.W)
    CreateToolTip(accuracyEntry, text='Choose accuracy / mean of data distribution...')

    precisionEntry = createEntry(settingWin, 'Precision [°]', 8, 1, settings.get("precision"), 0, 10, sticky=tk.W)
    CreateToolTip(precisionEntry, text='Choose Precision [SD]...')

    tk.Label(settingWin, text="Distribution:").grid(row=9, pady=10, sticky=tk.W)
    OptionList = ["Gamma", "Normal", "Uniform"]
    choice = tk.StringVar(settingWin)
    choice.set(OptionList[0])
    tk.OptionMenu(settingWin, choice, *OptionList).grid(row=10, padx = 50, sticky=tk.W)
    choice.trace("w", writeChoiceToConfig)

    sdEntry = createEntry(settingWin, 'Standard deviation', 11, 1, settings.get("sd"), 0, 10, sticky=tk.W)
    CreateToolTip(sdEntry, text='Choose standard deviation of data distribution...')

    skewEntry = createEntry(settingWin, 'Skew', 12, 1, settings.get("skew"), 0, 10, sticky=tk.W)
    CreateToolTip(skewEntry, text='Choose skrewness of data distribution...')

    simulationEntryList = [distanceEntry, fpsEntry, sampleSizeEntry, trialEntry, durationEntry, accuracyEntry, precisionEntry, sdEntry, skewEntry]

    createButton(settingWin, 'Start', lambda: writeToConfig(settingWin, "simulationSettings", simulationSettingsNames,
                                                            simulationEntryList,
                                                            simulateAccPrec_ET.startAccPrecTargets),
                 10, 13, 0, 0, 10, bg="#dbdbdb")

    createButton(settingWin, 'Cancel',
                 lambda: settingWin.destroy(),
                 10, 13, 1, 0, 10, bg="#dbdbdb")

'''Setting GUI: Manual AOIs'''
def settingsGUImanualAOI():
    global root

    aoiSettingNames = ["distanceAOI", "radius", "lineWidth", "centerSize"]

    settingWin = tk.Toplevel(root)
    settingWin.title("Settings: Manual center points")
    settingWin.geometry("450x425")  # width x height

    tk.Label(settingWin, text="Settings: Manual center points", font="Arial 12 bold").grid(row=1, pady=10, sticky=tk.W)

    distanceEntry = createEntry(settingWin, 'Viewing distance [cm]', 2, 1, settings.get("distanceAOI"), 10, 15,
                                sticky=tk.W)
    CreateToolTip(distanceEntry, text='Specify viewing distance...')

    radiusEntry = createEntry(settingWin, u"AOI radius [°]", 3, 1, settings.get("radius"), 10, 15, sticky=tk.W)
    CreateToolTip(radiusEntry, text='Specify AOI size...')

    colorBoundaryButton = createButton(settingWin, 'Color AOI \n boundaries', lambda: chooseColor(ele=1),
                                       20, 4, 0, 10, 15, bg="#dbdbdb")
    CreateToolTip(colorBoundaryButton, text='Choose color of AOI boundaries...')

    lineWidthEntry = createEntry(settingWin, "Linewidth [px]", 5, 1, settings.get("lineWidth"), 10, 15,
                                 sticky=tk.W)
    CreateToolTip(lineWidthEntry, text='Choose linewidth of AOI boundaries...')

    colorButton = createButton(settingWin, 'Color AOI \n center points', lambda: chooseColor(ele=3),
                               20, 6, 0, 10, 5, bg="#dbdbdb")
    CreateToolTip(colorButton, text='Choose color of AOI center points...')

    centerSizeEntry = createEntry(settingWin, "Center points size [px]", 7, 1, settings.get("centerSize"), 10, 15,
                                 sticky=tk.W)
    CreateToolTip(centerSizeEntry, text='Choose size of AOI center points...')

    aoiEntryList = [distanceEntry, radiusEntry, lineWidthEntry, centerSizeEntry]

    createButton(settingWin, 'Start', lambda: writeToConfig(settingWin, "aoiSettings",
                                                                    aoiSettingNames, aoiEntryList, manualTargetPoints(completeManualAOIs)), 10, 8, 0,
                 0, 10,
                 bg="#dbdbdb")
    createButton(settingWin, 'Cancel',
                 lambda: settingWin.destroy(),
                 10, 8, 1, 0, 10, bg="#dbdbdb")

''' Setting GUI: OpenFace AOIs '''
def settingsGUIopenface():
    global root

    aoiSettingNames = ["distanceAOI", "radius", "lineWidth", "centerSize"]

    settingWin = tk.Toplevel(root)
    settingWin.title("Settings: OpenFace center points")
    settingWin.geometry("450x775") #width x height

    tk.Label(settingWin, text="Settings: OpenFace center points", font="Arial 12 bold").grid(row=1, pady=10,
                                                                                             sticky=tk.W)

    distanceEntry = createEntry(settingWin, 'Viewing distance [cm]', 2, 1, settings.get("distanceAOI"), 10, 15,
                                sticky=tk.W)
    CreateToolTip(distanceEntry, text='Specify viewing distance...')

    radiusEntry = createEntry(settingWin, u"AOI radius [°]", 3, 1, settings.get("radius"), 10, 15, sticky=tk.W)
    CreateToolTip(radiusEntry, text='Specify AOI size...')

    colorBoundaryButton = createButton(settingWin, 'Color AOI \n boundaries', lambda:chooseColor(ele = 1),
                         20, 4, 0, 10, 15, bg = "#dbdbdb")
    CreateToolTip(colorBoundaryButton, text='Choose color of AOI boundaries...')

    lineWidthEntry = createEntry(settingWin, "Linewidth [px]", 5, 1, settings.get("lineWidth"), 10, 15, sticky = tk.W)
    CreateToolTip(lineWidthEntry, text='Choose linewidth of AOI boundaries...')

    colorButton = createButton(settingWin, 'Color AOI \n center points', lambda:chooseColor(ele= 3),
                                      20, 6, 0, 10, 5, bg = "#dbdbdb")
    CreateToolTip(colorButton, text='Choose color of AOI center points...')

    centerSizeEntry = createEntry(settingWin, "Center points size [px]", 7, 1, settings.get("centerSize"), 10, 15,
                                  sticky=tk.W)
    CreateToolTip(centerSizeEntry, text='Choose size of AOI center points...')

    tk.Label(settingWin, text="OpenFace settings", font="Arial 12 bold").grid(row=8, pady=10, sticky=tk.W)

    file = settings.config["settings"]["openFace"]
    v = tk.StringVar(root, value= file)
    tk.Entry(settingWin, textvariable=v, width = "40").grid(row=9, sticky=tk.W)
    ofExeButton = createButton(settingWin, 'Select OpenFace\nexecutable', selectPathExe,
                         20, 9, 1, 5, 20, bg="#dbdbdb")

    CreateToolTip(ofExeButton, text='Specify path to OpenFace executable...')

    ellipseColorButton = createButton(settingWin, 'Color Ellipse', lambda:chooseColor(ele = 2),
                              20, 10, 0, 10, 20, bg = "#dbdbdb")

    CreateToolTip(ellipseColorButton, text='Choose color of face ellipse boundary...')

    aoiEntryList = [distanceEntry, radiusEntry, lineWidthEntry, centerSizeEntry]

    tk.Frame(settingWin, bg=['#b8b1ae'], width = 450, height = 150).grid(row = 11, column = 0,columnspan = 2,
                                                                         rowspan = 4)

    tk.Label(settingWin, text="AOIs:", font="Arial 12 bold", bg=['#b8b1ae']).grid(row=11, pady=0, sticky=tk.W)

    lefteye = tk.Checkbutton(settingWin, text="LeftEye", anchor="w",
                             command=lambda: settings.check("aoiSettings","leftEye"), bg=['#b8b1ae'])
    CreateToolTip(lefteye, text='Center point on left eye?')

    lefteye.grid(row=12, column=0, pady=0, sticky = tk.W)
    settings.setCheckbox("aoiSettings", "leftEye", lefteye)

    righteye = tk.Checkbutton(settingWin, text="RightEye", command=lambda: settings.check("aoiSettings",
                                                                                          "rightEye"), bg=['#b8b1ae'])
    CreateToolTip(righteye, text='Center point on right eye?')
    righteye.grid(row=12, column=1, pady=0, sticky = tk.W)
    settings.setCheckbox("aoiSettings", "rightEye", righteye)

    nose = tk.Checkbutton(settingWin, text="Nose", anchor="w", command=lambda: settings.check("aoiSettings",
                                                                                              "nose"),bg=['#b8b1ae'])
    CreateToolTip(nose, text='Center point on nose?')
    nose.grid(row=13, column=0, pady=0, sticky = tk.W)
    settings.setCheckbox("aoiSettings", "nose", nose)

    mouth = tk.Checkbutton(settingWin, text="Mouth", command=lambda: settings.check("aoiSettings",
                                                                                    "mouth"), bg=['#b8b1ae'])
    CreateToolTip(mouth, text='Center point on mouth?')
    mouth.grid(row=13, column=1, pady=0, sticky = tk.W)
    settings.setCheckbox("aoiSettings", "mouth", mouth)

    ellipse = tk.Checkbutton(settingWin, text="Ellipse", command=lambda: settings.check("aoiSettings",
                                                                                        "ellipse"), bg=['#b8b1ae'])
    CreateToolTip(ellipse, text='Face ellipse?')
    ellipse.grid(row=14, pady=0, sticky = tk.W)
    settings.setCheckbox("aoiSettings", "ellipse", ellipse)

    createButton(settingWin, 'Start', lambda:writeToConfig(settingWin, "aoiSettings",
                                                                          aoiSettingNames, aoiEntryList, ofAOIs),
                 10, 15, 0, 0, 10, bg = "#dbdbdb")
    createButton(settingWin, 'Cancel',
                 lambda: settingWin.destroy(),
                 10, 15, 1, 0, 10, bg="#dbdbdb")

''' Setting GUI: Load center points '''
def settingsGUItargetAOI():
    global root

    aoiSettingNames = ["distanceAOI", "radius", "lineWidth", "centerSize"]

    settingWin = tk.Toplevel(root)
    settingWin.title("Settings: Load target points  ")
    settingWin.geometry("450x490")  # width x height

    tk.Label(settingWin, text="Settings: Load target points", font="Arial 12 bold").grid(row=1, pady=10, sticky=tk.W)
    
    file = settings.get("targetPoints")
    v = tk.StringVar(root, value= file)
    tk.Entry(settingWin, textvariable=v, width = "40").grid(row=2, sticky=tk.W)
    ofExeButton = createButton(settingWin, 'Select target point file', selectTargetPoints,
                         20, 2, 1, 5, 20, bg="#dbdbdb")
    CreateToolTip(ofExeButton, text='Specify path to target points file...')

    distanceEntry = createEntry(settingWin, 'Viewing distance [cm]', 3, 1, settings.get("distanceAOI"), 10, 15,
                                sticky=tk.W)
    CreateToolTip(distanceEntry, text='Specify viewing distance...')

    radiusEntry = createEntry(settingWin, u"AOI radius [°]", 4, 1, settings.get("radius"), 10, 15, sticky=tk.W)
    CreateToolTip(radiusEntry, text='Specify AOI size...')

    colorBoundaryButton = createButton(settingWin, 'Color AOI \n boundaries', lambda: chooseColor(ele=1),
                                       20, 5, 0, 10, 15, bg="#dbdbdb")
    CreateToolTip(colorBoundaryButton, text='Choose color of AOI boundaries...')

    lineWidthEntry = createEntry(settingWin, "Linewidth [px]", 6, 1, settings.get("lineWidth"), 10, 15,
                                 sticky=tk.W)
    CreateToolTip(lineWidthEntry, text='Choose linewidth of AOI boundaries...')

    colorButton = createButton(settingWin, 'Color AOI \n center points', lambda: chooseColor(ele=3),
                               20, 7, 0, 10, 5, bg="#dbdbdb")
    CreateToolTip(colorButton, text='Choose color of AOI center points...')

    centerSizeEntry = createEntry(settingWin, "Center points size [px]", 8, 1, settings.get("centerSize"), 10, 15,
                                  sticky=tk.W)
    CreateToolTip(centerSizeEntry, text='Choose size of AOI center points...')

    aoiEntryList = [distanceEntry, radiusEntry, lineWidthEntry, centerSizeEntry]

    createButton(settingWin, 'Start', lambda: writeToConfig(settingWin, "aoiSettings",
                                                                    aoiSettingNames, aoiEntryList, targetAOIs), 10, 9, 0,
                 0, 10,
                 bg="#dbdbdb")
    createButton(settingWin, 'Cancel',
                 lambda: settingWin.destroy(),
                 10, 9, 1, 0, 10, bg="#dbdbdb")

'''Setting GUI: Plot data'''
def settingsGUIdata():
    global root
    dataSettingNames = ["alpha", "size", "delimiter", "xColumn", "yColumn", "originColumn"]
    settingWin = tk.Toplevel(root)
    settingWin.title("Settings: Plot data           ")
    settingWin.geometry("450x475")  # width x height
    tk.Label(settingWin, text="Settings: Plot data", font='Arial 12 bold').grid(row=0, pady=10, sticky=tk.W)

    data = settings.config["settings"]["gazeData"]
    v = tk.StringVar(root, value=data)
    tk.Entry(settingWin, textvariable=v, width="40").grid(row=1, sticky=tk.W)
    selectFileButton = createButton(settingWin, 'Select data file', selectDataFile,
                         20, 1, 1, 5, 20, bg="#dbdbdb")

    CreateToolTip(selectFileButton, text='Specify path to gaze data file...')

    delimiterEntry = createEntry(settingWin, 'Delimiter', 2, 1, settings.get("delimiter"), 0, 10, sticky=tk.W)
    CreateToolTip(delimiterEntry, text='Choose delimiter of data file...')

    xEntry = createEntry(settingWin, 'Name X column', 3, 1, settings.get("xColumn"), 0, 10, sticky=tk.W)
    CreateToolTip(xEntry, text='Specify column name of X coordinates...')

    yEntry = createEntry(settingWin, 'Name Y column', 4, 1, settings.get("yColumn"), 0, 10, sticky=tk.W)
    CreateToolTip(yEntry, text='Specify column name of Y coordinates...')

    originEntry = createEntry(settingWin, 'Name of targeted AOI column', 5, 1, settings.get("originColumn"), 0, 10, sticky=tk.W)
    CreateToolTip(originEntry, text='Specify column name of target AOI...')

    colorDataButton = createButton(settingWin, 'Color data', lambda:chooseColor(ele = 4),
                         20, 6, 0, 0, 20, bg = "#dbdbdb")
    CreateToolTip(colorDataButton, text='Choose color of data points...')

    transparencyEntry = createEntry(settingWin, 'Transparency', 7, 1, settings.get("alpha"), 0, 10, sticky=tk.W)
    CreateToolTip(transparencyEntry, text='Choose transparency of data points...')

    markerSizeEntry = createEntry(settingWin, 'Markersize', 8, 1, settings.get("size"), 0, 10, sticky=tk.W)
    CreateToolTip(markerSizeEntry, text='Choose size of data points...')

    dataEntryList = [transparencyEntry, markerSizeEntry, delimiterEntry, xEntry, yEntry, originEntry]


    createButton(settingWin, 'Start', lambda:writeToConfig(settingWin,
                                                                      "dataSettings", dataSettingNames,
                                                                      dataEntryList, plotData), 10, 9, 0, 0, 10, bg = "#dbdbdb")
    createButton(settingWin, 'Cancel',
                 lambda: settingWin.destroy(),
                 10, 9, 1, 0, 10, bg="#dbdbdb")


''' Setting GUI: Analyze data'''
def settingsGUIanalyze():
    global root
    SettingsNames = ["radiusAnalyze"]

    settingWin = tk.Toplevel(root)
    settingWin.title("Settings: Analyze data        ")
    settingWin.geometry("450x300")  # width x height
    tk.Label(settingWin, text="Settings: Analyze data", font='Arial 12 bold').grid(row=0, pady=10, sticky=tk.W)

    file = settings.get("targetPoints")
    v = tk.StringVar(root, value=file)
    tk.Entry(settingWin, textvariable=v, width="40").grid(row=1, sticky=tk.W)
    selectCenterPointsButton = createButton(settingWin, 'Select target point file', selectTargetPoints,
                               20, 1, 1, 5, 20, bg="#dbdbdb")
    CreateToolTip(selectCenterPointsButton, text='Specify path to target points file...')

    data = settings.config["settings"]["gazeData"]
    v = tk.StringVar(root, value=data)
    tk.Entry(settingWin, textvariable=v, width="40").grid(row=2, sticky=tk.W)
    selectFileButton = createButton(settingWin, 'Select data file', selectDataFile,
                         20, 2, 1, 5, 20, bg="#dbdbdb")
    CreateToolTip(selectFileButton, text='Specify path to gaze data file...')

    radiusEntry = createEntry(settingWin, u"AOI radius [°]", 3, 1, settings.get("radiusAnalyze"), 10, 15, sticky=tk.W)
    CreateToolTip(radiusEntry, text='Specify AOI size...')

    EntryList = [radiusEntry]

    createButton(settingWin, 'Start', lambda:writeToConfig(settingWin, "analyzeSettings", SettingsNames,
                                                                     EntryList, selectTargetName),
                           10, 4, 0, 0, 10, bg = "#dbdbdb")

    createButton(settingWin, 'Cancel',
                 lambda:settingWin.destroy(),
                 10, 4, 1, 0, 10, bg="#dbdbdb")

def chooseColor(ele):
    color_code = tk.colorchooser.askcolor(title="Choose color")
    if ele == 1:
        settings.config["aoiSettings"]["color"] = color_code[-1]
    elif ele == 2:
        settings.config["aoiSettings"]["colorEllipse"] = color_code[-1]
    elif  ele == 3:
        settings.config["aoiSettings"]["colorCenterpoints"] = color_code[-1]
    else:
        settings.config["dataSettings"]["color"] = color_code[-1]
    settings.saveConfig()


### ROOT WINDOW ###
''' Create base window of GUI'''
def createBaseWindow(fig, ax):
    global canvas
    global root
    root = tk.Tk()
    root.wm_title("AOEyes")
    root.iconbitmap('./ico/AOEyes_Icon.ico')

    canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    menubar = tk.Menu(root)

    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open Image...", command=selectFile)
    filemenu.add_command(label="Save", command=saveFile)
    filemenu.add_command(label="Save as...", command=saveAsFile)
    filemenu.add_command(label="Load settings...", command=settings.loadConfigFile)
    filemenu.add_command(label="General settings", command=settingsGUIgeneral)
    menubar.add_cascade(label="File", menu=filemenu)

    simulateMenu = tk.Menu(menubar, tearoff=0)
    simulateMenu.add_command(label="Manual target points", command=settingsGUIsimulationManual)
    simulateMenu.add_command(label="OpenFace target points", command=settingsGUIsimulation)
    simulateMenu.add_command(label="Load target points...", command=settingsGUIsimulationTarget)
    menubar.add_cascade(label="Generate gaze data", menu=simulateMenu)

    aoiMenu = tk.Menu(menubar, tearoff=0)
    aoiMenu.add_command(label="Manual AOIs", command=settingsGUImanualAOI)
    aoiMenu.add_command(label="OpenFace AOIs", command=settingsGUIopenface)
    aoiMenu.add_command(label="Load target points...", command=settingsGUItargetAOI)
    menubar.add_cascade(label="Plot AOIs", menu=aoiMenu)

    menubar.add_cascade(label="Plot gaze data", command=settingsGUIdata)

    menubar.add_cascade(label="Analyze classification", command=settingsGUIanalyze)

    root.config(menu=menubar)
    
    root.protocol("WM_DELETE_WINDOW", sys.exit)


### CANVAS DRAWS ###
def drawAOIsAll(ax, voronoiPoints, elli):
    ''' clear axis and redraw image '''
    try:
        ax.cla()
        img = getImageFile(settings.config["settings"]["image"])
        ax.imshow(img)
    except:
        return
    
    ''' get configurations '''
    settings.saveSession(voronoiPoints)
    deg_radius = settings.getRadiusAOI()
    distance = float(settings.config["aoiSettings"]["distanceAOI"]) * 10
    
    ''' draw AOIs '''
    for i in range(0, len(deg_radius)):
        radius = vf.degToPx(deg_radius[i], distance)
        showAOIs(ax, voronoiPoints, elli, radius)

def showAOIs(ax, voronoiPoints, elli, radius):
    global originPoints
    global text_box
    global center
    global r_min
    global r_max
    
    ''' set to global '''
    originPoints = voronoiPoints
    
    ''' get configurations '''
    title = settings.config["generalSettings"]["title"]
    centerSize = int(settings.config["aoiSettings"]["centerSize"])
    lineWidth = float(settings.config["aoiSettings"]["lineWidth"])
    color_centerpoints = settings.config["aoiSettings"]["colorCenterpoints"]
    color_elli = settings.config["aoiSettings"]["colorEllipse"]
    color_bound = settings.config["aoiSettings"]["color"]
    xLimInfo = settings.config["generalSettings"]["xLim"]
    yLimInfo = settings.config["generalSettings"]["yLim"]
    axisInfo = settings.config["generalSettings"]["axis"]
    
    ''' set details '''
    fig.suptitle(title, fontsize=12)
    if xLimInfo != "":
        xLimInfo = tuple(map(int, xLimInfo.split(',')))
        ax.set_xlim(xLimInfo)
        
    if yLimInfo != "":
        yLimInfo = tuple(map(int, yLimInfo.split(',')))
        ax.set_ylim(yLimInfo)

    if int(axisInfo) < 1:
        ax.axis('off')
    else:
        ax.axis('on')


    ''' draw voronoi LRVT '''
    voronoiLR.drawLRVTfromPoints(ax, voronoiPoints, radius, lineWidth, color_bound, color_centerpoints, centerSize)
    
    ''' draw ellipse '''
    if elli:
        ellipse = matplotlib.patches.Ellipse(xy = (center[0], center[1]), width = r_min*2, height = r_max*2,
                                             fill = False, color = color_elli, linewidth = lineWidth)
        ax.add_patch(ellipse)
    
    canvas.draw()

def drawTargetPointsManual(event):
    global originPoints
    global ax
    global scatter
    global state

    ''' get configurations '''
    centerSize = int(settings.config["aoiSettings"]["centerSize"])

    ''' if not in correct state, return '''
    if not state == 1:
        return
    
    if event.button == 1 and event.xdata is not None:
        ''' get target points '''
        point = [event.xdata, event.ydata]
        originPoints.append(point)
        pts = np.asarray(originPoints)
        
        ''' redraw target points ''' 
        try:
            scatter.remove()
        except:
            pass
        scatter = ax.scatter(pts[:,0], pts[:,1], marker = '+', c = '#FF0000')
    elif event.button == 3:
        if len(originPoints) <= 0:
            return
        
        ''' remove target point '''
        del originPoints[-1]
        scatter.remove()
        
        ''' redraw remaining target points '''
        pts = np.asarray(originPoints)
        if len(originPoints) > 0:
            scatter = ax.scatter(pts[:,0], pts[:,1], markersize = centerSize, marker = '+', c = '#FF0000')
            
    canvas.draw()
               
def targetAOIs():
    ''' clear axis and redraw image '''
    try:
        ax.cla()
        img = getImageFile(settings.config["settings"]["image"])
        ax.imshow(img)
    except:
        return
    
    ''' read target points from file '''
    target = getTargetFile()
    targetFile = pd.read_csv(target, delimiter = ',')
    pts = pd.DataFrame(targetFile).to_numpy()
    
    ''' draw AOIs '''
    drawAOIsAll(ax, pts, False)
    
def ofAOIs():
    global center
    global r_min
    global r_max
    
    ''' clear axis and redraw image '''
    try:
        ax.cla()
        img = getImageFile(settings.config["settings"]["image"])
        ax.imshow(img)
    except:
        return

    ''' get configurations '''
    excluded = []
    elli = True
    pathname = settings.config["settings"]["openFace"]
    if not os.path.isfile(pathname) and not ".exe" in pathname:
        selectPathExe()
    if settings.aoiCfg.lefteye == "0":
        excluded.append(0)
    if settings.aoiCfg.righteye == "0":
        excluded.append(1)
    if settings.aoiCfg.nose == "0":
        excluded.append(2)
    if settings.aoiCfg.mouth == "0":
        excluded.append(3)
    if settings.aoiCfg.ellipse == "0":
        elli = False

        
    ''' get landmarks '''
    landmarks, center, r_min, r_max, trial = vf.getLandmarksOF()
    landmarks = np.delete(landmarks, excluded, axis = 0)

    ''' draw AOIs '''
    drawAOIsAll(ax, landmarks, elli)

def plotData():
    global ax
    global canvas
    global fileGazeData

    ''' set configurations '''
    delim = settings.config["dataSettings"]["delimiter"]
    transparency = float(settings.config["dataSettings"]["alpha"])
    rgb = hex_to_rgb(settings.config["dataSettings"]["color"])
    hex = settings.config["dataSettings"]["color"]
    markerSize = float(settings.config["dataSettings"]["size"])
    nameX = settings.config["dataSettings"]["xColumn"]
    nameY = settings.config["dataSettings"]["yColumn"]
    nameOrigin = settings.config["dataSettings"]["originColumn"]
    xLimInfo = settings.config["generalSettings"]["xLim"]
    yLimInfo = settings.config["generalSettings"]["yLim"]
    axisInfo = settings.config["generalSettings"]["axis"]
    title = settings.config["generalSettings"]["title"]
    
    ''' set details '''
    fig.suptitle(title, fontsize=12)
    if xLimInfo != "":
        xLimInfo = tuple(map(int, xLimInfo.split(',')))
        ax.set_xlim(xLimInfo)
        
    if yLimInfo != "":
        yLimInfo = tuple(map(int, yLimInfo.split(',')))
        ax.set_ylim(yLimInfo)
        
    if int(axisInfo) < 1:
        ax.axis('off')
    else:
        ax.axis('on')
    
    ''' read from data file '''
    dataFile = getDataFile()
    try:
        data = pd.read_csv(dataFile, delimiter=delim)
    except:
        return

    df_data = pd.DataFrame(data)

    if nameOrigin == "":
        ''' remove old data '''
        if fileGazeData is not None:
            fileGazeData.remove()

        ''' draw new data points '''
        fileGazeData = ax.scatter(df_data[nameX], df_data[nameY], s=markerSize, color=hex,
                                  alpha=transparency)
    else:
        nrAOIs = len(np.unique(df_data[nameOrigin]))
        colorScheme = colorsys.rgb_to_hls(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)

        ''' calculate color scheme'''
        colors = []
        for i in range(0, nrAOIs):
            offset = i / nrAOIs
            h = (colorScheme[0] + offset) % 1

            col = colorsys.hls_to_rgb(colorScheme[0] + offset, colorScheme[1], colorScheme[2])
            col = (col[0], col[1], col[2])
            colors.append(col)
        color_labels = df_data[nameOrigin].unique()
        color_map = dict(zip(color_labels, colors))

        ''' remove old data '''
        if fileGazeData is not None:
            fileGazeData.remove()

        ''' draw new data points '''
        fileGazeData = ax.scatter(df_data[nameX], df_data[nameY], s=markerSize, c=df_data[nameOrigin].map(color_map),alpha=transparency)

    canvas.draw()

def plotStackedBar():
    global canvas
    global ins

    ''' read from data file '''
    gaze = getDataFile()
    target = getTargetFile()
    gazePoints = pd.read_csv(gaze, delimiter=',')
    targetPoints = pd.read_csv(target, delimiter=',')
    targetArr = pd.DataFrame(targetPoints).to_numpy()

    ''' configurations '''
    ax_width = 0.5
    ax_height = 0.23
    ax_posX = 0.7
    ax_posY = 0.75
    width = 0.2
    xPos = 0.23
    
    ''' classify gaze points '''
    ccPercent, fcPercent, ncPercent = analyzeAccPrec_ET.analyzeGazePoints(gazePoints, targetArr)


    ''' remove old subgraph '''
    try:
        ins.remove()
    except:
        pass
    
    ''' insert new subgraph '''
    ins = ax.inset_axes([ax_posX, ax_posY, ax_width, ax_height])
    ins.set_xlim(0,1)
    ins.get_xaxis().set_visible(False)
    ins.get_yaxis().set_visible(False)
    ins.bar(xPos, ncPercent*100, width, bottom=np.array(fcPercent*100) + np.array(ccPercent*100),
           label='Not C', color = '#dddddd')
    ins.bar(xPos, fcPercent*100, width, bottom=ccPercent*100, label='False C', color = "#fe5d00")
    ins.bar(xPos, ccPercent*100, width,
            label='Correct C', color="#005900")
    yCC = (ccPercent * 100) / 2
    if yCC < 10:
        yCC = 10
    ins.text(x=xPos+0.1, y= yCC, s=f"{round(ccPercent*100,1)}"+"%", fontdict=dict(fontsize=9), va='center')
    
    yFC = (ccPercent*100 + fcPercent*100/2)
    if yFC > 93:
        yFC = 93
    ins.text(x=xPos+0.1, y=yFC , s=f"{round((fcPercent*100),1)}"+"%", fontdict=dict(fontsize=9), va='center')
    
    yNC = (ccPercent * 100 + fcPercent * 100 + ncPercent*100/ 2)
    if yNC > 93:
        yNC = 93
        if yFC >= 93:
            xPos = -0.15
    ins.text(x=xPos + 0.1, y=yNC, s=f"{round((ncPercent*100),1)}" + "%",
             fontdict=dict(fontsize=9), va='center')

    ins.set_ylabel('Percent (%)')
    ins.legend(title_fontsize="xx-small", fontsize="xx-small")
    
    canvas.draw()
    

### SET MANUAL TARGETS CALLBACKS ###
def manualTargetPoints(completeFunction):
    global state
    global fig
    global originPoints
    global cid
    global cid2
    
    ''' clear axis and redraw image '''
    try:
        ax.cla()
        img = getImageFile(settings.config["settings"]["image"])
        ax.imshow(img)
    except:
        return
    
    ''' set details '''
    originPoints = []
    tellme('Left-click at the corresponding position to define AOI center point.\nRight-click to remove point.\n'
           'Enter to confirm selection.')
    
    ''' switch into manual target point state '''
    state = 1

    ''' register callbacks '''
    cid2 = fig.canvas.callbacks.connect('button_press_event', drawTargetPointsManual)
    cid = fig.canvas.callbacks.connect('key_press_event', completeFunction)

def completeTargetPointState():
    global state
    global fig
    global scatter    
    global originPoints
    global cid
    global cid2
    
    ''' exit manual target point state'''
    state = 2
    
    ''' remove target points and callbacks'''
    scatter.remove()
    fig.canvas.callbacks.disconnect(cid2)
    fig.canvas.callbacks.disconnect(cid)

    tellme("")

    ''' return target points '''
    pts = np.asarray(originPoints)
    elli = 0
    
    return pts

def completeManualAOIs(event):
    global state

    ''' check if in correct state and button press'''
    if not state == 1:
        return
    if not (event.key == "enter" or event.key == " "):
        return
    
    elli = False
    pts = completeTargetPointState()
    drawAOIsAll(ax, pts, elli)
    
def completeManualTargetPoints(event):
    global state
    
    ''' check if in correct state and button press'''
    if not state == 1:
        return
    if not (event.key == "enter" or event.key == " "):
        return
    
    elli = False
    pts = completeTargetPointState()
    simulateAccPrec_ET.startAccPrecManual(pts)


### START ###
global ax
global fig
global outputDir
global originPoints
global fileGazeData
fileGazeData = None
originPoints = []

backend_bases.NavigationToolbar2.toolitems = (
        (None, None, None, None),
        ('Home', 'Reset original view', 'home', 'home'),
        (None, None, None, None),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        (None, None, None, None),
      )

''' Create output directory if it doesn't exist '''
dir_path = os.path.dirname(os.path.realpath(__file__))
outputDir = dir_path + "\\output"
os.makedirs(outputDir, exist_ok=True)

fig, ax = plt.subplots()
createBaseWindow(fig, ax)

tk.mainloop()

