from locust import HttpUser, TaskSet, task, between
#from requests_toolbelt.adapters.source import SourceAddressAdapter
from ssladapter_modified import SourceAddressAdapter
#from requests_toolbelt import SSLAdapter
import random
#import requests
import socket
import urllib3
urllib3.disable_warnings()

def get_ip(target):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect((target, 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# def login(self):
#     #ua = pick_ua()
#     self.client.get("/login.php", auth=("admin", "password"))

def pick_ua():
    ua1 = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"   ## human
    ua2 = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20100101 Firefox/29.0"   ## human
    ua3 = "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko"  ## human
    ua4 = "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"
    ua5 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"
    ua6 = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.61 Mobile Safari/537.36"
    ua7 = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/101.0.4951.58 Mobile/15E148 Safari/604.1"
    ua = [ua1, ua2, ua3, ua4, ua5, ua6, ua7]
    return(random.choice(ua))

def pick_ip():
    iplist = ["1.12.2.187","5.39.14.101","52.14.30.135", "67.223.120.87", "103.142.12.32", "109.237.177.16","142.214.161.165"]
    return(random.choice(iplist))

def build_headers():
    ua = pick_ua()
    ip = pick_ip()
    headers={'user-agent': ua, 'X-Forwarded-For' : ip}
    return(headers)
class avi_demo(HttpUser):
    def __init__(self, parent):
        super().__init__(parent)
        #print(self.locust.host)
    wait_time = between(1, 4)

    @task(100)
    def index(self):
        self.client.get("https://" + self.host + "/", headers=build_headers(), verify=False)

    @task(100)
    def httplogo(self):
        self.client.get("http://" + self.host + "/imgs/logo.png", headers=build_headers(), verify=False)

    @task(50)
    def conversion(self):
        self.client.get("https://" + self.host + "/imgs/conversion.js", headers=build_headers(), verify=False)

    @task(100)
    def header(self):
        self.client.get("https://" + self.host + "/imgs/header.png", headers=build_headers(), verify=False)

    # @task(1)
    # def avi_webm(self):
    #     ua = pick_ua()      
    #     self.client.get("https://" + self.locust.host + "/assets/avi.webm", headers={'user-agent': ua}, verify=False)

    @task(100)
    def textfile(self):
        self.client.get("https://" + self.host + "/128kb.txt", headers=build_headers(), verify=False)

    @task(100)
    def httpslogo(self):
        self.client.get("https://" + self.host + "/imgs/logo.png", headers=build_headers(), verify=False)


    def on_start(self):
        #ip = get_ip()
        ip = get_ip(self.host)
        print("tweaking mount")
        print(f"using IP {ip}")
        self.client.mount("https://", SourceAddressAdapter(ip))
        self.client.mount("http://", SourceAddressAdapter(ip))
        self.client.verify = False
        #login(self)

    # def on_stop(self):
    #     logout(self)


