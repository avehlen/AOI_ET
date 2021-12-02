from scipy.stats import pearson3 as pears
import math
import numpy as np
import voronoi_functions as vf
import pandas as pd
import tkinter as tk
import settings
import os

from tkinter import ttk
import tkinter as tk

def getSettings():
    sSize = int(settings.config["simulationSettings"]["sampleSize"])
    runs = int(settings.config["simulationSettings"]["runsPerSample"])
    accuracy = float(settings.config["simulationSettings"]["accuracy"])
    precision = float(settings.config["simulationSettings"]["precision"])
    fps = int(settings.config["simulationSettings"]["fps"])
    duration = int(settings.config["simulationSettings"]["durationSeconds"])
    skew = float(settings.config["simulationSettings"]["skew"])
    sd = float(settings.config["simulationSettings"]["sd"])


class Settings():
    def __init__(self):
        self.size = int(settings.config["simulationSettings"]["sampleSize"])
        self.runs = int(settings.config["simulationSettings"]["runsPerSample"])
        self.accuracy = float(settings.config["simulationSettings"]["accuracy"])
        self.precision = float(settings.config["simulationSettings"]["precision"])
        self.fps = int(settings.config["simulationSettings"]["fps"])
        self.duration = int(settings.config["simulationSettings"]["durationSeconds"])
        self.distance = float(settings.config["simulationSettings"]["distanceSim"])* 10
        self.skew = float(settings.config["simulationSettings"]["skew"])
        self.sd = float(settings.config["simulationSettings"]["sd"])
        self.LRVTrad = settings.getRadiusAOI()


class AOIs():
    def __init__(self, landmarks):
        self.lefteye = landmarks[0]
        self.righteye = landmarks[1]
        self.nose = landmarks[2]
        self.mouth = landmarks[3]

    def setFH(self, fh):
        self.forehead = fh


def normalClamp(mean, sd, maxDev, minValue = -np.inf, maxValue = np.inf):
    rand = np.random.normal(mean, sd)
    while np.abs(rand - mean) > maxDev or rand < minValue or rand > maxValue:
        rand = np.random.normal(mean, sd)
        
    return rand


def startAccPrecOF(vpnNrStart = 1):
    global center
    global rMin
    global rMax
    global createEllipse
    
    createEllipse = True
    
    ''' Get landmarks '''
    landmarks, center, rMin, rMax, fhPoint = vf.getLandmarksOF()
    if landmarks is None:
        return
    
    lm = AOIs(landmarks)
    lm.setFH(fhPoint)
    lmArr = getLMtoSimulate(lm)
    
    ell = [center, rMin, rMax]
    startAccPrecSimulation(lmArr, vpnNrStart)
    
    
def startAccPrecManual(landmarks, vpnNrStart = 1):
    global createEllipse
    createEllipse = False
    startAccPrecSimulation(landmarks, vpnNrStart)
    
def startAccPrecTargets(vpnNrStart = 1):
    global createEllipse
    createEllipse = False
    targetFile = settings.get("targetPoints")
    
    landmarksFile = pd.read_csv(targetFile, delimiter = ',')
    lmArr = pd.DataFrame(landmarksFile).to_numpy()
    
    startAccPrecSimulation(lmArr, vpnNrStart)
    
    
def startAccPrecSimulation(lmArr, vpnNrStart = 1):
    global vpnNr

    """ save current configurations """
    settings.saveSession(lmArr)
    
    cfg = Settings()

    nrVpn = cfg.size
    nrRuns = cfg.runs
    duration = cfg.duration
    fps = cfg.fps

    lengthFileVpn = nrRuns*duration*fps

    gpMeanTotalX = []
    gpMeanTotalY = []


    ''' Create the output directory '''
    createOutputDir(cfg.accuracy, cfg.precision)

    ''' Draw random accuracies from a pearson 3 (gamma), normal or uniform distribution '''
    accuracies = None
    if settings.config["simulationSettings"]["distribution"] == "Gamma":
        accuracies = pears.rvs(cfg.skew, loc=cfg.accuracy, scale=cfg.sd, size=cfg.size)
    elif settings.config["simulationSettings"]["distribution"] == "Normal":
        accuracies = np.random.normal(cfg.accuracy, cfg.sd, cfg.size)
    elif settings.config["simulationSettings"]["distribution"] == "Uniform":
        accuracies = np.random.uniform(cfg.accuracy-cfg.sd, cfg.accuracy+cfg.sd, cfg.size)
        
    ''' Show progress Bar '''
    createProgressBar()
    updateProgress(0, cfg.size)
    
    for i in range(0, cfg.size):
        gazePointsXarrVpn = []
        gazePointsYarrVpn = []
        gpMeanAggX = []
        gpMeanAggY = []
        inAOIarrVpn = []
        inEllipseArrVpn = []      

        angle = np.random.uniform(0,2*np.pi)
        vpnNr = vpnNrStart + i
        
        ''' Redraw accuracy if it falls below (or equal) 0 '''
        acc = accuracies[i]
        while acc <= 0:
            if settings.config["simulationSettings"]["distribution"] == "Gamma":
                acc = pears.rvs(cfg.skew, loc=cfg.accuracy, scale=cfg.sd)
            elif settings.config["simulationSettings"]["distribution"] == "Normal":
                acc = np.random.normal(cfg.accuracy, cfg.sd)
            elif settings.config["simulationSettings"]["distribution"] == "Uniform":
                acc = np.random.uniform(cfg.accuracy-cfg.sd, cfg.accuracy+cfg.sd)
                
        ''' Set precision and redraw if the deviation is too high '''
        prec = normalClamp(cfg.precision, cfg.precision*0.3, 1.5, 0)

        for j in range(0, cfg.runs):
            tmpAcc = normalClamp(acc, acc*0.15, 3, 0)
            tmpPrec = normalClamp(prec, prec*0.15, 1.5, 0)
            
            gazePointsXall, gazePointsYall, inAOI, inEllipse, gpMeanX, gpMeanY = simulateAccPrec(vpnNr, j, tmpAcc,
                                                                               tmpPrec, angle, lmArr, cfg)
            gazePointsXarrVpn.append(gazePointsXall)
            gazePointsYarrVpn.append(gazePointsYall)
            inAOIarrVpn.append(inAOI)
            inEllipseArrVpn.append(inEllipse)

            gpMeanAggX.append(gpMeanX)
            gpMeanAggY.append(gpMeanY)

        gpMeanTotalX.append(np.mean(gpMeanAggX, 0))
        gpMeanTotalY.append(np.mean(gpMeanAggY, 0))
        
        ''' Update progress Bar '''
        updateProgress(i+1, cfg.size)
        saveSimulatedDataAgg(vpnNr, gazePointsXarrVpn, gazePointsYarrVpn, inAOIarrVpn, inEllipseArrVpn, lengthFileVpn,
                             cfg, lmArr)

    getFixationPoints(gpMeanTotalX, gpMeanTotalY, cfg, vpnNrStart, lmArr)

    ''' Destroy progress bar window '''
    updateProgress(2, 1)

def simulateAccPrec(vpnNr, runNr, accuracy, precision, angle, lm, cfg):
    global center
    global rMin
    global rMax
    global createEllipse
    
    fps = cfg.fps
    duration = cfg.duration
    distance = cfg.distance

    lengthFile = fps*duration
    
    ''' initialize arrays '''
    PAcc = np.zeros((fps*duration, 1))
    PAccs = np.zeros((fps*duration, 1))
    DeviationX = np.zeros((fps*duration, len(lm)))
    DeviationY = np.zeros((fps*duration, len(lm)))
    PAccDeg = np.zeros((len(lm), 1))
    PrecStd = np.zeros((len(lm), 1))
    gazePointsXall = np.zeros((fps*duration, len(lm)))
    gazePointsYall = np.zeros((fps*duration, len(lm)))
    inAOI = np.zeros((fps*duration, len(lm)))
    inEllipse = np.zeros((fps*duration, len(lm)))
    inAllAOIs = []
    
    ''' mean values '''
    gpMeanX = np.zeros((len(lm), 1))
    gpMeanY = np.zeros((len(lm), 1))

    accuracyThr = 0.05
    precisionThr = 0.05
    
    ''' convert degrees to px '''
    precPx = vf.degToPx(precision, distance)
    accPx = vf.degToPx(accuracy, distance)

    ''' start simulation '''
    for i in range(0, len(lm)):
        repeat = True
        while repeat:
            ''' Slightly randomize '''
            accDist = np.random.uniform(accPx * 0.9, accPx * 1.1)
            angle = np.random.uniform(angle - np.pi/6, angle + np.pi/6)
            lm = np.array(lm)
            offset = [lm[i,0] + np.cos(angle) * accDist, lm[i,1] + np.sin(angle) * accDist]

            ''' Create normal distributed gaze points around the starting point '''
            gazePointsX = np.random.normal(offset[0], precPx/np.sqrt(2), fps*duration)
            gazePointsY = np.random.normal(offset[1], precPx/np.sqrt(2), fps*duration)
            
            ''' Calculate accuracy and deviation for every gaze point '''
            for j in range(0, cfg.fps*cfg.duration):
                PAccs[j] = np.sqrt((lm[i,0] - gazePointsX[j])**2 + (lm[i,1] - gazePointsY[j])**2) 
                PAcc[j] = vf.pxToDeg(PAccs[j], cfg.distance)
                DeviationX[j,i] = lm[i,0] - gazePointsX[j]
                DeviationY[j,i] = lm[i,1] - gazePointsY[j]
                
            ''' Calculate accuracy and precision among all gaze points '''
            PAccPx = np.sqrt((lm[i,0] - np.mean(gazePointsX))**2 + (lm[i,1] - np.mean(gazePointsY))**2) 
            PAccDeg[i] = vf.pxToDeg(PAccPx, cfg.distance)
          
            prec = np.sqrt(np.std(gazePointsX)**2 + np.std(gazePointsY)**2)
            PrecStd[i] = vf.pxToDeg(prec, cfg.distance)
            
            ''' Discard and repeat if thresholds aren't met '''
            if abs(PAccDeg[i] - accuracy) > accuracyThr or abs(PrecStd[i] - precision) > precisionThr:
                repeat = True
            else:
                repeat = False
                             
        gazePointsXall[:,i] = gazePointsX
        gazePointsYall[:,i] = gazePointsY
        gpMeanX[i] = np.mean(gazePointsX)
        gpMeanY[i] = np.mean(gazePointsY)

    ''' Classify gaze points in AOIs '''
    for radius in cfg.LRVTrad:
        rad = vf.degToPx(radius, cfg.distance)
        inAOI = np.zeros((fps*duration, len(lm)))
        for j in range(0, len(lm)):
            for i in range(0, fps*duration):
                
                gazepoint = [gazePointsXall[i,j], gazePointsYall[i,j]]
                
                ''' get voronoi index '''
                index = vf.inLRVT(lm[0:4], gazepoint, rad)
                
                if createEllipse:
                    inEllipse[i,j] = 1
                    inEll = vf.inEllipse(center, rMin, rMax, gazepoint)
                    if not inEll:
                        inEllipse[i,j] = 0
                    if not inEll and index == 0:
                        index = -1
                elif index == 0:
                    index = -1
    
                inAOI[i,j] = index
        
        inAllAOIs.append(inAOI)

    #saveSimulatedData(vpnNr, runNr, gazePointsXall, gazePointsYall, inAOI, inEllipse, lengthFile)

    return gazePointsXall, gazePointsYall, inAllAOIs, inEllipse, gpMeanX, gpMeanY


def getLMtoSimulate(landmarks):
    lmCfg = settings.getCfg("simulation")
    lm = []
    if lmCfg.getKey("lefteye") == "1":
        lm.append(landmarks.lefteye)
    if lmCfg.getKey("righteye") == "1":
        lm.append(landmarks.righteye)
    if lmCfg.getKey("nose") == "1":
        lm.append(landmarks.nose)
    if lmCfg.getKey("mouth") == "1":
        lm.append(landmarks.mouth)
    if lmCfg.getKey("forehead") == "1":
        lm.append(landmarks.forehead)
        
    return lm

def saveSimulatedDataAgg(vpnNr, gpX, gpY, inAOI, inEllipse, lengthFile, cfg, lm):
    global filepath

    fps = cfg.fps
    runNr = cfg.runs
    
    runVar = []
    runCounter = 0
    for i in range(0, runNr):
        runCounter = runCounter + 1
        for j in range(0,fps):
            runVar.append(runCounter)

    ''' flatten all arrays '''
    vpn = []
    orig = []
    run = []
    for i in range(0,len(lm)):
        vpn.append(np.zeros((lengthFile, 1)) + vpnNr)
        orig.append(np.zeros((lengthFile, 1)) + i + 1)
        run.append(runVar)



    gpXAll = np.ndarray.flatten(np.transpose(np.array(gpX)))
    gpYAll = np.ndarray.flatten(np.transpose(np.array(gpY)))
    ellAll = np.ndarray.flatten(np.transpose(np.array(inEllipse)))
    origAll = np.ndarray.flatten(np.array(orig))
    vpnAll = np.ndarray.flatten(np.array(vpn))
    runAll = np.ndarray.flatten(np.array(run))

    arr = np.array([vpnAll, runAll, gpXAll, gpYAll, origAll, ellAll])
    col = ["vpn", "run", "X", "Y", "Original_AOI", "Ellipse"]
    for j in range(0, len(inAOI[0])):
        vpnAOI = []
        for i in range(0, len(inAOI)):
            vpnAOI.append(inAOI[i][j])
        
        aoiAll = np.ndarray.flatten(np.transpose(np.array(vpnAOI)))
        aoiAll = np.array([aoiAll])
        arr = np.append(arr, aoiAll, 0)
        col.append("Found_AOI_rad_" + str(cfg.LRVTrad[j]))
    
    arr = np.transpose(arr)

    df = pd.DataFrame(data=arr, columns=col)
    df.to_csv(filepath + "\\vpn" + str(vpnNr) + ".csv", index=False)


''' Save fixation points (mean gaze points per participant) '''
def getFixationPoints(gpX, gpY, cfg, vpnNrStart, lm):
    global filepath

    sampleSize = cfg.size

    ''' Recreate vpnNr from start '''
    vpnVar = []
    vpnCounter = vpnNrStart
    for i in range(0, sampleSize):
        vpnVar.append(vpnCounter)
        vpnCounter = vpnCounter + 1
            
    vpn = []
    orig = []
    for i in range(0,len(lm)):
        vpn.append(vpnVar)
        orig.append(np.zeros((sampleSize, 1)) + i + 1)

    gpXAll = np.ndarray.flatten(np.transpose(np.array(gpX)))
    gpYAll = np.ndarray.flatten(np.transpose(np.array(gpY)))
    vpnAll = np.ndarray.flatten(np.array(vpn))
    origAll = np.ndarray.flatten(np.array(orig))


    arr = np.array([vpnAll, gpXAll, gpYAll, origAll])

    arr = np.transpose(arr)

    df = pd.DataFrame(data=arr, columns=["vpn","X", "Y", "Original_AOI"])

    df.to_csv(filepath + "\\FixationPoints.csv", index=False)

def createOutputDir(accuracy, precision):
    global filepath
   
    filepath = settings.saveDir + "\\acc" + str(accuracy) + "_prec" + str(precision) 
    os.makedirs(filepath, exist_ok=True)

    
''' Create progress bar '''
def createProgressBar():
    global canvas
    global root
    global progress
    global prLabel
    
    root = tk.Tk()
    root.wm_title("Progress data generation...")
    root.geometry("420x150")  # width x height
    prLabel = tk.Label(root, text = "Please wait...", font='Arial 12 bold').grid(row = 0, pady = 10, sticky = tk.N)
    progress=ttk.Progressbar(root,orient="horizontal",length=400,mode='determinate')
    progress.grid(row = 1, pady = 10, padx = 10)


def updateProgress(i, max):
    global root
    global progress
    global prLabel
    progress['value']=int(i/max*100)
    root.update()
    if i > max:
        root.destroy()
    elif i == max:
        prLabel = tk.Label(root, text = "Saving...", font='Arial 12 bold').grid(row = 0, pady = 10, sticky = tk.N)

global createEllipse
createEllipse = False