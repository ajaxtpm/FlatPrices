# -*- coding: utf-8 -*- 
import urllib2
import json 
import pprint
import time
import sqlite3
import os

debug = 0
districts = ['taldomskiy-r-n', 'sergievo-posadskiy-r-n', 'lotoshinskiy-r-n', 'klinskiy-r-n', 'dmitrovskiy-r-n', 'solnechnogorskiy-r-n', 'pushkinskiy-r-n', 'myitischinskiy-r-n', 'volokolamskiy-r-n', 'shahovskoy-r-n', 'istrinskiy-r-n', 'himki-gor-okrug', 'pavlovo-posadskiy-r-n', 'krasnogorskiy-r-n', 'schelkovskiy-r-n', 'ruzskiy-r-n', 'balashiha-gor-okrug', 'noginskiy-r-n', 'odintsovskiy-r-n', 'lyuberetskiy-r-n', 'orehovo-zuevskiy-r-n', 'naro-fominskiy-r-n', 'mojayskiy-r-n', 'leninskiy-r-n', 'podolskiy-r-n', 'ramenskiy-r-n', 'voskresenskiy-r-n', 'egorevskiy-r-n', 'shaturskiy-r-n', 'chehovskiy-r-n', 'domodedovo-gor-okrug', 'stupinskiy-r-n', 'kolomenskiy-r-n', 'serpuhovskiy-r-n', 'ozerskiy-r-n', 'luhovitskiy-r-n', 'kashirskiy-r-n', 'zarayskiy-r-n', 'serebryano-prudskiy-r-n']

def get_sob_url(district, page):
    return r'http://sob.ru/prodazha-kvartir-moskovskaya-oblast/'+districts[district]+'?page='+str(page)

def parse_sob_page(page_address):
    price_prologue=u"<div class=\"b-cardList__item-info-right\">\n                                <p>"
    price_epilogue=u" <span>Р</span></p>"
    square_prologue=u"<p>Площадь: "
    square_epilogue=u" м&sup2;</p>"
    location_prologue=u"<a href=\"#\" onclick=\"$(map).data('map').show("
    location_epilogue=u"); return false;\">"
    
    i = 0
    result = []
    response = urllib2.urlopen(page_address)
    html = response.read().decode('utf-8')
    
    if debug:
        print "[*] searching for 1st entry"
    
    begin_index = html.find(price_prologue)
    
    
    if begin_index == -1:
        print "[!] failed to find 1st entry"
        return result;
        
    if debug:
        print "[*] found 1st entry"
    html = html[begin_index:]
    
    while begin_index >= 0:
        if debug:
            print "\n[+] starting with "+str(i)+"st entry"
            
        #getting price
        begin_index = html.find(price_prologue)
        end_index = html.find(price_epilogue)
        if begin_index >= 0 and end_index >= begin_index:
            money_string = html[begin_index+len(price_prologue):end_index].strip().replace(' ','')
            if debug:
                print "[+] found price"
                print "[+] "+str(money_string)
            html = html[end_index+len(price_epilogue):]
        else:
            continue
        
        #getting area   
        begin_index = html.find(square_prologue)
        end_index = html.find(square_epilogue)
        if begin_index >= 0 and end_index >= begin_index:
            area = html[begin_index+len(square_prologue):end_index]
            if len(area) <= 0 or len(area) > 4:
                if debug:
                    print '[!] wrong area for location above'
                continue
            if debug:
                print "[+] found area"
                print "[+] "+area
            html = html[end_index+len(square_epilogue):]
        else:
            continue
        
        #getting location
        begin_index = html.find(location_prologue)
        
        if html[:begin_index].find(price_prologue) >= 0:
            if debug:
                print '[!] no location for price above'
            continue
            
        end_index = html.find(location_epilogue)
        if begin_index >= 0 and end_index >= begin_index:
            location_string = html[begin_index+len(location_prologue):end_index].strip()
            if debug:
                print "[+] found location"
                print "[+] "+location_string
            html = html[end_index+len(location_epilogue):]
        else:
            continue
        
        if len(money_string) > 0 and len(location_string) > 0 and len(area) > 0:
            #print '[*] price str: <'+money_string+'>  area str: <'+area+'>'
            square_metre = str(round(int(money_string)/float(area)))
            result.append([location_string, square_metre])

        i = i+1
        begin_index = html.find(price_prologue)
    return result

table_name = r'flats'
db_path = os.getcwd()+'\\flats_metres_sob.db'
print '[*] creating db at '+db_path
db = sqlite3.connect(db_path)
cursor = db.cursor()
tables = cursor.execute('SELECT name FROM sqlite_master').fetchall()
table_name = table_name + str(len(tables) + 1)
print '[*] creating table with name '+table_name

cursor.execute('CREATE TABLE '+table_name+' (lat real, lng real, price integer)')
db.commit()

total = []
for d in range(len(districts)):
    result = [1]
    i = 1
    while len(result) > 0 and i < 25:
        url = get_sob_url(d,i)
        print "\n[*] starting with "+url
        result = parse_sob_page(url)
        if result == []:
            print '[!] got no result'
        else:
            for pair in result:
                location = []
                try:
                    location = eval(pair[0])
                except Exception:
                    print '[!] could not parse location '+pair[0]
                if location != []:
                    cursor.execute('INSERT INTO '+table_name+' VALUES (?,?,?)', (location[0], location[1], pair[1]))
                    print pair[0]+': '+pair[1]
            db.commit()
        i = i + 1