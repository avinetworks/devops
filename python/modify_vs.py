#!/usr/bin/python

import json
from avi.sdk.avi_api import ApiSession

api = ApiSession.get_session("34.217.42.190", "admin", "@AviTraining", tenant="admin")

vs_obj = api.get_object_by_name('virtualservice', 'eanderson-vstest')

print vs_obj

vs_ref = api.get_obj_ref(vs_obj)

pool_obj = api.get_object_by_name('pool', 'testpool4-eanderson')

pool_ref = api.get_obj_ref(pool_obj)

vs_data = {
    "cloud_ref": "/api/cloud?name=Default-Cloud",
    "name": 'eanderson-vstest',
    "services": [
    { "port": 8080 }
    ],
    "subnet_uuid": "subnet-592cd420",
    "auto_allocate_ip": "true",
    "pool_ref": pool_ref
}

print api.put(vs_ref, data=vs_data).json()
