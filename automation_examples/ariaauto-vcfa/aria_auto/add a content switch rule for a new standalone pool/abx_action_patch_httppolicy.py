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
    vs_resp = api.get(f"{base_url}/api/virtualservice?name={inputs['requestInputs']['vs']}", headers=headers).json()['results'][0]
    policy_resp_json = api.get(vs_resp['http_policies'][0]['http_policy_set_ref']).json()
    number_of_rules = len(policy_resp_json['http_request_policy']['rules'])
    pool_resp = api.get(f"{base_url}/api/pool?name={inputs['deploymentName']}", headers=headers).json()['results'][0]
    data = {"add":{  'http_request_policy' :{ 'rules' : [{
        'enable': 'true',
        'index': (number_of_rules+1),
        'match': {
          'path': {
            'match_case': 'INSENSITIVE',
            'match_criteria': 'CONTAINS',
            'match_decoded_string': 'true',
            'match_str': [
              f"{inputs['requestInputs']['path']}"
            ]
          }
        },
        'name': f"{inputs['deploymentName']}-switchrule",
        'switching_action': {
          'action': 'HTTP_SWITCHING_SELECT_POOL',
          'pool_ref': pool_resp['url'],
          'status_code': 'HTTP_LOCAL_RESPONSE_STATUS_CODE_200'
                        }
                    }]
                }
            }
        }
    print(data)
    patchresp = api.patch(vs_resp['http_policies'][0]['http_policy_set_ref'], json=data, headers=headers)
    print(patchresp.status_code)


    return ""