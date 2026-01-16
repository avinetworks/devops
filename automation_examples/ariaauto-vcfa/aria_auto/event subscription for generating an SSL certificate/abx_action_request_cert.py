#import json
import requests

def handler(context, inputs):
    # SANITIZED: Controller URL - Replace <CONTROLLER_FQDN> with your Avi Controller FQDN
    base_url = f"https://{inputs['controller']}"
    login_url = f"{base_url}/login"
    # SANITIZED: Authentication credentials - Replace with your username and password
    auth = {'username' : inputs['username'] , 'password': inputs['password']}
    api = requests.session()
    api.verify = False
    resp = api.post(login_url, json=auth)
    print(inputs['requestInputs'])

    #build header dict
    hdr = {'X-Avi-Version': resp.json()['version']['Version']}
    hdr['X-CSRFToken'] = resp.cookies['csrftoken']
    hdr['Referer'] = base_url
    # SANITIZED: Tenant name - Replace with your tenant name
    hdr['X-Avi-Tenant'] = inputs['tenant']
    hdr['Content-Type'] = "application/json"
    headers = hdr

    #query_params = {"name": args.pool}
    vs_resp = api.get(f"{base_url}/api/virtualservice?name=vs-{inputs['deploymentName']}", headers=headers).json()['results'][0]
    #vs_resp = api.get(f"{base_url}/api/virtualservice?name=vs-test", headers=headers).json()['results'][0]
    print(vs_resp)
    # SANITIZED: Certificate request data - Replace <DOMAIN> with your DNS domain
    data = {"certificate":{"subject":{"common_name":f"{inputs['deploymentName']}.<DOMAIN>"}},
        "key_params":{"algorithm":"SSL_KEY_ALGORITHM_RSA","rsa_params":{"key_size":"SSL_KEY_2048_BITS"}},
        "type":"SSL_CERTIFICATE_TYPE_VIRTUALSERVICE",
        "name":inputs['deploymentName'],
        # SANITIZED: Certificate management profile reference - Replace with your cert management profile URL
        "certificate_management_profile_ref":"https://<CONTROLLER_FQDN>/api/certificatemanagementprofile/<CERT_MGMT_PROFILE_UUID>"
      }
    
    postresp = api.post(f'{base_url}/api/sslkeyandcertificate', json=data, headers=headers)
    print(postresp.status_code)
    vs_resp['ssl_key_and_certificate_refs'] = [postresp.json()['url']]
    vs_update_resp = api.put(vs_resp['url'], json=vs_resp, headers=headers)
    print(vs_update_resp.status_code)



    return ""