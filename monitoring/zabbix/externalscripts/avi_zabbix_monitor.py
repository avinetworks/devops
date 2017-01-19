#!/usr/bin/python
#
# Created on Aug 27, 2016
# @author: Eric Anderson (eanderson@avinetworks.com)

import argparse
import json
import sys
from avi.sdk.avi_api import ApiSession
from avi.sdk.utils.api_utils import ApiUtils
import requests
requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser(description='Script used to get stats from Avi Vantage API into Zabbix')
parser.add_argument('entity_type', help='The type of object')
parser.add_argument('entity_name', help='The name of the Object')
parser.add_argument('metric_id', help='The metric_id of the object to be queried')
parser.add_argument('step', default=300, nargs='?', help='The amount of time of metric gathered')
parser.add_argument('-t', '--tenant', default='admin', help='The name of the tenant to run against')
parser.add_argument('-c', '--controller', type=str, required=True, help='IP Address of the controller')
parser.add_argument('-u', '--user', type=str, required=True, help='Username to authenticate against Avi Controller')
parser.add_argument('-p', '--password', type=str, required=True, help='Password to authenticate against Avi Controller')
args = parser.parse_args()

api = ApiSession.get_session(args.controller, args.user, args.password, tenant=args.tenant)
api_utils = ApiUtils(api)

def get_metrics(entity_type, entity_name, metric_id, step, tenant):
    try:
        metrics_dict = api_utils.get_metrics(entity_type, entity_name, metric_id=metric_id, step=step, limit=1, tenant=tenant, timeout=5)
        return metrics_dict['series'][0]['data'][0]['value']
    except:
        print 'Error in getting %s metric for %s name: %s' % (metric_id, entity_type, entity_name)
        return exit(1)


print get_metrics(args.entity_type, args.entity_name, args.metric_id, args.step, args.tenant)
