from scipy import interpolate
from PIL import Image
import urllib
import sqlite3
import os
import pprint
import collections
import math
from werkzeug import datastructures
import numpy as np

def fieldInterpolation(args):
    (xx, yy, parts, border) = args
    windowx = 0.11/2.
    windowy = 0.08/2.

    res = []
    if len(xx) != len(yy):
        return res
    for i in range(len(xx)):
        print "[!] Row",str(i)
        row = []
        for j in range(len(xx)):
            currx = xx[i][j]
            curry = yy[i][j]
            force = 0.
            for key1 in filter(lambda x: x > currx - windowx and x < currx + windowx, parts.keys()):
                for key2 in filter(lambda x: x > curry - windowy and x < curry + windowy, parts[key1].keys()):
                    module = 0.00185 / ((currx - key1)**2 + (curry - key2)**2)
                    if parts[key1][key2] < border:
                        force = force + module
                    else:
                        force = force - module
            if force >= 0.:
                row.append(1.)
            else:
                row.append(-1.)
        res.append(row)
    return res
    