#!/usr/bin/python

import json
from avi.sdk.avi_api import ApiSession

api = ApiSession.get_session("34.217.42.190", "admin", "@AviTraining", tenant="admin")

def create_pool(pool_name):
    pool_data = {
        "name": pool_name,
        "health_monitor_refs": [
            "/api/healthmonitor?name=System-HTTP"
        ],
        "servers": [
            {
            "ip": {
            "addr": "10.90.64.16",
            "type": "V4"
                }
            }
        ]
    }
    pool_obj = api.post('pool', data=pool_data)
    return pool_obj

def find_pool(pool_name):
    pool_obj = api.get_object_by_name('pool', pool_name)
    return pool_obj

def create_virtualservice(vs_name, pool_ref):
    vs_data = {
      "cloud_ref": "/api/cloud?name=Default-Cloud",
      "name": vs_name,
      "services": [
        { "port": 80 }
       ],
      "subnet_uuid": "subnet-592cd420",
      "auto_allocate_ip": "true",
      "pool_ref": pool_ref
    }
    virtualservice_obj = api.post('virtualservice', data=vs_data)
    return virtualservice_obj

try:
    pool_data = find_pool('testpool4-eanderson')
except:
    pool_data = create_pool('testpool4-eanderson')

pool_ref = api.get_obj_ref(pool_data)

if pool_ref:
    create_virtualservice('eanderson-vstest', pool_ref )
else:
    print 'unable to create vs and pool'

#create_virtualservice('eanderson-virtualservice', )
#print pool_obj
