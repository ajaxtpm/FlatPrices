from scipy import interpolate
from PIL import Image
import urllib
import sqlite3
import os
import sys
import pprint
import collections
import math
from werkzeug import datastructures
import numpy as np
import matplotlib.pyplot as plt
import pylab as py
import field
import multiprocessing

img_name_postfix = ".png"
prices_img_name = 'prices'+img_name_postfix
map_img_name = 'map'+img_name_postfix
result_img_name = 'result'+img_name_postfix
border = 2000000
action = 'interpolation'
# run as >python interpolate.py border_value [field|interpolation]
if len(sys.argv) > 1:
    border = int(sys.argv[1])
else:
    border = 400000
if len(sys.argv) > 2:
    action = sys.argv[2]
print '[*] Border =',str(border)
show_points = True

left = 37.320
right = 37.87
bottom = 55.607
top = 55.917

def interpolation(tdic):
    print '[+] starting linear interpolation'
    unique_lat = [x[1][0] for x in tdic.keys()]
    unique_lng = [x[0][0] for x in tdic.keys()]
    unique_price = [tdic[x] for x in tdic.keys()]
    print '[*] finished data processing'

    f = interpolate.LinearNDInterpolator((unique_lng, unique_lat), unique_price)
    print '[*] succesfully interpolated'

    #print '[*] interpolation error =',max(f(unique_lng, unique_lat) - unique_price)
    print '[*] drawing image'
    print '[*] latitude', str(bottom)+'...'+str(top)
    print '[*] longtitude', str(left)+'...'+str(right)

    xx, yy = np.mgrid[left:right:400j, bottom:top:400j]
    zz = f(xx, yy)
    zz = np.array(map(lambda x: map(lambda y: int(2*(0.956657*math.log(y) - 10.6288)) , x), zz)) #HARD    
    #zz = np.array(map(lambda x: map(lambda y: int(2*(0.708516*math.log(y) - 7.12526)) , x), zz)) #MEDIUM  
    #zz = np.array(map(lambda x: map(lambda y: int(2*(0.568065*math.log(y) - 5.10212)) , x), zz))#LOW     
    zz = np.array(map(lambda x: map(lambda y: 0 if y < 0. else y , x), zz))
    zz = zz.max() - zz

    plt.ioff()
    fig = plt.figure(1, figsize=(4,4))
    plt.scatter(xx,yy,10,zz,cmap=py.cm.RdYlGn, edgecolors='none')
    if show_points:
        for i in tdic.keys():
            if i[0][0] > left and i[0][0] < right and i[1][0] > bottom and i[1][0] < top:
                plt.plot(i[0][0], i[1][0], 'bo', markersize=2,markeredgecolor = 'none')
    plt.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    plt.axis([left,right,bottom,top])
    plt.savefig(prices_img_name, dpi=100, transparent=True)
    print '[*] saved prices map on disc as '+prices_img_name

def fieldinterpolation(tdic):
    print '[+] starting field calculation'
    dictdict = dict()
    for key in tdic.keys():
        if key[0][0] not in tdic.keys():
            dictdict[key[0][0]] = dict()
        dictdict[key[0][0]][key[1][0]] = tdic[key]
    print '[*] latitude', str(bottom)+'...'+str(top)
    print '[*] longtitude', str(left)+'...'+str(right)
    xx, yy = np.mgrid[left:right:60j, bottom:top:60j]
    
    dic = dict((key, tdic[key]) for key in tdic.keys() if tdic[key] < border )
    filtered_dic = dict((key, tdic[key]) for key in tdic.keys() if tdic[key] >= border )


    zz = field.fieldInterpolation((xx, yy, dictdict, border))

    plt.ioff()
    fig = plt.figure(1, figsize=(4,4))
    #plt.scatter(xx,yy,10,zz,cmap=py.cm.RdYlGn, edgecolors='none')
    for i in range(len(zz)):
        for j in range(len(zz[i])):
            if zz[i][z] > 0:
                plt.plot(xx[i][j], yy[i][j], 'bo', markersize=2,markeredgecolor = 'none')
            else:
                plt.plot(xx[i][j], yy[i][j], 'bo', markersize=2,markeredgecolor = 'none')
    if show_points:
        for i in filtered_dic.keys():
            if i[0][0] > left and i[0][0] < right and i[1][0] > bottom and i[1][0] < top:
                plt.plot(i[0][0], i[1][0], 'go', markersize=2,markeredgecolor = 'none')
        for i in dic.keys():
            if i[0][0] > left and i[0][0] < right and i[1][0] > bottom and i[1][0] < top:
                plt.plot(i[0][0], i[1][0], 'bo', markersize=2,markeredgecolor = 'none')
    plt.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    plt.axis([left,right,bottom,top])
    plt.savefig(prices_img_name, dpi=100, transparent=True)
    os.system('"C:\Program Files (x86)\IrfanView\i_view32.exe" '+ prices_img_name +' /effect=(6,7,0) /convert=' + prices_img_name)
    print '[*] saved prices map on disc as '+prices_img_name


lat = lng = price = []
db_paths = [os.getcwd()+'\\flats_metres.db', os.getcwd()+'\\flats_metres_sob.db']
for db_path in db_paths:
    print '\n[*] reading db at '+db_path
    db = sqlite3.connect(db_path)
    cursor = db.cursor()

    tables = cursor.execute('SELECT name FROM sqlite_master').fetchall()
    for table in tables:
        table_name = table[0]
        print '[*] fetching data from '+table_name
        price = price + cursor.execute('SELECT price FROM '+table_name+' WHERE price < 12000000').fetchall()
        lat = lat + cursor.execute('SELECT lat FROM '+table_name+' WHERE price < 12000000').fetchall()
        lng = lng + cursor.execute('SELECT lng FROM '+table_name+' WHERE price < 12000000').fetchall()
print '[*] finished db reading\n'


print '[*] starting data processing: averaging price by same addresses'
md = datastructures.MultiDict(map(lambda i: ((lng[i], lat[i]), price[i]), range(len(lat))))
tdic = dict((key, sum([x[0] for x in md.getlist(key)])/len(md.getlist(key))) for key in md.keys() )

if action == 'interpolation':
    interpolation(tdic)
else:
    fieldinterpolation(tdic)

ya_map_string = 'http://static-maps.yandex.ru/1.x/?ll=37.5946002,55.7622764&spn=0.25,0.25&size=400,400&l=map'

"""
ya_map_string = 'http://static-maps.yandex.ru/1.x/?ll='+str(center_lng)+','+str(center_lat)+'&spn='+str(mx*diameterx)+','+str(my*diametery)+'&size=400,400&l=map'
if False:
    ya_map_string = ya_map_string + '&pt='
    for i in filtered_dic.keys():
        print "Filtered coordinates (lng, lat): "+str(i)
        ya_map_string = ya_map_string + str(i[0][0]) + ',' + str(i[1][0]) + ',pm2rdm~'
    ya_map_string = ya_map_string[:-1]
"""

print '[*]',ya_map_string
urllib.urlretrieve(ya_map_string, map_img_name)
print '[*] saved yandex map on disc as '+map_img_name

print '[*] combining images'
map_img = Image.open(map_img_name, 'r').convert('RGBA')
map_w, map_h = map_img.size
price_img = Image.open(prices_img_name, 'r').convert('RGBA')
price_w, price_h = price_img.size
if map_w == price_w and map_h == price_h:
    result_img = Image.blend(map_img, price_img, 0.5)
    result_img.show()
    result_img.save(result_img_name)
    print '[*] save result as',result_img_name
else:
    print '[!] prices and yandex map sized do not equals. prices ('+str(price_w)+','+str(price_h)+'), yandex ('+str(map_w)+','+str(map_h)+')'