from collections import defaultdict
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi
import numpy as np
import math
from textwrap import indent


def voronoi_polygons(voronoi, diameter):
    """Generate shapely.geometry.Polygon objects corresponding to the
    regions of a scipy.spatial.Voronoi object, in the order of the
    input points. The polygons for the infinite regions are large
    enough that all points within a distance 'diameter' of a Voronoi
    vertex are contained in one of the infinite polygons.
    
    By BeatTheBookie at https://github.com/exasol/sports-analytics/blob/master/voronoi%20showcase/voronoi_polygon_calculation.py
    """
    centroid = voronoi.points.mean(axis=0)

    # Mapping from (input point index, Voronoi point index) to list of
    # unit vectors in the directions of the infinite ridges starting
    # at the Voronoi point and neighbouring the input point.
    ridge_direction = defaultdict(list)
    for (p, q), rv in zip(voronoi.ridge_points, voronoi.ridge_vertices):
        u, v = sorted(rv)
        if u == -1:
            # Infinite ridge starting at ridge point with index v,
            # equidistant from input points with indexes p and q.
            t = voronoi.points[q] - voronoi.points[p] # tangent
            n = np.array([-t[1], t[0]]) / np.linalg.norm(t) # normal
            midpoint = voronoi.points[[p, q]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - centroid, n)) * n
            ridge_direction[p, v].append(direction)
            ridge_direction[q, v].append(direction)

    for i, r in enumerate(voronoi.point_region):
        region = voronoi.regions[r]
        if -1 not in region:
            # Finite region.
            yield Polygon(voronoi.vertices[region])
            continue
        # Infinite region.
        inf = region.index(-1)              # Index of vertex at infinity.
        j = region[(inf - 1) % len(region)] # Index of previous vertex.
        k = region[(inf + 1) % len(region)] # Index of next vertex.
        if j == k:
            # Region has one Voronoi vertex with two ridges.
            dir_j, dir_k = ridge_direction[i, j]
        else:
            # Region has two Voronoi vertices, each with one ridge.
            dir_j, = ridge_direction[i, j]
            dir_k, = ridge_direction[i, k]

        # Length of ridges needed for the extra edge to lie at least
        # 'diameter' away from all Voronoi vertices.
        length = 2 * diameter / np.linalg.norm(dir_j + dir_k)

        # Polygon consists of finite part plus an extra edge.
        finite_part = voronoi.vertices[region[inf + 1:] + region[:inf]]
        extra_edge = [voronoi.vertices[j] + dir_j * length,
                      voronoi.vertices[k] + dir_k * length]
        yield Polygon(np.concatenate((finite_part, extra_edge)))


def circleOverlaps(circleArray):
    prec = circleArray[0].prec
    for circle in circleArray:
        if circle.prec != prec:
            return -1
        
    for circle1 in circleArray:
        origin1 = np.array([circle1.x, circle1.y])
        j = 0
        for circle2 in circleArray:
            overlap = []
            if circle1 == circle2:
                j = j + 1
                continue
            origin2 = np.array([circle2.x, circle2.y])
            # get overlap
            for i in range(0, len(circle1.xUnits)):
                point = np.array([circle1.xUnits[i], circle1.yUnits[i]])
                
                dist = np.linalg.norm(point - origin1)
                dist2 = np.linalg.norm(point - origin2)
                if dist > dist2:
                    overlap.append(i)
                    
            circle1.removeOverlaps(overlap, circle2)
            circle1.intersects(circle2)
            j = j + 1
                        
    return circleArray


def closestMiddlePoint(circle1, circle2, circle3):
    p0 = [circle1.x, circle1.y]
    p1 = [circle2.x, circle2.y]
    p2 = [circle3.x, circle3.y]
    
    a1 = 2*p1[0]-2*p0[0]
    b1 = 2*p1[1]-2*p0[1]
    a2 = 2*p2[0]-2*p0[0]
    b2 = 2*p2[1]-2*p0[1]
    
    p012 = p0[0]**2+p0[1]**2-p1[0]**2-p1[1]**2
    p022 = p0[0]**2+p0[1]**2-p2[0]**2-p2[1]**2
    
    y = (-p012/a1 + p022/a2)/(b1/a1-b2/a2)
    x = -y*b1/a1 - p012/a1

    dist1 = np.linalg.norm(np.array([x,y]) - np.array([circle1.x, circle1.y]))
    dist2 = np.linalg.norm(np.array([x,y]) - np.array([circle2.x, circle2.y]))
    dist3 = np.linalg.norm(np.array([x,y]) - np.array([circle3.x, circle3.y]))

    return np.array([x,y])


def closestMiddlePointfromPoints(circle1, circle2, circle3, pointArray):
    for point in pointArray:
        dist1 = np.linalg.norm(np.array(point) - np.array(circle1.origin))
        dist2 = np.linalg.norm(np.array(point) - np.array(circle2.origin))
        dist3 = np.linalg.norm(np.array(point) - np.array(circle3.origin))
        if fNearEqual(dist1, dist2) and fNearEqual(dist1, dist3):
            return point
    return None

def fNearEqual(val1, val2, prec = 0.00001):        
    if math.fabs(val1 - val2) <  prec:
        return True
    return False


def pointsNearEqual(point1, point2, prec = 0.00001):
    if math.fabs(point1[0] - point2[0]) <  prec and math.fabs(point1[1] - point2[1]) <  prec:
        return True
    return False


def pointInArray(arr, point):
    if len(arr) > 0:
        for p1 in arr:
            if point[0] == p1[0] and point[1] == p1[1]:
                return True
    return False


class Circle2():
    def __init__(self, midX, midY, radius, precision):
        self.x = midX
        self.y = midY
        self.r = radius
        self.prec = precision
        self.broken = False
        self.origin = [midX,midY]

        # draw circle
        th = np.arange(0, 2*math.pi+self.prec, self.prec)
        xUnit = self.r * np.cos(th) + self.x;
        yUnit = self.r * np.sin(th) + self.y;
        
        self.xUnits = xUnit
        self.yUnits = yUnit
        
        self.points = []


class Circle():
    def __init__(self, circle, removed = []):
        self.x = circle.x
        self.y = circle.y
        self.r = circle.r
        self.prec = circle.prec
        self.broken = len(removed) > 0
        self.xUnits = circle.xUnits
        self.yUnits = circle.yUnits
        self.overlaps = []
        self.overlapPoints = []
        self.origin = np.array([self.x, self.y])

        self.removeOverlaps(removed, None)
        
        
        self.anchorPoints = []
        self.middlePoints = []

        self.paths = []
        
    def toPoints(self):
        for i in range(0, len(xUnits)):
            point = [xUnits[i], yUnits[i]]
            self.points.append(point) 
        
    def getAnchor(self, pMiddlePoints):
        for i in range(0, len(self.overlaps)):
            anchors = [];
            oPoints = self.overlapPoints[i]
            for point in oPoints:
                inOther = False
                theCircle = None
                for circle in self.overlaps:
                    if self.overlaps[i] == circle:
                        continue
                    if not self.closestPoint(point, self.overlaps[i]):
                        inOther = True
                        theCircle = circle
                        #mPoint = closestMiddlePoint(self, self.overlaps[i], circle)
                        mPoint = closestMiddlePointfromPoints(self, self.overlaps[i], circle, pMiddlePoints)
                        if mPoint is not None:
                            if self.closestPoint(mPoint, self.overlaps[i], circle) and self.inRadius(mPoint):
                                if not pointInArray(self.middlePoints, mPoint):
                                    self.middlePoints.append(mPoint)
                                    #anchors.append(mPoint)
                    
                if not inOther:
                    if not pointInArray(self.middlePoints, point):
                        anchors.append(point)
            if len(anchors) > 0:
                self.anchorPoints.append(anchors)

        for anchors in self.anchorPoints:               
            for point in anchors:
                if pointInArray(self.middlePoints, point):
                    continue
                self.addNearestPoint(point)  
                pass  
                
        for point in self.middlePoints:
            #self.addToNearestAnchorPoint(point)
            pass
                
    def addToNearestAnchorPoint(self, point):
        ind1 = np.argwhere(self.xUnits == point[0])
        ind2 = np.argwhere(self.yUnits == point[1])
        if ind1.size > 0 and ind1[0] == ind2[0]:
            return

        
        anch = []
        for anchor in self.anchorPoints:
            for p in anchor:
                if not p[0] == point[0] and not p[1] == point[1]:
                    ind1 = np.argwhere(self.xUnits == p[0])
                    ind2 = np.argwhere(self.yUnits == p[1])
                    if ind1.size > 0 and ind1[0] == ind2[0]:
                        anch.append(p)
        
        
        minDist = math.inf
        min = -1
        for i in range(0, len(anch)):
            dist = np.linalg.norm(point - anch[i])
            if dist < minDist:
                min = i
                minDist = dist
        
        minDist2 = math.inf
        min2 = -1
        for i in range(0, len(anch)):
            if i == min:
                continue
            dist = np.linalg.norm(point - anch[i])
            if dist < minDist2:
                min2 = i
                minDist2 = dist       
        
        ind = []
        ind1 = np.argwhere(self.xUnits == anch[min][0])
        ind2 = np.argwhere(self.yUnits == anch[min][1])
        if ind1.size > 0 and ind1[0] == ind2[0]:
            ind.append(ind1)
        ind1 = np.argwhere(self.xUnits == anch[min2][0])
        ind2 = np.argwhere(self.yUnits == anch[min2][1])
        if ind1.size > 0 and ind1[0] == ind2[0]:
            ind.append(ind1)
        
        i = int((ind[0] + ind[1])/2)+1
        self.xUnits = np.insert(self.xUnits, i, point[0])
        self.yUnits = np.insert(self.yUnits, i, point[1])
            
            
    def inRadius(self, point):
        dist = np.linalg.norm(np.array(point) - np.array([self.x, self.y]))
        if dist <= self.r:
            return True
        return False
    
    def closestPoint(self, point, circle1, circle2 = None):
        dist1 = np.linalg.norm(point - np.array([self.x, self.y]))
        for circle in self.overlaps:
            dist2 = np.linalg.norm(point - np.array([circle.x, circle.y]))
            if circle == circle1 or circle == circle2:
                # rounding errors
                if dist2-0.000001 < dist1:
                    continue
            if dist2 < dist1:
                return False
        return True
    

    def intersects(self, circle):
        x0 = self.x
        y0 = self.y
        r0 = self.r
        x1 = circle.x
        y1 = circle.y
        r1 = circle.r
             
        d = math.sqrt((x1-x0)**2 + (y1-y0)**2)
        
        # non intersecting
        if d > r0 + r1 :
            return None
        # One circle within other
        if d < abs(r0-r1):
            return None
        # coincident circles
        if d == 0 and r0 == r1:
            return None
        else:
            a=(r0**2-r1**2+d**2)/(2*d)
            h=math.sqrt(r0**2-a**2)
            x2=x0+a*(x1-x0)/d   
            y2=y0+a*(y1-y0)/d   
            x3=x2+h*(y1-y0)/d     
            y3=y2-h*(x1-x0)/d 
    
            x4=x2-h*(y1-y0)/d
            y4=y2+h*(x1-x0)/d
            
            p1 = np.array([x3,y3])
            p2 = np.array([x4,y4])

            self.overlapPoints.append([p1,p2])
            self.overlaps.append(circle)

        
    def removeOverlaps(self, removed, circle):
        # remove overlap points
        self.xUnits = np.delete(self.xUnits, removed)
        self.yUnits = np.delete(self.yUnits, removed)

    
    def addOverlapCircle(self, circle):
        isOverlapping = False
        for overlap in self.overlaps:
            if overlap == circle:
                isOverlapping = True
        if not isOverlapping:
            self.overlaps.append(circle)

    def countAnchorPoints(self):
        i = 0
        for anchor in self.anchorPoints:
            i = i + len(anchor)
        return i

    def addNearestPoint(self, point):
        ind = np.argwhere(self.xUnits == point[0])
        ind2 = np.argwhere(self.yUnits == point[1])

        if ind.size > 0 and ind2.size > 0 and ind[0] == ind2[0]:
            return
        
        minDist = math.inf
        min = -1
        for i in range(0, len(self.xUnits)):
            dist = np.linalg.norm(point - np.array([self.xUnits[i], self.yUnits[i]]))
            if dist < minDist:
                min = i
                minDist = dist
        
        if minDist == 0:
            return

        if min < len(self.xUnits)-1:
            p = np.array([self.xUnits[min-1], self.yUnits[min-1]])
            p2 = np.array([self.xUnits[min+1], self.yUnits[min+1]])
            p3 = np.array([self.xUnits[min], self.yUnits[min]])
   
            dist1 = np.linalg.norm(point - np.array([self.xUnits[min-1], self.yUnits[min-1]]))
            dist2 = np.linalg.norm(point - np.array([self.xUnits[min+1], self.yUnits[min+1]]))
            if dist1 < dist2:
                self.xUnits = np.insert(self.xUnits, min+1, point[0])
                self.yUnits = np.insert(self.yUnits, min+1, point[1])
                self.xUnits = rotate(self.xUnits, min+2)
                self.yUnits = rotate(self.yUnits, min+2)
            else:
                self.xUnits = np.insert(self.xUnits, min, point[0])
                self.yUnits = np.insert(self.yUnits, min, point[1])
                self.xUnits = rotate(self.xUnits, min)
                self.yUnits = rotate(self.yUnits, min)
        else:
            dist1 = np.linalg.norm(point - np.array([self.xUnits[min-1], self.yUnits[min-1]]))
            dist2 = np.linalg.norm(point - np.array([self.xUnits[0], self.yUnits[0]]))
            if dist1 < dist2:
                self.xUnits = np.insert(self.xUnits, 0, point[0])
                self.yUnits = np.insert(self.yUnits, 0, point[1])
                self.xUnits = rotate(self.xUnits, 1)
                self.yUnits = rotate(self.yUnits, 1)
            else:
                self.xUnits = np.insert(self.xUnits, min, point[0])
                self.yUnits = np.insert(self.yUnits, min, point[1])
                self.xUnits = rotate(self.xUnits, min)
                self.yUnits = rotate(self.yUnits, min)


def rotate(l, n):
    return np.append(l[n:], l[:n])


def sortPointArray(points):
    if len(points) == 0:
        return []
    sorted = [points[0]]
    del points[0]

    while len(points) > 0:
        minDist = math.inf
        min = -1
        
        for i in range(0,len(points)):
            dist = np.linalg.norm(np.array(sorted[-1]) - points[i])
            if dist < minDist:
                min = i
                minDist = dist

        if not points[min][0] == sorted[-1][0] and not points[min][1] == sorted[-1][1]:
            sorted.append(points[min])
        del points[min]
    
    return np.array(sorted)


def getAllAnchorPoints(circleArray):
    arr = []
    for circle in circleArray:
        for point in circle.anchorPoints:
            if len(point[0]) > 1:
                for p in point:
                    arr.append(p)
            else:
                arr.append(point)

    arr = sortPointArray(arr)
    return arr


def splitCircles(circleArray):
    cArray = []
    for circle in circleArray:
        cr = splitCircle(circle)
        for c in cr:
            cArray.append(c)
    return cArray


def splitCircle(circle):  
    if circle.countAnchorPoints() < 3:
        return [circle]
    
    circleArray = []
    indices = []
    for anch in circle.anchorPoints:
        for anchors in anch:
            ind = np.argwhere(circle.xUnits == anchors[0])
            ind2 = np.argwhere(circle.yUnits == anchors[1])
            if ind.size == 0 or ind2.size == 0:
                print("something went wrong: anchor not found")
                continue
            
            indArr = []
            indArr2 = []
            for point in ind:
                indArr.append(point[0])
            for point in ind:
                indArr2.append(point[0])
            
            ind = -1
            for val in indArr:
                for val2 in indArr2:
                    if val == val2:
                        ind = val

            indices.append(val)
    
    indices.sort()
    i = 0
    while i < len(indices):
        tmpCircle = Circle(circle)
        tmpCircle.xUnits = tmpCircle.xUnits[indices[i]:indices[i+1]+1]
        tmpCircle.yUnits = tmpCircle.yUnits[indices[i]:indices[i+1]+1]
        circleArray.append(tmpCircle)
        i = i + 2
    return circleArray


def removeBoundaryBox(ax, p, boundary_polygon, color, lineWidth):
    diameter = 2000
    xz, yz = zip(*boundary_polygon.exterior.coords)
    boundary_lines = splitToLines(xz, yz)
    try:    
        x, y = zip(*p.intersection(boundary_polygon).exterior.coords)
        
        voronoi_lines = splitToLines(x, y)
        for i in range(len(voronoi_lines)-1, -1, -1):
            for b_line in boundary_lines:
                if b_line.nearEqual(voronoi_lines[i]):
                    del voronoi_lines[i]
                    break

        for line in voronoi_lines:
            drawLine(ax, line, color, lineWidth)
    except:
        try:
            x, y = zip(*p.intersection(boundary_polygon).coords)
            ax.plot(x, y, color)
        except:
            noDraw = True


class Line():
    def __init__(self, point1, point2):
        self.start = point1
        self.end = point2

    def nearEqual(self, line):
        if math.fabs(self.start[0] - line.start[0]) < 0.0001 and math.fabs(self.start[1] - line.start[1]) < 0.0001:
            if math.fabs(self.end[0] - line.end[0]) < 0.0001 and math.fabs(self.end[1] - line.end[1]) < 0.0001:
                return True
        
        if math.fabs(self.end[0] - line.start[0]) < 0.0001 and math.fabs(self.end[1] - line.start[1]) < 0.0001:
            if math.fabs(self.start[0] - line.end[0]) < 0.0001 and math.fabs(self.start[1] - line.end[1]) < 0.0001:
                return True
        
        return False


def drawLine(ax, line, color, lineWidth):
    x = [line.start[0], line.end[0]]
    y = [line.start[1], line.end[1]]
    ax.plot(x, y, color = color, linewidth = lineWidth)


def drawCircle(ax, circle, color, lineWidth, markersize, color_centerpoints):   
    xUnit = circle.xUnits  
    yUnit = circle.yUnits

    if len(xUnit) == 0:
        return
    xUnit = np.append(xUnit, xUnit[0])
    yUnit = np.append(yUnit, yUnit[0])
    
    ''' draw center point '''
    points = np.array(circle.origin)
    ax.plot(*points.T, '+', markeredgewidth = markersize/3,  color = color_centerpoints, markersize = markersize)


    ax.plot(xUnit[:-1], yUnit[:-1], color = color, linewidth = lineWidth, markersize = markersize)
    
    if circle.countAnchorPoints() == 2 and len(circle.middlePoints) == 0:
        x = []
        y = []
        for anchors in circle.anchorPoints:
            for anch in circle.anchorPoints:
                for points in anch:
                    x.append(points[0])
                    y.append(points[1])
        ax.plot(x, y, color = color, linewidth = lineWidth, markersize = markersize)


def findBoundaryMatches(x, y, xz, yz):
    match = np.zeros((len(xz), len(x)))
    
    for i in range(0, len(xz)-1):
        for j in range(0,len(x)-1):
            if math.fabs(xz[i] - x[j]) < 0.00001 and math.fabs(yz[i] - y[j]) < 0.00001:
                 match[i,j] = 1


def splitToLines(x, y):
    lineArray = []
    for i in range(0, len(x)-1):
        point1 = [x[i], y[i]]
        point2 = [x[i+1], y[i+1]]
        line = Line(point1, point2)
        lineArray.append(line)
    return lineArray


def drawVoronoiInterior(ax, circleArray, color_centerpoints, color, lineWidth, markerSize):
    points = []
    for circle in circleArray:
        points.append(circle.origin)
    points = np.array(points)

    ax.plot(*points.T, '+', markeredgewidth = markerSize/3,  color = color_centerpoints, markersize = markerSize)
    
    diameter = 2000
    anchorPoints = getAllAnchorPoints(circleArray)
    if len(anchorPoints) <= 2:
        return

    boundary_polygon = Polygon(np.array(anchorPoints))
    xz, yz = zip(*boundary_polygon.exterior.coords)

    for p in voronoi_polygons(Voronoi(points), diameter):
        removeBoundaryBox(ax, p, boundary_polygon, color, lineWidth)


def drawLRVT(ax, circleArray, color, color_centerpoints, lineWidth, markersize, excludeCircles = []):
    points = []
    for circle in circleArray:
        points.append(circle.origin)
    points = np.array(points)
    
    circleArray = circleOverlaps(circleArray)
    for c in circleArray:
        c.getAnchor(Voronoi(points).vertices)
    
    drawVoronoiInterior(ax, circleArray, color_centerpoints, color, lineWidth, markersize)

    cArray = circleArray
    cArray = np.delete(circleArray, excludeCircles)
    cArray = splitCircles(cArray)
    for c in cArray:
        drawCircle(ax, c, color, lineWidth, markersize, color_centerpoints)


def drawLRVTfromPoints(ax, voronoiPoints, radius, lineWidth, color_bound, color_centerpoints, markerSize):   
    ''' get AOI circles '''
    circleArrayAll = []
    for points in voronoiPoints:
        c = Circle2(points[0], points[1], radius, math.pi/1000)
        c = Circle(c)
        circleArrayAll.append(c)

    ''' get connected components '''   
    connectedCircles = getConnectedCircles(circleArrayAll, radius)

    for circleArray in connectedCircles:
        ''' draw circles '''
        if len(circleArray) == 1:
            ''' draw single circle '''
            for c in circleArray:
                drawCircle(ax, c, color_bound, lineWidth, markerSize, color_centerpoints)
        elif len(circleArray) == 2:
            ''' draw two circles ''' 
            circleArray = circleOverlaps(circleArray)
            circleArray = splitCircles(circleArray)
            for c in circleArray:
                drawCircle(ax, c, color_bound, lineWidth, markerSize, color_centerpoints)
        else:
            ''' draw arbitrary amount of circles '''
            drawLRVT(ax, circleArray, color_bound, color_centerpoints, lineWidth, markerSize)

      
def getConnectedCircles(circleArray, radius):
    connected = []
    
    ''' dfs search for connected components '''
    component, ccounter = getComponents(circleArray, radius)
    
    ''' add circles to component list '''
    for i in range(0, ccounter+1):
        connected.append([])
    for i in range(0, len(circleArray)):
        connected[component[i]].append(circleArray[i])
    

    return connected
    
    
def getComponents(circleArray, radius):
    global component
    global ccounter
    
    ''' initialize '''
    ccounter = -1
    component = []
    for i in range(0, len(circleArray)):
        component.append(ccounter)
    
    
    ''' dfs search '''
    for i in range(0, len(circleArray)):
        if component[i] < 0:
            ccounter = ccounter + 1
            dfs(circleArray, i, radius)
    
    return component, ccounter
    

def dfs(circleArray, i, radius):
    global marker
    global component
    global ccounter

    component[i] = ccounter
    
    ''' iterate through neighbours '''
    circle = circleArray[i]
    for j in range(0, len(circleArray)):
        circ = circleArray[j]
        ''' check if neibhbour '''
        if np.linalg.norm(np.array(circle.origin) - np.array(circ.origin)) < radius * 2:
            if component[j] < 0:
                dfs(circleArray, j, radius)



    