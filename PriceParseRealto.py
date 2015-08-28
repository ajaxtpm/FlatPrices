# -*- coding: utf-8 -*- 
import urllib2
import json 
import pprint
import time
import sqlite3
import os

debug = 0

def get_moscow_realto_url(i):
    return r'http://www.realto.ru/base/flat_sale/?SecLodg_step='+str(i)+r'&page=3'

def parse_realto_page(page_address):
    i = 0
    result = []
    response = urllib2.urlopen(page_address)
    html = response.read().decode('cp1251')
    
    if debug:
        print "[*] searching for 1st entry"
        
    begin_index = html.find(r'<td class="base_td" align="right">')
    
    if begin_index == -1:
        print "[!] failed to find 1st entry"
        return;
        
    if debug:
        print "[*] found 1st entry"
    html = html[begin_index:]
    
    while begin_index >= 0:
        if debug:
            print "\n[+] starting with "+str(i)+"st entry"
        begin_index = html.find(ur'<td class="base_td" align="right">')
        end_index = html.find(u'руб')
        if begin_index >= 0 and end_index >= begin_index:
            money_string = html[begin_index+len(r'<td class="base_td" align="right">'):end_index].strip().replace('&nbsp;','').replace(' ','')
            rub_index = money_string.rfind('>')
            money_string = money_string[rub_index+1:]
            if debug:
                print "[+] found price"
                print "[+] "+str(money_string)
            html = html[end_index+len(ur'руб'):]
        else:
            continue
        
        begin_index = html.find(r'<td class="base_td">')
        end_index = html.find(r'</td>')
        if begin_index >= 0 and end_index >= begin_index:
            if debug:
                print "[+] found region"
            html = html[end_index+len(r'</td>'):]
            
        begin_index = html.find(r'<span style="font-size: 80%;">')
        end_index = html.find(r'</span>')
        if begin_index >= 0 and end_index >= begin_index:
            location_string = html[begin_index+len(r'<span style="font-size: 80%;">'):end_index].replace(r'&nbsp;','').strip()
            if len(location_string) <= 0 or begin_index > 400:
                if debug:
                    print '[!] no location for price above'
                continue
            if debug:
                print "[+] found location"
                print "[+] "+location_string
            #print '[!] begin:',str(begin_index)+'   end:',str(end_index)
            html = html[end_index+len(r'</span>'):]
        else:
            continue
            
        begin_index = html.find(u'общая площадь - ')
        end_index = html.find(u' кв.м., ')
        if begin_index >= 0 and end_index >= begin_index:
            area = html[begin_index+len(u'общая площадь - '):end_index]
            if len(area) <= 0 or len(area) > 4:
                if debug:
                    print '[!] wrong area for location above'
                continue
            if debug:
                print "[+] found area"
                print "[+] "+area
            html = html[end_index+len(u' кв.м., '):]
        else:
            continue
        
        if len(money_string) > 0 and len(location_string) > 0 and len(area) > 0:
            #print '[*] price str: <'+money_string+'>  area str: <'+area+'>'
            square_metre = str(round(int(money_string)/float(area)))
            result.append([location_string, square_metre])

        i = i+1
        begin_index = html.find(r'<td class="base_td" align="right">')
    return result

def get_location(location_string):
    location_url = r'https://maps.google.com/maps/api/geocode/json?address='+(location_string+ur' Москва').replace(' ','+')+'&key={Your Key, Habravchanin}'
    if debug:
        print '[*] getting location for url'
        print '[*] '+location_url
    
    rate_limit_exceeded = False
    data = ''
    while True:
        response = urllib2.urlopen(location_url.encode('utf-8'))
        json_string = response.read()
        if len(json_string) < 10:
            print '[!] got incorrect response'
        data = json.loads(json_string)
        if data["status"] == "OVER_QUERY_LIMIT":
            print '[!] too many queries. need some sleep'
            time.sleep(1)
        else:
            data = data["results"]
            break
    
    if len(data) == 0:
        print '[!] got empty answer'
        print '[!] for location '+location_string
        print '[!] with url '+location_url
        return []
    if len(data) == 2:
        print '[*] got 2 answers'
        print '[*] trying resolve'
        if data[0]["formatted_address"] == data[0]["formatted_address"]:
            print '[*] hah, google have same instanses'
        else:    
            return []
    if len(data) > 2:
        print '[!] got',len(data),'answers'
        print '[!] for location '+location_string
        print '[!] with url '+location_url
        print '[*] getting 1st item'
    location = data[0]["geometry"]["location"];
    return [location["lat"], location["lng"]]

table_name = r'flats'
db_path = os.getcwd()+'\\flats_metres.db'
print '[*] creating db at '+db_path
db = sqlite3.connect(db_path)
cursor = db.cursor()
tables = cursor.execute('SELECT name FROM sqlite_master').fetchall()
table_name = table_name + str(len(tables) + 1)
print '[*] creating table with name '+table_name

cursor.execute('CREATE TABLE '+table_name+' (lat real, lng real, price integer)')
db.commit()

total = []
result = [1]
i = 0
while len(result) > 0:
    url = get_moscow_realto_url(i)
    print "\n[*] starting with "+url
    result = parse_realto_page(url)
    if result == None:
        break;
    for pair in result:
        location = get_location(pair[0])
        if len(location) > 0:
            cursor.execute('INSERT INTO '+table_name+' VALUES (?,?,?)', (location[0], location[1], pair[1]))
            print '['+str(location[0])+', '+str(location[1])+'] '+pair[0]+': '+pair[1]
        else:
            print '[!] wrong result'
        db.commit()
    #total = total + result
    i = i + 1

