#!/usr/bin/python
#
# Created on Aug 27, 2016
# @author: Eric Anderson (eanderson@avinetworks.com)

from avi.sdk.avi_api import ApiSession
import json
import requests
import argparse
import requests
requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser(description='Script used to get objects from Avi Vantage API into Zabbix')
parser.add_argument('entity_type', help='The type of object')
parser.add_argument('-t', '--tenant', default='admin', help='The name of the tenant to run against')
parser.add_argument('-c', '--controller', required=True, help='IP Address of the controller')
parser.add_argument('-u', '--user', required=True, help='Username to authenticate against Avi Controller')
parser.add_argument('-p', '--password', required=True, help='Password to authenticate against Avi Controller')
args = parser.parse_args()

api = ApiSession.get_session(args.controller, args.user, args.password, tenant=args.tenant)

obj_dict = { "data": [] }
response = api.get(args.entity_type + '?page_size=1000').json()
for obj in response['results']:
    new_obj = { "{#OBJNAME}": obj["name"], "{#OBJTYPE}": args.entity_type, "{#OBJTENANT}": args.tenant }
    obj_dict["data"].append(new_obj)

print json.dumps(obj_dict)
