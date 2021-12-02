import numpy as np
import pandas as pd
import settings
import os
import tkinter as tk
import subprocess
import math


''' Get index of closest voronoi point in specified radius or return -1 '''
def inLRVT(vPoints, point, maxDist = np.inf):
    if maxDist < np.inf:
        maxDist = maxDist*maxDist
        
    min = -1
    index = -1

    for i in range(0, len(vPoints)):
        dist = (vPoints[i,0] - point[0])**2 + (vPoints[i,1] - point[1])**2
        
        if dist < min or min < 0:
            min = dist
            
            ''' check if dist is within bounds '''
            if min <= maxDist:
                index = i

    return index+1


''' Check if a point is in ellipse with given center, horizontal and vertical radius (not angled) '''
def inEllipse(center, radX, radY, point):
    inEll = False
    
    # (x-h)^2/radX^2 + (y-k)^2/radY^2 <= 1
    tmp = (point[0] - center[0])**2 * radY**2 + (point[1] - center[1])**2 * radX**2

    if tmp <= radX**2*radY**2 and not tmp == 0:
        inEll = True
        
    return inEll


def getLandmarksOF():
    ''' Get paths '''
    image_path = settings.config["settings"]["image"]   
    image_name = image_path.split("/")[-1]
    image_name = image_name.split(".")[0]

    pathname = settings.config["settings"]["openFace"]

    
    ''' Start open face facial landmark detection '''
    try:
        subprocess.call([pathname, '-f', image_path])
    except:
        return None, None, None, None, None
    
      
    landmarksFile = pd.read_csv('./processed/' + image_name + '.csv', delimiter = ',')
    landmarksDF = pd.DataFrame(landmarksFile)
    
    ''' Determine AOI center points '''
    lefteyeCoords = np.empty([1,2])
    lefteyeCoords[0,0] = (landmarksDF[" x_36"][0] + landmarksDF[" x_39"][0]) / 2
    lefteyeCoords[0,1] = (landmarksDF[" y_36"][0] + landmarksDF[" y_39"][0]) / 2
    
    righteyeCoords = np.empty([1, 2])
    righteyeCoords[0,0] = (landmarksDF[" x_42"][0] + landmarksDF[" x_45"][0]) / 2
    righteyeCoords[0,1] = (landmarksDF[" y_42"][0] + landmarksDF[" y_45"][0]) / 2
    
    noseCoords = np.empty([1, 2])
    noseCoords[0,0] = landmarksDF[" x_30"][0]
    noseCoords[0,1] = landmarksDF[" y_30"][0]
    
    mouthCoords = np.empty([1, 2])
    mouthCoords[0,0] = landmarksDF[" x_51"][0]
    mouthCoords[0,1] = landmarksDF[" y_51"][0]
    
    landmarks = np.concatenate((lefteyeCoords, righteyeCoords, noseCoords, mouthCoords))
    landmarks = np.array(landmarks)

    
    ''' Determine face ellipse from landmarks '''
    center = np.empty([2,1], dtype=int)
    center[0] = (lefteyeCoords[0,0] + righteyeCoords[0,0])/2
    facethird = landmarksDF[" y_8"][0] - landmarksDF[" y_33"][0]
    center[1] = landmarksDF[" y_8"][0] - facethird * 3/2
    leftdist = math.hypot(landmarksDF[" x_0"][0] - center[0], landmarksDF[" y_0"][0] - center[1])
    rightdist = math.hypot(landmarksDF[" x_16"][0] - center[0], landmarksDF[" y_16"][0] - center[1])
    radX = min(leftdist, rightdist)
    radY = math.hypot(center[0] - landmarksDF[" x_8"][0], center[1] - landmarksDF[" y_8"][0])
    
    ''' Determine a forehead point from landmarks '''
    faceBottom = [landmarksDF[" x_8"][0], landmarksDF[" y_8"][0]]
    faceTop = np.round(mirrorPointByPoint(faceBottom, center))
    fhPoint = np.round([(faceTop[0] + faceBottom[0])/2, faceTop[1]*2/3 + faceBottom[1]/3])
    fhPoint = np.ndarray.flatten(np.array(fhPoint))

    return landmarks, center, radX, radY, fhPoint

''' Convert visual degrees to pixel distance '''
def degToPx(degree, distance):
    rad = np.deg2rad(degree)
    mmDist = np.tan(rad)*distance
    pxDist = mmDist * getMmToPxFactor(distance)
    return pxDist

''' Get the conversion factor for mm to pixel '''
def getMmToPxFactor(distance):
    factor = (339165 * np.power(distance, -1.003)) / 200
    return factor

''' Convert pixel distance to visual degrees '''
def pxToDeg(pxDist, distance):
    mmDist = pxDist / getMmToPxFactor(distance)
    deg = np.rad2deg(np.arctan(mmDist/distance))
    return deg



''' Mirror a point by a specified fix point '''
def mirrorPointByPoint(point, fixPoint):
    dx = fixPoint[0] - point[0]
    dy = fixPoint[1] - point[1]
    
    if dx == 0:
        mPoint = [point[0], point[1]+2*dy]
        return mPoint
    elif dy == 0:
        mPoint = [point[0]+2*dx, point[1]]
        return mPoint
    
    a = dy/dx
    b = point[1] - a*point[0]
    
    y = point[1] + 2*dy
    x = (y-b)/a
    
    mPoint = [x, y]
    return mPoint
    