import json
import datetime
import time
import os
import pytz
import hashlib
import requests
import leancloud
leancloud.init(os.getenv('appid'),os.getenv('appkey'))
requests.adapters.DEFAULT_RETRIES = 5
r = requests.session()
r.keep_alive=False
def getAddress(lat,lng):
  AK=os.getenv("BD_AK")
  location = r.get(f'https://apis.map.qq.com/ws/coord/v1/translate?locations={lat},{lng}&type=1&key={AK}').json()
  lat=location['locations'][0]['lat']
  lng=location['locations'][0]['lng']
  result = r.get(f'https://apis.map.qq.com/ws/geocoder/v1/?location={lat},{lng}&poi_options=policy=4&key={AK}').json()
  results = result['result']['address_component']
  try:
    results['township'] = result['result']['address_reference']['town']['title']
  except:
    results['township'] = ''
  try:
    results['citycode'] = result['result']['ad_info']['city_code']
  except:
    results['citycode'] = ''
  del results['street_number']
  return results

def isEnabled(dict):
  try:
    if dict['status'] == 0:
      return False
  except:
    return False
  else:
    return True
def getData(sheet):
  timestamp = str(round(time.time() * 1000))
  resp = r.get(f'https://r5eeSMNI.api.lncldglobal.com/1.1/classes/{sheet}',headers={
  'X-LC-Id':os.getenv("appid"),
  'X-LC-Sign':md5( timestamp + os.getenv("appkey"))+","+timestamp},timeout=None).json()
  data_stream = resp['results']
  data_stream = list(filter(isEnabled, data_stream))
  return data_stream
def md5(str):
    m = hashlib.md5()
    m.update(str.encode("utf8"))
    #print(m.hexdigest())
    return m.hexdigest()
def getCurrentTime():
  return datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
def getCurrentHour():
  return datetime.datetime.now(pytz.timezone('Asia/Shanghai')).hour
def getCurrentMinute():
  return datetime.datetime.now(pytz.timezone('Asia/Shanghai')).minute
class processJson:
  def __init__(self,path):
    self.path = path

  def read(self):
    with open(self.path,'rb') as file:
        data = json.load(file)
    file.close()
    return data
  
  def write(self,data):
    with open(self.path,'w',encoding='utf-8') as file:   
        json.dump(data,file,ensure_ascii = False,indent = 2)
    file.close()
