#!/usr/bin/env python3
import requests
import urllib3
urllib3.disable_warnings()
import sys
import json
import time

tenant = "admin"

def read_in():
    return {x.strip() for x in sys.stdin}

def main():
#login
    lines = read_in()
    for line in lines:
        jsondata = json.loads(line)
    base_url = f"https://{jsondata['controller']}"
    login_url = f"{base_url}/login"
    auth = {'username': jsondata['user'], 'password': jsondata['password']}
    api = requests.session()
    api.verify = False
    resp = api.post(login_url, json=auth)
    hdr = {'X-Avi-Version': resp.json()['version']['Version']}
    hdr['X-CSRFToken'] = resp.cookies['csrftoken']
    hdr['Referer'] = base_url
    hdr['X-Avi-Tenant'] = tenant
    headers = hdr
    mydict = {}
    vs_inv_url = f"{base_url}/api/virtualservice-inventory"
    urls = []
    for i in range(1,20):
        resp = api.get(vs_inv_url, headers=headers, params={"name":jsondata['vs_name']}).json()
        if resp['results'][0]['runtime']['vip_summary'][0]['num_se_assigned'] == 2 and resp['results'][0]['runtime']['vip_summary'][0]['percent_ses_up'] == 100:
            break
        else:
            #print("SEs not ready yet, sleeping 30s")
            time.sleep(30)    
    resp = api.get(vs_inv_url, headers=headers, params={"name":jsondata['vs_name']}).json()
    #print(resp)
    mydict["vs_ip"] = resp['results'][0]['config']['vip'][0]['ip_address']['addr']
    for se in resp['results'][0]['runtime']['vip_summary'][0]['service_engine']:
        urls.append(se['url'])
    for idx, url in enumerate(urls):
        resp = api.get(url, headers=headers).json()
        for nic in resp['data_vnics']:
            if nic['network_name'] == "Avi Internal":
                continue
            else:
                mydict[f"se{idx}"] = nic['vnic_networks'][0]['ip']['ip_addr']['addr']
    #print(mydict)
    sys.stdout.write(json.dumps(mydict))
if __name__ == '__main__':
    main()