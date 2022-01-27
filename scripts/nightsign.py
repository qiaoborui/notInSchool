import requests
import json
import hashlib
import os
import time
import utils
import random
import sys
from urllib.parse import urlencode
from urllib3.util import Retry
import urllib3
import functools
print = functools.partial(print, flush=True)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WozaixiaoyuanPuncher:
    def __init__(self,username,password,bark=None):
        self.username = username
        self.password = password
        self.bark = bark
        self.healthurl = "https://student.wozaixiaoyuan.com/health/save.json"
        self.sign_url="https://student.wozaixiaoyuan.com/sign/getSignMessage.json"
        self.heat_list_url = "https://student.wozaixiaoyuan.com/heat/getTodayHeatList.json"
        self.nightsignList = "https://student.wozaixiaoyuan.com/getMessage.json"
        self.nightsignurl = "https://student.wozaixiaoyuan.com/sign/doSign.json"
        self.loginurl = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username"
        self.heat_url = "https://student.wozaixiaoyuan.com/heat/save.json"
        self.jwsession = None
        self.sign_data = {
            "answers": '["0","0","1"]',
            "latitude": str(random.uniform(34.01085662841797,34.01085662841900)),
            "longitude": str(random.uniform(108.75390625,108.75390725)),
            "country": "中国",
            "city": "西安市",
            "district": "鄠邑区",
            "province": "陕西省",
            "township": "草堂街道",
            "street": "中心街",
        }
        self.headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.13(0x18000d32) NetType/WIFI Language/zh_CN miniProgram",
            "Content-Type": "application/json;charset=UTF-8",
            "Host": "gw.wozaixiaoyuan.com",
            "Accept-Language": "en-us,en",
            "Accept": "application/json, text/plain, */*"
        }
        self.heat_data = {
            "answers": '["0"]',
            "seq": "1",
            "temperature": str(round(random.uniform(36.0,36.7),1)),
            "latitude": str(random.uniform(34.01085662841797,34.01085662841900)),
            "longitude": str(random.uniform(108.75390625,108.75390725)),
            "country": "中国",
            "city": "西安市",
            "district": "鄠邑区",
            "province": "陕西省",
            "township": "草堂街道",
            "street": "中心街",
        }
        self.nightData ={#id,signid
            "latitude": str(random.uniform(34.01085662841797,34.01085662841900)),
            "longitude":str(random.uniform(108.75390625,108.75390725)) ,
            "country": "中国",
            "city": "西安市",
            "district": "鄠邑区",
            "province": "陕西省",
            "township": "草堂街道",
            "street": "中心街"}
        self.body="{}"
    def login(self):
        username, password = str(self.username), str(self.password)
        url = f'https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username?username={username}&password={password}'
        self.session = requests.session()
        # 登录
        #print(url)
        response = self.session.post(url=url, data=self.body, headers=self.headers)
        res = json.loads(response.text)
        if res["code"] == 0:
            print("使用账号信息登录成功")
            jwsession = response.headers['JWSESSION']
            self.setJwsession(jwsession)
            return True
        else:
            print(res)
            print(username)
            print("登录失败，请检查账号信息")
            self.sendNotify("❌ 打卡失败，登录错误，请检查账号信息","⏱️ 我在校园")
            return False
    def setJwsession(self, jwsession):
        # 如果找不到cache,新建cache储存目录与文件
        if not os.path.exists('.cache'):
            print("正在创建cache储存目录与文件...")
            os.mkdir('.cache')
            data = {"jwsession": jwsession}
        if not os.path.exists(f'.cache/{self.username}_cache.json'):
            print("正在创建cache文件...")
            data = {"jwsession": jwsession}
        # 如果找到cache,读取cache并更新jwsession
        else:
            print("找到cache文件，正在更新cache中的jwsession...")
            data = utils.processJson(f'.cache/{self.username}_cache.json').read()
            data['jwsession'] = jwsession
        utils.processJson(f'.cache/{self.username}_cache.json').write(data)
        self.jwsession = data['jwsession']

    def getJwsession(self):
        if not self.jwsession:  # 读取cache中的配置文件
            data = utils.processJson(f'.cache/{self.username}_cache.json').read()
            self.jwsession = data['jwsession']
        return self.jwsession

    def sendNotify(self,result,title):
        if (self.bark==None):
            return "bark通知失败"
        notifyToken = self.bark
        requests.adapters.DEFAULT_RETRIES = 5
        r = requests.session()
        req = "{}/{}/{}?icon=https://jwoss-static.wozaixiaoyuan.com/basicinfo/logo/21.png&sound=choo&group=InSchool".format(notifyToken, title, result)
        r.keep_alive = False
        try:
            r.get(req)
        except:
            print("消息经bark推送失败")
            return
        print("消息经bark推送成功")

    def DoSign(self,id,signid):
        url = self.nightsignurl
        data =self.nightData
        self.headers['JWSESSION']=self.getJwsession()
        self.headers['Content-Type']="application/json"
        data['id']=id
        data['signid']=signid
        try:
            r = requests.post(url, data = json.dumps(data,ensure_ascii=False).encode("utf-8").decode("latin1"), headers = self.headers, verify = False).json()
        except Exception as e:
            print('Error:'+str(e))
            self.sendNotify("签到失败,请求错误","⏰ 我在校园晚签结果通知")
            return
        if r["code"] != 0:
            print("签到失败:"+str(r["code"]))
            self.sendNotify("签到失败,服务端错误","⏰ 我在校园晚签结果通知")
            return
        print("签到成功")
        self.sendNotify("签到成功","⏰ 我在校园晚签结果通知")
        return
	
    def AutoSign(self):
        print("自动签到:")
        url = self.nightsignList
        self.headers['JWSESSION'] = self.getJwsession()
        self.headers['Host']="student.wozaixiaoyuan.com"
        self.headers['Content-Type']="application/x-www-form-urlencoded"
        #print(self.headers)
        headers = {
            "JWESSION":self.getJwsession()
        }
        try:
            r = requests.post(url, headers = self.headers, verify = False).json()
        except Exception as e:
            print('Error:'+str(e))
            return
        if r["code"] == -10:
            print(r)
            print('Jwsession失效，将尝试重新登陆')
            loginStatus = self.login()
            if loginStatus:
                self.AutoSign()
            else:
                print(r)
                self.sendNotify("❌ 打卡失败，登录错误，请检查账号信息","⏰ 我在校园晚签结果通知")
                print("重新登陆失败，检查账号信息")
                return 
        elif r["code"] != 0:
            print("获取未读消息失败:"+str(r["code"]))
            return
        elif r["data"]["sign"] == 0:
            print("没有未完成的签到...")
            return
        url = self.sign_url
        data = {'page':"1",'size':"5"}
        try:
            r = requests.session().post(url, data = data,headers = self.headers, verify = False).json()
            #print(r)
        except Exception as e:
            print('Error:'+str(e))
            return
        if r["code"] != 0:
            print("获取签到信息失败:"+str(r["code"]))
            return
        AllSigns = r["data"]
        for Sign in AllSigns:
            if Sign["state"] == 1 and Sign["type"] == 0 : # 新签到
                self.DoSign(str(Sign["logId"]),str(Sign["id"]))
            elif Sign["state"] == 2 and Sign["type"] == 0 : # 补签
                self.DoSign(str(Sign["logId"]),str(Sign["id"]))
        print("所有签到处理完毕")
        #self.sendNotify("所有签到处理完毕","⏰ 我在校园晚签结果通知")
        return
    def doPunchIn(self):
        url = self.healthurl
        del self.headers['Host']
        self.headers['Content-Type'] = "application/x-www-form-urlencoded"
        self.headers['JWSESSION'] = self.getJwsession()
        sign_data=self.sign_data
        data = urlencode(sign_data)
        self.session = requests.session()
        response = self.session.post(url=url, data=data, headers=self.headers)
        response = json.loads(response.text)
        # 打卡情况        
        # 如果 jwsession 无效，则重新 登录 + 打卡
        if response['code'] == -10:
            print(response)
            print('jwsession 无效，将尝试使用账号信息重新登录')
            loginStatus = self.login()
            if loginStatus:
                self.doPunchIn()
            else:
                print(response)
                print("重新登录失败，请检查账号信息")
                self.sendNotify("❌ 打卡失败，登录错误，请检查账号信息","⏰ 我在校园健康打卡结果通知")

        elif response["code"] == 0:
            self.sendNotify("✅ 打卡成功","⏰ 我在校园打卡（健康打卡）结果通知")
            print("打卡成功")
        elif response['code'] == 1:
            self.sendNotify("❌ 打卡失败，当前不在打卡时间段内","⏰ 我在校园打卡（健康打卡）结果通知")
            print("打卡失败：今日健康打卡已结束")
            self.status_code = 3
        else:
            self.sendNotify("❌ 打卡失败，未知原因","⏰ 我在校园打卡（健康打卡）结果通知")
            print("打卡失败")
    
    def dailyCheck(self):
        print("获取打卡列表中...")
        url = self.heat_list_url
        self.headers['Host'] = "student.wozaixiaoyuan.com"
        self.headers['JWSESSION'] = self.getJwsession()
        self.session = requests.session()
        response = self.session.post(url=url, data=self.body, headers=self.headers)
        res = json.loads(response.text)
        # 如果 jwsession 无效，则重新 登录 + 打卡
        if res['code'] == -10:
            print(res)
            print('jwsession 无效，将尝试使用账号信息重新登录')
            loginStatus = self.login()
            if loginStatus:
                self.PunchIn()
            else:
                print(res)
                print("重新登录失败，请检查账号信息") 
                self.sendNotify("❌ 打卡失败，登录错误，请检查账号信息","⏰ 我在校园（日检日报）结果通知")    
        elif res['code'] == 0:                    
            # 标志时段是否有效
            inSeq = False
            # 遍历每个打卡时段（不同学校的打卡时段数量可能不一样）
            for i in res['data']:
                # 判断时段是否有效
                if int(i['state']) == 1:
                    inSeq = True
                    # 保存当前学校的打卡时段
                    self.seq = int(i['seq'])
                    # 判断是否已经打卡
                    if int(i['type']) == 0:
                        self.execdoPunchIn()
                    elif int(i['type']) == 1:
                        print("已经打过卡了")
            # 如果当前时间不在任何一个打卡时段内
            if inSeq == False:            
                print("打卡失败：不在打卡时间段内")
            self.sendNotify("❌ 不在任意打卡时间段","⏰ 我在校园（日检日报）结果通知") 
    def execdoPunchIn(self):
        url = self.heat_url
        self.headers['Host'] = "student.wozaixiaoyuan.com"
        self.headers['Content-Type'] = "application/x-www-form-urlencoded"
        self.headers['JWSESSION'] = self.getJwsession()
        sign_data = self.heat_data
        data = urlencode(sign_data)
        self.session = requests.session()    
        response = self.session.post(url=url, data=data, headers=self.headers)
        response = json.loads(response.text)
        # 打卡情况
        if response["code"] == 0:
            self.status_code = 1
            print("打卡成功")
            self.sendNotify("✅ 打卡成功","⏰ 我在校园打卡（日检日报）结果通知")
        else:
            print(response)
            print("打卡失败")
            self.sendNotify("❌ 打卡失败","⏰ 我在校园(日检日报)结果通知") 

def md5(str):
    m = hashlib.md5()
    m.update(str.encode("utf8"))
    #print(m.hexdigest())
    return m.hexdigest()

def main():
    timestamp = str(round(time.time() * 1000))
    r = requests.get("https://r5eeSMNI.api.lncldglobal.com/1.1/classes/InSchool",headers={
    'X-LC-Id':os.getenv('appid'),
    'X-LC-Sign':md5( timestamp + os.getenv('appkey') )+","+timestamp},timeout=None).json()
    userList = r['results']
    random.shuffle(userList)
    for dict in userList:
        try:
            status = dict['status']
        except:
            status = 1
        if status==0:
            continue
        name = dict['Zh_name']
        print('用户“{}”开始--------------------{}'.format(name,time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))))
        try:
            start = dict['start']
            end = dict['end']
        except:
            start=0
            end=59
        minute = utils.getCurrentMinute()
        try:
            dict['bark']
        except:
            locals()[name] = WozaixiaoyuanPuncher(dict['username'],dict['passwd'])
        else:
            locals()[name] = WozaixiaoyuanPuncher(dict['username'],dict['passwd'],dict['bark'])
        username = dict['username']
        if not os.path.exists(f'.cache/{username}_cache.json'):
            print ("找不到cache文件，正在使用账号信息登录...")
            loginStatus = locals()[name].login()
            if loginStatus:
                locals()[name].AutoSign()
            else:
                print("登陆失败，请检查账号信息")
        else:
            print("找到cache文件，尝试使用jwsession打卡...")
            locals()[name].AutoSign()
        print(f'用户{name}结束-----------------------\n')
        time.sleep(round(random.uniform(1.0,6.0),1))
main()
