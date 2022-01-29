import utils
import requests
import os
import random
import time
import json
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
        try:
            self.bark = dict['bark']
        except:
            self.bark=None
        self.loginurl = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username"
        self.jwsession = None
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
            self.sendNotify("❌ 登录失败，请检查账号信息","⏱️ 我在校园")
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
    def sendNotify(self,result,title):
        if (self.bark==None):
            return "bark通知失败"
        notifyToken = self.bark
        requests.adapters.DEFAULT_RETRIES = 5
        r = requests.session()
        req = "{}/{}/{}?icon=https://jwoss-static.wozaixiaoyuan.com/basicinfo/logo/21.png&sound=typewriters&group=InSchool".format(notifyToken, title, result)
        r.keep_alive = False
        try:
            r.get(req)
        except:
            print("消息经bark推送失败")
            return
        print("消息经bark推送成功")

if __name__=='__main__':
    userList =  utils.getData("InSchool")
    random.shuffle(userList)
    for dict in userList:
        name = dict['Zh_name']
        print('用户“{}”开始--------------------{}'.format(name,time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))))
        locals()[name] = WozaixiaoyuanPuncher(dict)
        locals()[name].login()
        print(f'用户{name}结束-----------------------\n')
