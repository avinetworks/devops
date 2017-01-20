#!/usr/bin/python
#
# Created on Sept 21, 2016
# @author: Eric Anderson (eanderson@avinetworks.com)

import argparse
import json
import sys
from pyzabbix import *
from avi.sdk.avi_api import ApiSession
from avi.sdk.utils.api_utils import ApiUtils
import requests
requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser(description='Script used to get objects from Avi Vantage API into Zabbix')
parser.add_argument('entity_type', help='The type of object')
parser.add_argument('-c', '--controller', required=True, help='IP Address of the controller')
parser.add_argument('-u', '--user', required=True, help='Username to authenticate against Avi Controller')
parser.add_argument('-p', '--password', required=True, help='Password to authenticate against Avi Controller')
parser.add_argument('-z', '--zabbix_server', required=True, help='The Zabbix server url: format 10.10.27.198 or zabbixserver.avi.local')
parser.add_argument('--zabbix_user', required=True, help='The Zabbix user.')
parser.add_argument('--zabbix_password', required=True, help='The Zabbix user password.')
parser.add_argument('--zabbix_templateid', required=True, help='The template id of the zabbix template we will post the generated itemprototypes to')
args = parser.parse_args()

zabbix_user = args.zabbix_user
zabbix_password = args.zabbix_password
zabbix_server = 'http://' + args.zabbix_server + '/zabbix/'
zabbix_templateid = args.zabbix_templateid

avi_controller = args.controller
avi_user = args.user
avi_password = args.password

zapi = ZabbixAPI(url=zabbix_server, user=zabbix_user, password=zabbix_password)
print "Connected to Zabbix API Version %s" % zapi.api_version()

def get_metrics_list(entity_type):
    metrics = api.get('analytics/metric_id?entity_type=' + entity_type + '&priority=true').json()['results']
    if entity_type == 'pool':
        metrics_list = [metric for metric in metrics if not metric['name'].startswith('vm_stats')]
    else:
        metrics_list = [metric for metric in metrics]
    return metrics_list

def create_lldiscovery_rule(entity_type):
    zapi.discoveryrule.create(name=entity_type, key_='avi_zabbix_discovery.py[' + entity_type + ']', hostid=zabbix_templateid, type=10, delay=30)

def create_avi_item(ruleid, entity_type, metric_name, metric_description):
    item = zapi.itemprototype.create(
        ruleid=ruleid,
        hostid=zabbix_templateid,
        name='{{#OBJTENANT}} {} {{#OBJNAME}} {}'.format(entity_type, metric_name),
        type='2',
        delay='30',
        status='0',
        description=metric_description,
        value_type='0',
        interfaceid='0',
        applicationPrototypes=[{'name': '{{#OBJTENANT}} {} {{#OBJNAME}}'.format(entity_type)}],
        #avi_trapper[admin,serviceengine,zabbix-1.8.13,vm_stats.avg_net_dropped]
        key_='avi_trapper[{{#OBJTENANT}},{},{{#OBJNAME}},{}]'.format(entity_type, metric_name)
        )
    return item

def create_avi_graph(item, entity_type, metric_name):
    graph = zapi.graphprototype.create(
        name='{{#OBJTENANT}} {} {{#OBJNAME}} {}'.format(entity_type, metric_name),
        width=500,
        height=200,
        gitems=[{'itemid': item['itemids'][0], 'color': '0000FF'}]
    )
    return graph

try:
    discoveryrule = zapi.discoveryrule.get(filter={'name': args.entity_type, 'hostid': zabbix_templateid})[0]
except:
    create_lldiscovery_rule(args.entity_type)
    discoveryrule = zapi.discoveryrule.get(filter={'name': args.entity_type, 'hostid': zabbix_templateid})[0]

api = ApiSession.get_session(avi_controller, avi_user, avi_password)

metrics_list = get_metrics_list(args.entity_type)
for metric in metrics_list:
    print metric['name']
    item = create_avi_item(discoveryrule['itemid'], args.entity_type, metric['name'], metric['description'])
    print item
    graph = create_avi_graph(item, args.entity_type, metric['name'])
    print graph
