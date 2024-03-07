#!/usr/bin/python
#
# Created: Aug 27, 2016
# Modified: Jan 2, 2017
# @author: Eric Anderson (eanderson@avinetworks.com)
#
# This script requires both Avi SDK and Zabbix Python Module to install:
# pip install --upgrade avisdk
# pip install --upgrade py-zabbix
#
#
import argparse
import json
import sys
from pyzabbix import *
from avi.sdk.avi_api import ApiSession
from avi.sdk.utils.api_utils import ApiUtils
import requests
requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser(description='Script used to get stats from Avi Vantage API into Zabbix')
parser.add_argument('entity_type', help='The type of object')
parser.add_argument('step', default=300, nargs='?', help='The amount of time of metric gathered')
parser.add_argument('-t', '--tenant', default='admin', help='The name of the tenant to run against')
parser.add_argument('-c', '--controllers', required=True, help='Comma Seperated List of IP Addresses of the controllers')
parser.add_argument('-u', '--user', required=True, help='Username to authenticate against Avi Controller')
parser.add_argument('-p', '--password', required=True, help='Password to authenticate against Avi Controller')
args = parser.parse_args()
tenant = args.tenant
controllers = args.controllers
user = args.user
password = args.password


def get_leader(controllers):
    exception_count = 0
    for controller in controllers.split(","):
        try:
            api = ApiSession.get_session(controller, user, password, tenant=tenant)
            cluster_runtime = api.get('cluster/runtime').json()
            for node in cluster_runtime['node_states']:
                if node['role'] == 'CLUSTER_LEADER':
                    master = node['name']
                    return master
        except:
            print 'Unable to connect to the controller:',controller
            exception_count += 1
            pass
    if exception_count == len(controllers.split(",")):
        print "No valid controllers found."
        exit(1)

def get_metrics_list(entity_type):
    metrics = api.get('analytics/metric_id?entity_type=' + entity_type + '&priority=true').json()['results']
    # need to remove extra metrics we don't need
    if entity_type == 'pool':
        metrics_list = [metric['name'] for metric in metrics if not metric['name'].startswith('vm_stats')]
    else:
        metrics_list = [metric['name'] for metric in metrics]
    clean_metrics_list = ','.join(metrics_list)
    return str(clean_metrics_list)

def get_metrics(entity_type, metrics_list, step):
    data = {"metric_requests":[{"step":step,"limit":1,"entity_uuid":"*", "metric_id":metrics_list, "include_name":True, "include_refs":True}]}
    if entity_type == 'pool':
        data['metric_requests'][0]['pool_uuid'] = "*"
    if entity_type == 'serviceengine':
        data['metric_requests'][0]['serviceengine_uuid'] = "*"
    metrics_dict = api.post('/analytics/metrics/collection/', data=data, params={"include_name": True}).json()
    return metrics_dict['series'].values()

def format_metric(entity_type, metric):
    header = metric['header']
    tenant_ref = header['tenant_ref'].rsplit('#',1)[1]
    if entity_type == 'pool':
        obj_name = header['pool_ref'].rsplit('#',1)[1]
    else:
        try:
            obj_name = header['entity_ref'].rsplit('#',1)[1]
        except:
            obj_name = header['entity_ref']
    return obj_name

def get_objects(entity_type, metrics):
    object_list = []
    for metric in metrics:
        for m in metric:
            data = format_metric(entity_type, m)
            object_list.append(data)
    clean_list_set = set(object_list)
    clean_list = list(clean_list_set)
    return json.dumps(clean_list)


master_controller = get_leader(controllers)
print 'Your master controller is:',master_controller
api = ApiSession.get_session(master_controller, user, password, tenant=tenant)
api_utils = ApiUtils(api)

print 'These objects are from the non-metrics api'
response = api.get(args.entity_type + '?page_size=1000').json()
#print response
#object_list = [obj["name"] for obj in response['results']]
#print object_list
object_list = []
for obj in response['results']:
    object_list.append(obj["name"])
print object_list

metrics_list = get_metrics_list(args.entity_type)
metrics_data = get_metrics(args.entity_type, metrics_list, args.step)
print get_objects(args.entity_type, metrics_data)
