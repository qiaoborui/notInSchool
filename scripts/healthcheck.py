import requests
import json
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
    def __init__(self,dict):
        self.username = dict['username']
        self.password = dict['passwd']
        self.lc=utils.leancloud.Query('InSchool').equal_to("username",self.username).first()
        try:
            self.bark = dict['bark']
        except:
            self.bark = None
        self.times=0
        self.log=float(dict['log'])
        self.lat=float(dict['lat'])
        add = utils.getAddress(self.lat,self.log)
        self.healthurl = "https://student.wozaixiaoyuan.com/health/save.json"
        self.loginurl = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username"
        self.jwsession = None
        self.sign_data = {
            "answers": '["0","0","1"]',
            "latitude": str(random.uniform(self.lat-0.0003,self.lat+0.0003)),
            "longitude": str(random.uniform(self.log-0.0003,self.log+0.0003)),
            "country": "中国",
            "city": add['city'],
            "district":add['district'],
            "province": add['province'],
            "township": add['township'],
            "street":add['street']
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
        self.body="{}"
    def login(self):
        username, password = str(self.username), str(self.password)
        url = f'{self.loginurl}?username={username}&password={password}'
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
        """# 如果找不到cache,新建cache储存目录与文件
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
        self.jwsession = data['jwsession']"""
        self.lc.set("cache",jwsession)
        self.lc.save()
        self.jwsession = jwsession

    def getJwsession(self):
        if not self.jwsession:  # 读取cache中的配置文件
            data = self.lc.get("cache")
            self.jwsession = data
        return self.jwsession

    def sendNotify(self,result,title):
        if (self.bark==None):
            return "bark通知失败"
        notifyToken = self.bark
        requests.adapters.DEFAULT_RETRIES = 5
        r = requests.session()
        req = "{}/{}/{}?icon=https://jwoss-static.wozaixiaoyuan.com/basicinfo/logo/21.png&sound=minuet&group=InSchool".format(notifyToken, title, result)
        r.keep_alive = False
        try:
            r.get(req)
        except:
            print("消息经bark推送失败")
            return
        print("消息经bark推送成功")

    def doPunchIn(self):
        url = self.healthurl
        try:
            del self.headers['Host']
        except:
            pass
        self.headers['Content-Type'] = "application/x-www-form-urlencoded"
        self.headers['JWSESSION'] = self.getJwsession()
        sign_data=self.sign_data
        data = urlencode(sign_data)
        print(sign_data)
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
            self.times+=1
            self.sendNotify("❌ 打卡失败，未知原因","⏰ 我在校园打卡（健康打卡）结果通知")
            if(self.times<=1):
                self.doPunchIn()
                self.sendNotify("❌ 打卡失败，未知原因，正在重试","⏰ 我在校园打卡（健康打卡）结果通知")
                print("重试ing")
            print("打卡失败")


if __name__=='__main__':
    userList = utils.getData("InSchool")
    random.shuffle(userList)
    for dict in userList:
        name = dict['Zh_name']
        print('用户“{}”开始--------------------{}'.format(name,time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))))
        locals()[name] = WozaixiaoyuanPuncher(dict)
        """if not os.path.exists(f'.cache/{username}_cache.json'):
            print ("找不到cache文件，正在使用账号信息登录...")
            loginStatus = locals()[name].login()
            if loginStatus:
                locals()[name].doPunchIn()
            else:
                print("登陆失败，请检查账号信息")
        else:
            print("找到cache文件，尝试使用jwsession打卡...")
            locals()[name].doPunchIn()"""
        try:
            dict['cache']
            print("找到cache文件，尝试使用jwsession打卡...")
            locals()[name].doPunchIn()
        except:
            print ("找不到cache文件，正在使用账号信息登录...")
            loginStatus = locals()[name].login()
            if loginStatus:
                locals()[name].doPunchIn()
            else:
                print("登陆失败，请检查账号信息")


        print(f'用户{name}结束-----------------------\n')
        time.sleep(round(random.uniform(1.0,6.0),1))
