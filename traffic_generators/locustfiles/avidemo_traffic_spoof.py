from locust import HttpUser, TaskSet, task, between
#from requests_toolbelt.adapters.source import SourceAddressAdapter
from ssladapter_modified import SourceAddressAdapter
#from requests_toolbelt import SSLAdapter
import random
import requests
import urllib3
urllib3.disable_warnings()
import socket



# def login(self):
#     #ua = pick_ua()
#     self.client.get("/login.php", auth=("admin", "password"))

def pick_ua():
    ua1 = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
    ua2 = "Mozilla/5.0 (iPhone; CPU iPhone OS 5_1_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9B206 Safari/7534.48.3"
    ua3 = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20100101 Firefox/29.0"
    ua4 = "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko"
    ua5 = "Mozilla/5.0(iPad; U; CPU OS 4_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F191 Safari/6533.18.5"
    ua = [ua1, ua2, ua3, ua4, ua5]
    return(random.choice(ua))

class MyUser(HttpUser):
    def __init__(self, parent):
        super().__init__(parent)
        #print(self.locust.host)
    wait_time = between(1, 4)
    @task(100)
    def index(self):
        ua = pick_ua()
        self.client.get("https://" + self.host + "/", headers={'user-agent': ua}, verify=False)

    @task(100)
    def httplogo(self):
        ua = pick_ua()
        self.client.get("http://" + self.host + "/imgs/logo.png", headers={'user-agent': ua}, verify=False)

    @task(50)
    def conversion(self):
        ua = pick_ua()
        self.client.get("https://" + self.host + "/imgs/conversion.js", headers={'user-agent': ua}, verify=False)

    @task(100)
    def header(self):
        ua = pick_ua()
        self.client.get("https://" + self.host + "/imgs/header.png", headers={'user-agent': ua}, verify=False)

    # @task(1)
    # def avi_webm(self):
    #     ua = pick_ua()      
    #     self.client.get("https://" + self.locust.host + "/assets/avi.webm", headers={'user-agent': ua}, verify=False)

    @task(100)
    def textfile(self):
        ua = pick_ua()
        self.client.get("https://" + self.host + "/128kb.txt", headers={'user-agent': ua}, verify=False)

    @task(100)
    def httpslogo(self):
        ua = pick_ua()
        self.client.get("https://" + self.host + "/imgs/logo.png", headers={'user-agent': ua}, verify=False)

    def on_start(self):
        # List of IP's that can be used as "source" - hardcoded for simplicity
        ips = ["161.98.255.1", "37.60.63.2", "206.223.191.1", "23.26.110.2", "27.113.239.2", "42.97.255.1", "132.247.255.2", "14.192.95.1", "37.16.63.1", "49.213.31.2", "41.67.128.1", "27.97.1.2"]
        ip = random.choice(ips)

        print("tweaking mount")
        print(f"using IP {ip}")
        self.client.mount("https://", SourceAddressAdapter(ip))
        self.client.mount("http://", SourceAddressAdapter(ip))
        self.client.verify = False
        #login(self)

    # def on_stop(self):
    #     logout(self)

