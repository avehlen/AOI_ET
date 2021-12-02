import math
import numpy as np
import voronoi_functions as vf
import pandas as pd
import settings
import os
from datetime import datetime
global outputDir


''' check if gazepoints are in their origin AOI '''
def analyzeGazePoints(gazePoints, targetPoints):
    global saveDir
    global filepath
    lm = targetPoints
    
    gp_frame = pd.DataFrame(gazePoints)
    
    ''' get configurations '''
    nameX = settings.config["dataSettings"]["xColumn"]
    nameY = settings.config["dataSettings"]["yColumn"]
    nameOrigin = settings.config["dataSettings"]["originColumn"]
    radius = float(settings.config["analyzeSettings"]["radiusAnalyze"])


    distance = float(settings.config["aoiSettings"]["distanceAOI"])* 10
    
    ''' allocate arrays '''
    originAOI = gp_frame[nameOrigin].to_numpy()
    gpX = gp_frame[nameX].to_numpy()
    gpY = gp_frame[nameY].to_numpy()
    
    lenGpX = gpX.size
    lenGpY = gpY.size

    
    ''' get AOI radius '''
    rad = vf.degToPx(radius, distance)
    landmarks, center, rMin, rMax, fhPoint = vf.getLandmarksOF()

    inAOI = np.zeros((lenGpX, 1))
    inElli = np.zeros((lenGpX, 1))
    correctlyClassified = np.zeros((lenGpX, 1))
    falselyClassified = np.zeros((lenGpX, 1))
    notClassified = np.zeros((lenGpX, 1))
    
    for i in range(0, lenGpX):

        gazepoint = [gpX[i], gpY[i]]

        ''' get voronoi index '''
        index = vf.inLRVT(lm, gazepoint, rad)

        ''' get ellipse information '''
        inElli[i] = vf.inEllipse(center, rMin, rMax, gazepoint)

        ''' classify '''
        inAOI[i] = index
        if index == originAOI[i]:
            correctlyClassified[i] = 1
        elif index > 0:
            falselyClassified[i] = 1
        else:
            notClassified[i] = 1

        ''' prepare pandas dataframe '''
        data = list(zip(gpX, gpY, originAOI, inAOI, inElli, correctlyClassified, falselyClassified, notClassified))

        ''' create pandas dataframe with classification data '''
        df = pd.DataFrame(data, columns=["gpX", "gpY", "originalAOI", "foundAOI","inEllipse", "CC", "FC", "notC"])
        df['foundAOI'] = df['foundAOI'].astype(int)
        df['inEllipse'] = df['inEllipse'].astype(int)
        df['CC'] = df['CC'].astype(int)
        df['FC'] = df['FC'].astype(int)
        df['notC'] = df['notC'].astype(int)

        ''' set save directory '''
        setSaveDir()
        createOutputDir()

        ''' save classification data '''
        df.to_csv(filepath + "\\classified_radius" + str(radius) + ".csv", index=False)


    ''' summerize '''
    ccPercent = np.sum(correctlyClassified)/len(gpX)
    fcPercent = np.sum(falselyClassified)/len(gpX)
    ncPercent = np.sum(notClassified)/len(gpX)
    
    return ccPercent, fcPercent, ncPercent


def setSaveDir():
    global outputDir
    global saveDir

    ''' create timestamped output folder '''
    today = datetime.today()
    timeStamp = today.strftime("%d.%m.%Y_%H_%M_%S")
    saveDir = outputDir + "\\" + timeStamp
    os.makedirs(saveDir, exist_ok=True)


def createOutputDir():
    global filepath
    global saveDir

    filepath = saveDir + "\\Classification"
    os.makedirs(filepath, exist_ok=True)


global outputDir
global saveDir

''' Create output directory if it doesn't exist '''
dir_path = os.path.dirname(os.path.realpath(__file__))
outputDir = dir_path + "\\output"
os.makedirs(outputDir, exist_ok=True)

