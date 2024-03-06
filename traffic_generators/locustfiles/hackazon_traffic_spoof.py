from locust import HttpUser, TaskSet, task, between
#from requests_toolbelt.adapters.source import SourceAddressAdapter
from ssladapter_modified import SourceAddressAdapter
import random
import requests
import urllib3
urllib3.disable_warnings()




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
    wait_time = between(5, 9)


    def login(self):
        #ua = pick_ua()
        response = self.client.post("/user/login", data={'username': 'test_user', 'password': '123456'})
        print("login Response status code:", response.status_code)
    #    print("login Response text:", response.text)
        print(self.client.cookies)
        # print(self.client.headers)

    # def logout(l):
    #     l.client.post("/logout", {"username":"ellen_key", "password":"education"})

    @task(100)
    def index(self):
        self.client.get("/", verify=False)

    @task(100)
    def contact(self):
        self.client.get("/contact",  verify=False)

    @task(100)
    def product(self):
        self.client.get("/product/view",params={'id':'81'}, verify=False)

    @task(10)
    def vuln_xss(self):
        payload = "userEmail=goaway%40mailinator.com&userQuestion=What+about+ordering+Beer%3F+Hey%3B+%3A-%3E+Is+there+a+table+where+I+can%2C+say%3B+select+from+*+all+*+my+favorite+beers%3F+&_csrf_faq=9bFfqUaud0SuzsKDt0z2Canq7J7bEC74" 
        self.client.post("/faq", params=payload, verify=False)

    @task(10)
    def vuln_sqli(self):
        payload = '<script>prompt("PleaseEnterYourPassword","")</script>'  
        params = {'id':'', 'searchString':'<script>prompt("PleaseEnterYourPassword","")</script>'}
        self.client.get(f"/search",params=params,verify=False)
        # with self.client.post("/vulnerabilities/sqli/", headers={'user-agent': ua}, cookies=self.locust.client.cookies.get_dict(), data={"id": "%' and 1=0 union select null, concat(first_name,0x0a,last_name,0x0a,user,0x0a,password) from users #","Submit": "Submit"},verify=False, catch_response=True) as response:
        #     if response.status_code == 403:
        #         response.success()

    @task(10)
    def upload_badfile(self):
        files = {'file': ('eicar_com.pdf', open('eicar_com.zip', 'rb'), 'application/zip', {'Expires': '0'})}
        r = self.client.post("/account/profile/edit", files=files, verify=False)

    @task(10)
    def upload_badpdffile(self):
        files = {'file': ('demo.pdf', open('demo.pdf', 'rb'), 'application/pdf', {'Expires': '0'})}
        r = self.client.post("/account/profile/edit", files=files, verify=False)


    def on_start(self):
        # List of IP's that can be used as "source" - hardcoded for simplicity
        ips = ["161.98.255.1", "37.60.63.2", "206.223.191.1", "23.26.110.2", "27.113.239.2", "42.97.255.1", "132.247.255.2", "14.192.95.1", "37.16.63.1", "49.213.31.2", "41.67.128.1", "27.97.1.2"]
        ip = random.choice(ips)
        self.client.verify = False
        #requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += '{cipher}'.format(cipher=currentcipher) 
        #requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'ECDHE-RSA-AES256-SHA'
        self.client.mount("https://", SourceAddressAdapter(ip))
        self.client.mount("http://", SourceAddressAdapter(ip))
        self.login()

    # def on_stop(self):
    #     logout(self)

