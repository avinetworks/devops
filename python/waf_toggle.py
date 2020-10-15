#!/usr/bin/python3

#example PATCH request script to turn off waf policy on vs
#requires avisdk packages. install here #requires avisdk packages. install here https://github.com/avinetworks/sdk/tree/master/python/avi/sdk
#API token generation needed. for token generation help, see https://avinetworks.com/docs/18.2/saas-rest-api-access/ 
import json
from avi.sdk.avi_api import ApiSession

token="InsertTokenHere"
user="admin"
tenant="admin"
controller_ip = "InsertControllerIP"
vs_name = "InsertVSnameHere"

#Desired policy state. Empty string removes WAF policy on VS.
# Input name of policy to turn on, ex: {"waf_policy_ref": "My Waf" } vs {"waf_policy_ref": "" }
request_body = '{ "replace": {"waf_policy_ref": "" }}'

# Get session on the basis of authentication token
with ApiSession(controller_ip, user, token=token, tenant=tenant) as session:
    # Get the virtualservice object by name
    vs_obj = session.get_object_by_name('virtualservice', vs_name)

    if vs_obj:
        # Save the object
        resp = session.patch( 'virtualservice/%s' %vs_obj['uuid'], data=request_body, api_version="18.2.7")
        print(resp.status_code, resp.json())
