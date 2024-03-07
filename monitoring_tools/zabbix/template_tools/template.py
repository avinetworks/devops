#!/usr/bin/python

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
args = parser.parse_args()

user = 'Admin'
password = 'zabbix'
zabbix_server = 'http://10.10.27.198/zabbix/'

avi_controller = '10.10.27.90'
avi_user = 'admin'
avi_password = 'AviNetworks123!'

zapi = ZabbixAPI(zabbix_server)
zapi.login(user, password)

def create_lldiscovery_rule(entity_type):
    zapi.discoveryrule.create(name=entity_type, key_='avi_zabbix_discovery.py[' + entity_type + ']', hostid='10105', type=10, delay=30)

def create_avi_item(ruleid, entity_type, metric_name, metric_description):
    zapi.itemprototype.create(
        ruleid=ruleid,
        hostid='10105',
        name='{#OBJNAME}.' + metric_name,
        type='10',
        delay='30',
        status='0',
        description=metric_description,
        value_type='3',
        interfaceid='0',
        key_='avi_zabbix_monitor.py[' + entity_type + ',{#OBJNAME},' + metric_name + ',5]'
        )

try:
    discoveryrule = zapi.discoveryrule.get(filter={'name': args.entity_type, 'hostid': '10105'})[0]
except:
    create_lldiscovery_rule(args.entity_type)
    discoveryrule = zapi.discoveryrule.get(filter={'name': args.entity_type, 'hostid': '10105'})[0]

api = ApiSession.get_session(avi_controller, avi_user, avi_password)
metrics = api.get('analytics/metric_id?entity_type=' + args.entity_type + '&priority=true').json()['results']
for metric in metrics:
    create_avi_item(discoveryrule['itemid'], args.entity_type, metric['name'], metric['description'])
