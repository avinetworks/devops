#!/usr/bin/python


version = 'v2018-11-26'

#########################################################################################
#                                                                                       #
#                                                                                       #
#                                                                                       #
#  REQUIREMENTS:                                                                        #
#    1. python 2.7                                                                      #
#    2. python requests                                                                 #
#                                                                                       #
#                                                                                       #
#                                                                                       #
#                                                                                       #
#  @author: Matthew Karnowski (mkarnowski@avinetworks.com)                              #
#                                                                                       #
#                                                                                       #
#                                                                                       #
#########################################################################################
#########################################################################################

#----- Import Libraries

import requests
requests.packages.urllib3.disable_warnings()
import json
import time
import syslog
import socket
from multiprocessing import Process
from datetime import datetime
import base64
import logging
import traceback
import argparse
import sys
import os
from metrics_endpoints import *
import cPickle as pickle



#----- Command line Arguments
parser = argparse.ArgumentParser(description='Avi Metrics Script')
parser.add_argument('-v', '--version', action='version', version='%(prog)s '+version)
required_args = parser.add_argument_group('required named arguments')
parser.add_argument('--brief', help='Print Exceptions Only', required=False, action='store_true')
parser.add_argument('--debug', help='Print All Output, this the DEFAULT setting', required=False, action='store_true')
parser.add_argument('-m', '--metrics', help='Metrics Endpoint for Sending the data', action='append', required=False, default=None)
parser.add_argument('--norealtime', help='Disable Check for Realtime Stats', required=False, action='store_true')
args = parser.parse_args()




#----- Determine Metrics Endpoint Type Info
def determine_endpoint_type():
    endpoint_types = [
        'graphite',
        'appdynamics_http',
        'appdynamics_machine',
        'splunk',
        'datadog',
        'influxdb'
        ]
    if args.metrics == None:
        print '=====> ERROR:  No metric type defined, acceptable types are: '+str(endpoint_types)
        sys.exit(1)
    else:
        endpoint_list = []
        for a in args.metrics:
            if a.lower() not in endpoint_types:
                print '=====> ERROR:  Invalid metrics type, acceptable types are: '+str(endpoint_types)
                sys.exit(1)
            elif a.lower() == 'graphite':
                with open(os.path.join(fdir,'graphite_host.json')) as gr:
                    endpoint_info = json.load(gr)['graphite']
                    endpoint_info['type'] = 'graphite'
                    endpoint_list.append(endpoint_info)
            elif a.lower() == 'appdynamics_machine':
                endpoint_info={'type': 'appdynamics_machine'}
                endpoint_list.append(endpoint_info)
            elif a.lower() == 'appdynamics_http':
                with open(os.path.join(fdir,'appdynamics_http.json')) as appd:
                    endpoint_info = json.load(appd)['appdynamics']
                    endpoint_info['type'] = 'appdynamics_http'
                    endpoint_list.append(endpoint_info)
            elif a.lower() == 'splunk':
                with open(os.path.join(fdir,'splunk_host.json')) as spl:
                    endpoint_info = json.load(spl)['splunk_server']
                    endpoint_info['type'] = 'splunk'
                    endpoint_list.append(endpoint_info)
            elif a.lower() == 'datadog':
                with open(os.path.join(fdir,'datadog.json')) as dd:
                    endpoint_info = json.load(dd)['datadog']
                    endpoint_info['type'] = 'datadog'
                    endpoint_list.append(endpoint_info)
            elif a.lower() == 'influxdb':
                with open(os.path.join(fdir,'influxdb.json')) as inflx:
                    endpoint_info = json.load(inflx)['influxdb']
                    endpoint_info['type'] = 'influxdb'
                    endpoint_list.append(endpoint_info)                    
        return endpoint_list





#----- Setting print levels
if args.brief == True:
    args.debug = False
else:
    args.debug = True





#----- This function allows for passwords to be either plaintext or base64 encoded
def isBase64(password):
    try:
        if base64.b64encode(base64.b64decode(b''+password)) == password:
            if all(ord(c) < 128 for c in base64.b64decode(b''+password)):
                return base64.b64decode(b''+password)
            else:
                return password
        else:
            return password
    except Exception:
        return password




#----- This class is where all the test methods/functions exist and are executed
class avi_metrics():
    def __init__(self,avi_controller,host_location,host_environment, avi_user, avi_pass):
        self.avi_cluster_ip = avi_controller
        self.host_location = host_location
        self.host_environment = host_environment
        self.avi_user = avi_user
        self.avi_pass = avi_pass
        #------ Default Metric Payload Template
        self.payload_template = {}
        self.payload_template['location'] = self.host_location
        self.payload_template['environment'] = self.host_environment
        self.payload_template['avicontroller'] = self.avi_cluster_ip
        #------
        self.vs_metric_list  = [
            'l4_server.avg_errored_connections',
            'l4_server.avg_rx_pkts',
            'l4_server.avg_bandwidth',
            'l4_server.avg_open_conns',
            'l4_server.avg_new_established_conns',
            'l4_server.avg_pool_complete_conns',
            'l4_server.apdexc',
            'l4_server.avg_total_rtt',
            'l4_client.apdexc',
            'l4_client.avg_bandwidth',
            'l4_client.avg_application_dos_attacks',
            'l4_client.avg_complete_conns',
            'l4_client.avg_connections_dropped',
            'l4_client.avg_new_established_conns',
            'l4_client.avg_policy_drops',
            'l4_client.avg_rx_pkts',
            'l4_client.avg_tx_pkts',
            'l4_client.avg_rx_bytes',
            'l4_client.avg_tx_bytes',
            'l4_client.max_open_conns',
            'l4_client.avg_lossy_connections',
            'l7_client.avg_complete_responses',
            'l7_client.avg_client_data_transfer_time',
            'l7_client.avg_client_txn_latency',
            'l7_client.sum_application_response_time',
            'l7_client.avg_resp_4xx_avi_errors',
            'l7_client.avg_resp_5xx_avi_errors',
            'l7_client.avg_resp_4xx',
            'l7_client.avg_resp_5xx',
            'l4_client.avg_total_rtt',
            'l7_server.avg_resp_latency',
            'l7_server.apdexr',
            'l7_client.avg_page_load_time',
            'l7_client.apdexr',
            'l7_client.avg_ssl_handshakes_new',
            'l7_client.avg_ssl_connections',
            'l7_server.avg_application_response_time',
            'l7_server.pct_response_errors',
            'l7_server.avg_frustrated_responses',
            'l7_server.avg_total_requests',
            'l7_client.sum_get_reqs',
            'l7_client.sum_post_reqs',
            'l7_client.sum_other_reqs',
            'l7_client.avg_frustrated_responses',
            'l7_client.avg_waf_attacks',
            'l7_client.pct_waf_attacks',
            'l7_client.sum_total_responses',
            'l7_client.avg_waf_rejected', #---- available after 17.2
            'l7_client.avg_waf_evaluated', #---- available after 17.2
            'l7_client.avg_waf_matched', #---- available after 17.2.12
            'l7_client.avg_waf_disabled', #---- available after 17.2.12
            'l7_client.pct_waf_disabled', #---- available after 17.2.12
            'l7_client.avg_http_headers_count', #---- available after 17.2.12
            'l7_client.avg_http_headers_bytes', #---- available after 17.2.12
            'l7_client.pct_get_reqs', #---- available after 17.2.12
            'l7_client.pct_post_reqs', #---- available after 17.2.12
            'l7_client.avg_http_params_count', #---- available after 17.2.12
            'l7_client.avg_uri_length', #---- available after 17.2.12
            'l7_client.avg_post_bytes', #---- available after 17.2.12
            'dns_client.avg_complete_queries',
            'dns_client.avg_domain_lookup_failures',
            'dns_client.avg_tcp_queries',
            'dns_client.avg_udp_queries',
            'dns_client.avg_udp_passthrough_resp_time',
            'dns_client.avg_unsupported_queries',
            'dns_client.pct_errored_queries',
            'dns_client.avg_domain_lookup_failures',
            'dns_client.avg_avi_errors',
            'dns_server.avg_complete_queries',
            'dns_server.avg_errored_queries',
            'dns_server.avg_tcp_queries',
            'dns_server.avg_udp_queries']
        #------        
        self.se_metric_list = [
            'se_if.avg_bandwidth',
            'se_stats.avg_connection_mem_usage',
            'se_stats.avg_connections',
            'se_stats.avg_connections_dropped',
            'se_stats.avg_cpu_usage',
            'se_stats.avg_disk1_usage',
            'se_stats.avg_mem_usage',
            'se_stats.avg_dynamic_mem_usage',
            'se_stats.avg_persistent_table_usage',
            'se_stats.avg_rx_bandwidth',
            'se_if.avg_rx_bytes',
            'se_if.avg_rx_pkts',
            'se_if.avg_rx_pkts_dropped_non_vs',
            'se_if.avg_tx_pkts',
            'se_if.avg_tx_bytes',
            'se_stats.avg_ssl_session_cache_usage',
            'se_if.avg_connection_table_usage',
            'se_stats.max_se_bandwidth',
            'se_stats.avg_eth0_bandwidth',
            'se_stats.pct_syn_cache_usage',
            'se_stats.avg_packet_buffer_usage',
            'se_stats.avg_packet_buffer_header_usage',
            'se_stats.avg_packet_buffer_large_usage',
            'se_stats.avg_packet_buffer_small_usage']
        #------          
        self.controller_metric_list  = [
            'controller_stats.avg_cpu_usage',
            'controller_stats.avg_disk_usage',
            'controller_stats.avg_mem_usage']
        #----
        self.pool_server_metric_list = [
            'l4_server.avg_rx_pkts',
            'l4_server.avg_tx_pkts',
            'l4_server.avg_rx_bytes',
            'l4_server.avg_tx_bytes',
            'l4_server.avg_bandwidth',
            'l7_server.avg_complete_responses',
            'l4_server.avg_new_established_conns',
            'l4_server.avg_pool_open_conns',
            'l4_server.avg_pool_complete_conns',
            'l4_server.avg_open_conns',
            'l4_server.max_open_conns']


    def avi_login(self):
        try:
            login = pickle.load(open((os.path.join(fdir,self.avi_cluster_ip)),'rb'))
            for c in login.cookies:
                expires = c.expires
            headers = ({"X-Avi-Tenant": "admin", 'content-type': 'application/json'})
            resp = requests.get('https://%s/api/cluster' %self.avi_cluster_ip, verify=False, headers = headers,cookies=dict(sessionid= login.cookies['sessionid']),timeout=5)
            #if expires > time.time():
            if resp.status_code == 200:
                return login
            else:
                login = requests.post('https://%s/login' %self.avi_cluster_ip, verify=False, data={'username': self.avi_user, 'password': self.avi_pass},timeout=15)
                pickle.dump(login, open((os.path.join(fdir,self.avi_cluster_ip)),'wb'))
                return login
        except:
            login = requests.post('https://%s/login' %self.avi_cluster_ip, verify=False, data={'username': self.avi_user, 'password': self.avi_pass},timeout=15)
            pickle.dump(login, open((os.path.join(fdir,self.avi_cluster_ip)),'wb'))
            return login


    def avi_request(self,avi_api,tenant):
        headers = ({"X-Avi-Tenant": "%s" %tenant, 'content-type': 'application/json'})
        return requests.get('https://%s/api/%s' %(self.avi_controller,avi_api), verify=False, headers = headers,cookies=dict(sessionid= self.login.cookies['sessionid']),timeout=50)


    def avi_post(self,api_url,tenant,payload):
        headers = ({"X-Avi-Tenant": "%s" %tenant, 'content-type': 'application/json','referer': 'https://%s' %self.avi_controller, 'X-CSRFToken': dict(self.login.cookies)['csrftoken']})
        cookies = dict(sessionid= self.login.cookies['sessionid'],csrftoken=self.login.cookies['csrftoken'])
        return requests.post('https://%s/api/%s' %(self.avi_controller,api_url), verify=False, headers = headers,cookies=cookies, data=json.dumps(payload),timeout=50)



    #----- Tries to determine a follower controller to poll
    def controller_to_poll(self):
        headers = ({"X-Avi-Tenant": "admin", 'content-type': 'application/json'})
        resp = (requests.get('https://%s/api/%s' %(self.avi_cluster_ip,'cluster/runtime'), verify=False, headers = headers,cookies=dict(sessionid= self.login.cookies['sessionid']),timeout=50)).json()
        follower_list = []
        if len(resp['node_states']) > 1:
            for c in resp['node_states']:
                if c['state'] == 'CLUSTER_ACTIVE' and c['role']  == 'CLUSTER_FOLLOWER':
                    follower_list.append(c['mgmt_ip'])
            if len(follower_list) == 0:
                return self.avi_cluster_ip
            else:
                return sorted(follower_list)[0]
        else:
            return self.avi_cluster_ip



    #----- Creates inventory dicts to be used by other methods
    def gen_inventory_dict(self):
        try:
            start_time = time.time()
            vs_dict = {'tenants':{},'admin_vs':[]}
            se_dict={'tenants':{},'admin_se':[]}
            pool_dict={'tenants':{}}
            seg_dict = {'tenants':{}}
            if self.login.json()['user']['is_superuser'] == True: #----if SU, use wildcard tenant
                vs_inv = self.avi_request('virtualservice-inventory?page_size=200','*').json()
                resp = vs_inv
                page_number = 1
                while 'next' in resp:
                    page_number += 1
                    resp = self.avi_request('virtualservice-inventory?page_size=200&page='+str(page_number),'*').json()
                    for v in resp['results']:
                        vs_inv['results'].append(v)
                #------------------
                se_inv = self.avi_request('serviceengine-inventory?page_size=200','*').json()
                resp = se_inv
                page_number = 1
                while 'next' in resp:
                    page_number += 1
                    resp = self.avi_request('serviceengine-inventory?page_size=200&page='+str(page_number),'*').json()
                    for s in resp['results']:
                        se_inv['results'].append(s)
                #------------------
                pool_inv = self.avi_request('pool-inventory?page_size=200','*').json()
                resp = pool_inv
                page_number = 1
                while 'next' in resp:
                    page_number += 1
                    resp = self.avi_request('pool-inventory?page_size=200&page='+str(page_number),'*').json()
                    for p in resp['results']:
                        pool_inv['results'].append(p)
                #------------------
                seg_inv = self.avi_request('serviceenginegroup-inventory?page_size=1000','*').json()
                if vs_inv['count'] > 0:
                    for v in vs_inv['results']:
                        for t in self.tenants:
                            if t['url'].split('/tenant/')[1] == v['config']['tenant_ref'].split('/tenant/')[1]:
                                temp_tenant = t['name']
                        if temp_tenant not in vs_dict['tenants']:
                            vs_dict['tenants'][temp_tenant] = {'count':1,'results':[v]}
                        else:
                            vs_dict['tenants'][temp_tenant]['count']+=1
                            vs_dict['tenants'][temp_tenant]['results'].append(v)
                        vs_dict[v['uuid']] = v['config']['name']
                        if temp_tenant == 'admin':
                            vs_dict['admin_vs'].append(v['uuid'])
                if se_inv['count'] > 0:
                    for s in se_inv['results']:
                        for t in self.tenants:
                            if t['url'].split('/tenant/')[1] == s['config']['tenant_ref'].split('/tenant/')[1]:
                                temp_tenant = t['name']
                        if temp_tenant not in se_dict['tenants']:
                            se_dict['tenants'][temp_tenant] = {'count':1,'results':[s]}
                        else:
                            se_dict['tenants'][temp_tenant]['count']+=1
                            se_dict['tenants'][temp_tenant]['results'].append(s)
                        se_dict[s['uuid']] = s['config']['name']
                        if temp_tenant == 'admin':
                            se_dict['admin_se'].append(s['uuid'])
                if pool_inv['count'] > 0:
                    for p in pool_inv['results']:
                        for t in self.tenants:
                            if t['url'].split('/tenant/')[1] == p['config']['tenant_ref'].split('/tenant/')[1]:
                                temp_tenant = t['name']
                        if temp_tenant not in pool_dict['tenants']:
                            pool_dict['tenants'][temp_tenant] = {'count':1,'results':[p]}
                        else:
                            pool_dict['tenants'][temp_tenant]['count']+=1
                            pool_dict['tenants'][temp_tenant]['results'].append(p)
                        pool_dict[p['uuid']] = p['config']['name']
                if seg_inv['count'] > 0:
                    for seg in seg_inv['results']:
                        for t in self.tenants:
                            if t['url'].split('/tenant/')[1] == seg['config']['tenant_ref'].split('/tenant/')[1]:
                                temp_tenant = t['name']
                        if temp_tenant not in seg_dict['tenants']:
                            seg_dict['tenants'][temp_tenant] = {'count':1,'results':[seg]}
                        else:
                            seg_dict['tenants'][temp_tenant]['count']+=1
                            seg_dict['tenants'][temp_tenant]['results'].append(seg)
                        seg_dict[seg['uuid']] = seg['config']['name']
            else:
                for t in self.tenants:
                    vs_inv = self.avi_request('virtualservice-inventory?page_size=200',t['name']).json()
                    resp = vs_inv
                    page_number = 1
                    while 'next' in resp:
                        page_number += 1
                        resp = self.avi_request('virtualservice-inventory?page_size=200&page='+str(page_number),t['name']).json()
                        for v in resp['results']:
                            vs_inv['results'].append(v)
                    #------------------
                    se_inv = self.avi_request('serviceengine-inventory?page_size=200',t['name']).json()
                    resp = se_inv
                    page_number = 1
                    while 'next' in resp:
                        page_number += 1
                        resp = self.avi_request('serviceengine-inventory?page_size=200&page='+str(page_number),t['name']).json()
                        for s in resp['results']:
                            se_inv['results'].append(s)
                    #------------------
                    pool_inv = self.avi_request('pool-inventory?page_size=200',t['name']).json()
                    resp = pool_inv
                    page_number = 1
                    while 'next' in resp:
                        page_number += 1
                        resp = self.avi_request('pool-inventory?page_size=200&page='+str(page_number),t['name']).json()
                        for p in resp['results']:
                            pool_inv['results'].append(p)
                    #------------------
                    seg_inv = self.avi_request('serviceenginegroup-inventory?page_size=1000',t['name']).json()
                    if vs_inv['count'] > 0:
                        vs_dict['tenants'][t['name']]=vs_inv
                    for v in vs_inv['results']:
                        vs_dict[v['uuid']] = v['config']['name']
                        if t['name'] == 'admin':
                            vs_dict['admin_vs'].append(v['uuid'])
                    if se_inv['count'] > 0:
                        se_dict['tenants'][t['name']] = se_inv
                    for s in se_inv['results']:
                        se_dict[s['uuid']] = s['config']['name']
                        if t['name'] == 'admin':
                            se_dict['admin_se'].append(s['uuid'])
                    if pool_inv['count'] > 0:
                        pool_dict['tenants'][t['name']] = pool_inv
                    for p in pool_inv['results']:
                        pool_dict[p['uuid']] = s['config']['name']
                    if seg_inv['count'] > 0:
                        seg_dict['tenants'][t['name']] = seg_inv
                    for seg in seg_inv['results']:
                        seg_dict[seg['uuid']] = seg['config']['name']
            temp_total_time = str(time.time()-start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func gen_inventory_dict completed, executed in '+temp_total_time+' seconds')
            return vs_dict, se_dict, pool_dict, seg_dict
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func gen_inventory_dict encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)
            sys.exit(1)




    #-----------------------------------
    #----- Remove unavailable metrics for current version
    def remove_version_specific_metrics(self):
        try:
        #----- Generate List of Available Metrics
            available_metrics = []
            resp = self.avi_request('analytics/metric_id',self.tenants[0]['name']).json()
            vs_metrics = []
            se_metrics = []
            pool_server_metrics = []
            controller_metrics = []
            for m in resp['results']:
                available_metrics.append(m['name'])
            for vm in self.vs_metric_list:
                if vm in available_metrics:
                    vs_metrics.append(vm)
            for sm in self.se_metric_list:
                if sm in available_metrics:
                    se_metrics.append(sm)
            for cm in self.controller_metric_list:
                if cm in available_metrics:
                    controller_metrics.append(cm)
            for pm in self.pool_server_metric_list:
                if pm in available_metrics:
                    pool_server_metrics.append(pm)
            vs_metric_list = ','.join(vs_metrics)          
            se_metric_list = ','.join(se_metrics)
            controller_metric_list = ','.join(controller_metrics)
            pool_server_metric_list = ','.join(pool_server_metrics)
            return vs_metric_list, se_metric_list, controller_metric_list, pool_server_metric_list
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': remove_version_specific_metrics encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)










    #-----------------------------------
    #----- Add Test functions
    #-----------------------------------
    def srvc_engn_vs_count(self):
        try:
            temp_start_time = time.time()
            discovered_vs = []
            srvc_engn_dict = {}
            for t in self.tenants:
                if t['name'] in self.se_dict['tenants'] and self.se_dict['tenants'][t['name']]['count'] > 0:
                    for entry in self.se_dict['tenants'][t['name']]['results']:
                        if len(entry['config']['virtualservice_refs']) > 0:
                            for v in entry['config']['virtualservice_refs']:
                                if entry['config']['name']+v not in discovered_vs:
                                    discovered_vs.append(entry['config']['name']+v)
                                    if entry['config']['name'] not in srvc_engn_dict:
                                        srvc_engn_dict[self.se_dict[entry['uuid']]] = 1
                                    else:
                                        srvc_engn_dict[entry['config']['name']] +=1
                        else:
                            if entry['config']['name'] not in srvc_engn_dict:
                                srvc_engn_dict[entry['config']['name']] = 0
            if len(srvc_engn_dict) > 0:
                endpoint_payload_list = []
                for entry in srvc_engn_dict:
                    temp_payload = self.payload_template.copy()
                    temp_payload['metric_type'] = 'serviceengine_vs_count'
                    temp_payload['timestamp']=int(time.time())
                    temp_payload['se_name'] = entry
                    temp_payload['metric_type'] = 'serviceengine_vs_count'
                    temp_payload['metric_name'] = 'vs_count'
                    temp_payload['metric_value'] = srvc_engn_dict[entry]
                    temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||serviceengine||%s||vs_count' %entry
                    endpoint_payload_list.append(temp_payload)
                send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func srvc_engn_vs_count completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func srvc_engn_vs_count encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)

    #-----------------------------------

    def srvc_engn_count(self):
        try:
            temp_start_time = time.time()
            se_count = len(self.se_dict) - 2
            endpoint_payload_list = []
            temp_payload = self.payload_template.copy()
            temp_payload['timestamp']=int(time.time())
            temp_payload['metric_type'] = 'serviceengine_count'
            temp_payload['metric_name'] = 'count'
            temp_payload['metric_value'] = se_count
            temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||serviceengine||count'
            endpoint_payload_list.append(temp_payload)
            send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func srvc_engn_count completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func srvc_engn_count encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)


    #-----------------------------------


    def srvc_engn_stats(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            discovered_ses = []
            discovered_health = []
            for t in self.tenants:
                if t['name'] in self.se_dict['tenants'] and self.se_dict['tenants'][t['name']]['count'] > 0:
                    payload = {
                        "metric_requests": [
                            {
                                "step": 300,
                                "limit": 1,
                                "aggregate_entity": False,
                                "entity_uuid": "*",
                                "se_uuid": "*",
                                "id": "collItemRequest:AllSEs",
                                "metric_id": self.se_metric_list
                            }
                            ]}
                    se_stat = self.avi_post('analytics/metrics/collection?pad_missing_data=false', t['name'], payload).json()
                    if args.norealtime == False:
                        payload = {
                            "metric_requests": [
                                {
                                    "step": 5,
                                    "limit": 1,
                                    "aggregate_entity": False,
                                    "entity_uuid": "*",
                                    "se_uuid": "*",
                                    "id": "collItemRequest:AllSEs",
                                    "metric_id": self.se_metric_list
                                }
                                ]}
                        realtime_stat = self.avi_post('analytics/metrics/collection?pad_missing_data=false', t['name'], payload).json()
                        if 'series' in realtime_stat:
                            se_stat['series']['collItemRequest:AllSEs'].update(realtime_stat['series']['collItemRequest:AllSEs'])
                    for s in se_stat['series']['collItemRequest:AllSEs']:
                        if s in self.se_dict:
                            se_name = self.se_dict[s]
                            if se_name not in discovered_ses:
                                discovered_ses.append(se_name)
                                for entry in se_stat['series']['collItemRequest:AllSEs'][s]:
                                    if 'data' in entry:
                                        temp_payload = self.payload_template.copy()
                                        temp_payload['timestamp']=int(time.time())
                                        temp_payload['se_name'] = se_name
                                        temp_payload['tenant'] = t['name']
                                        temp_payload['metric_type'] = 'serviceengine_metrics'
                                        temp_payload['metric_name'] = entry['header']['name']
                                        temp_payload['metric_value'] = entry['data'][0]['value']
                                        temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||serviceengine||%s||%s' %(se_name, entry['header']['name'])
                                        endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func srvc_engn_stats completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func srvc_engn_stats encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)



    #-----------------------------------
    #--- This function will loop through all tenants pulling the following statistics
    #--- for all Virtual Services.
    def virtual_service_stats_threaded(self):
        proc = []
        for t in self.tenants:
            t_name = t['name']
            p = Process(target = self.virtual_service_stats, args = (t_name,))
            p.start()
            proc.append(p)
        for p in proc:
            p.join()




    def virtual_service_stats(self,tenant):
        try:
            temp_start_time = time.time()
            #-----
            if tenant in self.vs_dict['tenants'] and self.vs_dict['tenants'][tenant]['count'] > 0:
                endpoint_payload_list = []
                payload =  {'metric_requests': [{'step' : 300, 'limit': 1, 'id': 'allvs', 'entity_uuid' : '*', 'metric_id': self.vs_metric_list}]}
                vs_stats = self.avi_post('analytics/metrics/collection?pad_missing_data=false', tenant, payload).json()
                #----- this pulls 1 min avg stats for vs that have realtime stats enabled
                if args.norealtime == False:
                    payload =  {'metric_requests': [{'step' : 5, 'limit': 1, 'id': 'allvs', 'entity_uuid' : '*', 'metric_id': self.vs_metric_list}]}
                    realtime_stats = self.avi_post('analytics/metrics/collection?pad_missing_data=false', tenant, payload).json()
                    #----- overwrites real time vs' 5 min avg with the 1 min avg
                    if 'series' in realtime_stats:
                        vs_stats['series']['allvs'].update(realtime_stats['series']['allvs'])
                #----- THIS IS NEW
                for v in vs_stats['series']['allvs']:
                    if v in self.vs_dict:
                        vs_uuid = v
                        vs_name = self.vs_dict[vs_uuid]
                        for m in vs_stats['series']['allvs'][v]:
                            metric_name = m['header']['name']
                            if 'data' in m:
                                temp_payload = self.payload_template.copy().copy()
                                temp_payload['timestamp']=int(time.time())
                                temp_payload['vs_name'] = vs_name
                                temp_payload['tenant'] = tenant
                                temp_payload['metric_type'] = 'virtualservice_metrics'
                                temp_payload['metric_name'] = metric_name
                                temp_payload['metric_value'] = m['data'][0]['value']
                                temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||%s||%s' %(vs_name, metric_name)
                                endpoint_payload_list.append(temp_payload)
                if len(endpoint_payload_list) > 0:
                    send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func virtual_service_stats completed for tenant: '+tenant+', executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func virtual_service_stats encountered an error for tenant '+tenant)
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)




    def vs_metrics_per_se_threaded(self):
        try:
            temp_start_time = time.time()
            major,minor = self.login.json()['version']['Version'].rsplit('.',1)
            if (float(major) >= 17.2 and float(minor) >= 8) or float(major) >= 18.1: #----- controller metrics api introduced in 17.2.5
                proc = []
                for t in self.tenants:
                    if t['name'] in self.se_dict['tenants'] and self.se_dict['tenants'][t['name']]['count'] > 0:
                        p = Process(target = self.vs_metrics_per_se, args = (t['name'],))
                        p.start()
                        proc.append(p)
                    elif 'admin' in self.se_dict['tenants'] and self.se_dict['tenants']['admin']['count'] > 0:
                        p = Process(target = self.vs_metrics_per_se, args = (t['name'],))
                        p.start()
                        proc.append(p)
                for p in proc:
                        p.join()
                temp_total_time = str(time.time()-temp_start_time)
                if args.debug == True:
                    print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_metrics_per_se_threaded completed, executed in '+temp_total_time+' seconds')
        except:
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)





    def vs_metrics_per_se(self,tenant):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            payload =  {'metric_requests': [{'step' : 300, 'limit': 1, 'id': 'vs_metrics_by_se', 'entity_uuid' : '*', 'serviceengine_uuid': '*', 'include_refs': True, 'metric_id': self.vs_metric_list}]}
            vs_stats = self.avi_post('analytics/metrics/collection?pad_missing_data=false', tenant, payload).json()
            #----- this will pull 1 min stats for vs that have realtime stat enabled
            if args.norealtime == False:
                payload =  {'metric_requests': [{'step' : 5, 'limit': 1, 'id': 'vs_metrics_by_se', 'entity_uuid' : '*', 'serviceengine_uuid': '*', 'include_refs': True, 'metric_id': self.vs_metric_list}]}
                realtime_stats = self.avi_post('analytics/metrics/collection?pad_missing_data=false', tenant, payload).json()
                #----- overwrite 5 min avg stats with 1 min avg stats for vs that have realtime stats enabled
                if 'series' in realtime_stats:
                    vs_stats['series']['vs_metrics_by_se'].update(realtime_stats['series']['vs_metrics_by_se'])
            if len(vs_stats['series']['vs_metrics_by_se']) > 0:
                for entry in vs_stats['series']['vs_metrics_by_se']:
                    if tenant == 'admin' and entry not in self.vs_dict['admin_vs']:
                        continue
                    elif tenant != 'admin' and entry in self.vs_dict['admin_vs']:
                        continue
                    else:
                        vs_name = self.vs_dict[entry]
                        for d in vs_stats['series']['vs_metrics_by_se'][entry]:
                            if 'data' in d:
                                se_name = self.se_dict[d['header']['serviceengine_ref'].split('serviceengine/')[1]]
                                temp_payload = self.payload_template.copy()
                                temp_payload['timestamp']=int(time.time())
                                temp_payload['se_name'] = se_name
                                temp_payload['tenant'] = tenant
                                temp_payload['vs_name'] = vs_name
                                temp_payload['metric_type'] = 'virtualservice_metrics_per_serviceengine'
                                temp_payload['metric_name'] = d['header']['name']
                                temp_payload['metric_value'] = d['data'][0]['value']
                                temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||serviceengine||%s||virtualservice_stats||%s||%s' %(se_name,vs_name,d['header']['name'])
                                endpoint_payload_list.append(temp_payload)
                if len(endpoint_payload_list) > 0:
                    send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
                temp_total_time = str(time.time()-temp_start_time)
                if args.debug == True:
                    print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_metrics_per_se completed tenant: '+tenant+', executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_metrics_per_se for tenant: '+tenant+', encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)








    #----- VS / SE HEALTHSCORES
    def vs_se_healthscores(self):
        try:
            temp_start_time = time.time()
            discovered_vs = []
            discovered_se = []
            endpoint_payload_list = []
            for t in self.tenants:
                if t['name'] in self.vs_dict['tenants'] and self.vs_dict['tenants'][t['name']]['count'] > 0:
                    for v in self.vs_dict['tenants'][t['name']]['results']:
                        if v['uuid'] not in discovered_vs:
                            discovered_vs.append(v['uuid'])
                            vs_name = v['config']['name']
                            temp_dict = {}
                            temp_dict['healthscore'] = v['health_score']['health_score']
                            temp_dict['resources_penalty'] = v['health_score']['resources_penalty']
                            temp_dict['anomaly_penalty'] = v['health_score']['anomaly_penalty']
                            temp_dict['performance_score'] = v['health_score']['performance_score']
                            temp_dict['security_penalty'] = v['health_score']['security_penalty']
                            for h in temp_dict:
                                temp_payload = self.payload_template.copy()
                                temp_payload['timestamp']=int(time.time())
                                temp_payload['vs_name'] = vs_name
                                temp_payload['tenant'] = t['name']
                                temp_payload['metric_type'] = 'virtualservice_healthscore'
                                temp_payload['metric_name'] = h
                                temp_payload['metric_value'] = temp_dict[h]
                                temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||%s||%s' %(vs_name,h)
                                endpoint_payload_list.append(temp_payload)
                if t['name'] in self.se_dict['tenants'] and self.se_dict['tenants'][t['name']]['count'] > 0:
                    for s in self.se_dict['tenants'][t['name']]['results']:
                        if s['uuid'] not in discovered_se:
                            discovered_se.append(s['uuid'])
                            #se_healthscore = s['health_score']['health_score']
                            temp1_dict = {}
                            temp1_dict['healthscore'] = s['health_score']['health_score']
                            temp1_dict['resources_penalty'] = s['health_score']['resources_penalty']
                            temp1_dict['anomaly_penalty'] = s['health_score']['anomaly_penalty']
                            temp1_dict['performance_score'] = s['health_score']['performance_score']
                            temp1_dict['security_penalty'] = s['health_score']['security_penalty']
                            for h in temp1_dict:
                                temp1_payload = self.payload_template.copy()
                                temp1_payload['timestamp']=int(time.time())
                                temp1_payload['se_name'] = self.se_dict[s['uuid']]
                                temp1_payload['tenant'] = t['name']
                                temp1_payload['metric_type'] = 'serviceengine_healthscore'
                                temp1_payload['metric_name'] = h
                                temp1_payload['metric_value'] = temp1_dict[h]
                                temp1_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||serviceengine||%s||%s' %(self.se_dict[s['uuid']],h)
                                endpoint_payload_list.append(temp1_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_se_healthscores completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_se_healthscores encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)



    #----- VS UP/DOWN/Enabled/Disabled STATUS
    def vs_oper_status(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            vs_up_count = 0
            vs_down_count = 0
            vs_disabled_count = 0
            vs_count = 0
            for t in self.tenants:
                if t['name'] in self.vs_dict['tenants'] and self.vs_dict['tenants'][t['name']]['count'] > 0:
                    for v in self.vs_dict['tenants'][t['name']]['results']:
                        vs_name = v['config']['name']
                        metric_name = 'oper_status'
                        if v['runtime']['oper_status']['state'] == 'OPER_UP':
                            metric_value = 1
                            vs_up_count += 1
                        elif v['runtime']['oper_status']['state'] == 'OPER_DISABLED':
                            metric_value = 0
                            vs_down_count += 1
                            vs_disabled_count += 1
                        else:
                            metric_value = 0
                            vs_down_count += 1
                        temp_payload = self.payload_template.copy()
                        temp_payload['timestamp']=int(time.time())
                        temp_payload['vs_name'] = vs_name
                        temp_payload['tenant'] = t['name']
                        temp_payload['metric_type'] = 'virtualservice_operstatus'
                        temp_payload['metric_name'] = 'oper_status'
                        temp_payload['metric_value'] = metric_value
                        temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||%s||%s' %(vs_name, metric_name)
                        endpoint_payload_list.append(temp_payload)
            #----- Starting here sending VS operstatus summary info
            temp_payload = self.payload_template.copy()
            temp_payload['timestamp']=int(time.time())
            #----- Total VS
            a = temp_payload.copy()
            a['metric_name'] = 'count'
            a['metric_value'] = len(self.vs_dict) - 2
            a['metric_type'] = 'virtualservice_count'
            a['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||count'
            endpoint_payload_list.append(a)
            #----- Total VS UP
            b = temp_payload.copy()
            b['metric_type'] = 'virtualservice_up'
            b['metric_name'] = 'status_up'
            b['metric_value'] = vs_up_count
            b['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||status_up'
            endpoint_payload_list.append(b)
            #----- Total VS Down
            c = temp_payload.copy()
            c['metric_type'] = 'virtualservice_down'
            c['metric_name'] = 'status_down'
            c['metric_value'] = vs_down_count
            c['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||status_down'
            endpoint_payload_list.append(c)
            #----- Total VS Disabled
            d = temp_payload.copy()
            d['metric_type'] = 'virtualservice_disabled'
            d['metric_name'] = 'status_disabled'
            d['metric_value'] = vs_disabled_count
            d['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||status_disabled'
            endpoint_payload_list.append(d)
            send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_oper_status completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_oper_status encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)



    #-----------------------------------
    #----- RETRIEVE THE NUMBER OF ENABLED, ACTIVE, AND TOTAL POOL MEMBERS FOR EACH VIRTUAL SERVER
    def vs_active_pool_members(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            for t in self.tenants:
                if t['name'] in self.pool_dict['tenants'] and self.pool_dict['tenants'][t['name']]['count'] > 0:
                    pool_member_status = self.pool_dict['tenants'][t['name']]['results']
                    for p in pool_member_status:
                        try:
                            vs_list = []
                            if 'num_servers' in p['runtime']:
                                if 'virtualservice' in p:
                                    vs_list.append(p['virtualservice']['name'])
                                elif 'virtualservices' in p:
                                    for v in p['virtualservices']:
                                        vs_list.append(self.vs_dict[v.rsplit('/',1)[1]])
                                pool_name = p['config']['name']
                                pool_members_up = p['runtime']['num_servers_up']
                                pool_members_enabled = p['runtime']['num_servers_enabled']
                                pool_members = p['runtime']['num_servers']
                                for vs_entry in vs_list:
                                    #----- pool members enabled
                                    temp_payload = self.payload_template.copy()
                                    temp_payload['timestamp']=int(time.time())
                                    temp_payload['vs_name'] = vs_entry
                                    temp_payload['tenant'] = t['name']
                                    temp_payload['pool_name'] = pool_name
                                    temp_payload['metric_type'] = 'virtualservice_pool_members'
                                    temp_payload['metric_name'] = 'virtualservice_pool_members_enabled'
                                    temp_payload['metric_value'] = pool_members_enabled
                                    temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||%s||pool||%s||%s' %(vs_entry, pool_name, 'pool_members_enabled')
                                    endpoint_payload_list.append(temp_payload)
                                    #----- pool members up
                                    temp1_payload = self.payload_template.copy()
                                    temp1_payload['timestamp']=int(time.time())
                                    temp1_payload['vs_name'] = vs_entry
                                    temp1_payload['pool_name'] = pool_name
                                    temp1_payload['metric_type'] = 'virtualservice_pool_members'
                                    temp1_payload['metric_name'] = 'virtualservice_pool_members_up'
                                    temp1_payload['metric_value'] = pool_members_up
                                    temp1_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||%s||pool||%s||%s' %(vs_entry, pool_name, 'pool_members_up')
                                    endpoint_payload_list.append(temp1_payload)
                                    #----- pool members configured
                                    temp2_payload = self.payload_template.copy()
                                    temp2_payload['timestamp']=int(time.time())
                                    temp2_payload['vs_name'] = vs_entry
                                    temp2_payload['pool_name'] = pool_name
                                    temp2_payload['metric_type'] = 'virtualservice_pool_members'
                                    temp2_payload['metric_name'] = 'virtualservice_pool_members'
                                    temp2_payload['metric_value'] = pool_members
                                    temp2_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||%s||pool||%s||%s' %(vs_entry, pool_name, 'pool_members')
                                    endpoint_payload_list.append(temp2_payload)
                        except:
                            exception_text = traceback.format_exc()
                            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_active_pool_members completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_active_pool_members encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)







    #-----------------------------------
    #----- SE missed heartbeats
    def se_missed_hb(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            discovered_se = []
            for t in self.tenants:
                if t['name'] in self.se_dict['tenants'] and self.se_dict['tenants'][t['name']]['count'] > 0:
                    for s in self.se_dict['tenants'][t['name']]['results']:
                        if s['uuid'] not in discovered_se:
                            discovered_se.append(s['uuid'])
                            if 'hb_status' in s['runtime']:
                                temp_payload = self.payload_template.copy()
                                temp_payload['timestamp']=int(time.time())
                                temp_payload['se_name'] = s['config']['name']
                                temp_payload['tenant'] = t['name']
                                temp_payload['metric_type'] = 'serviceengine_missed_heartbeats'
                                temp_payload['metric_name'] = 'missed_heartbeats'
                                temp_payload['metric_value'] = s['runtime']['hb_status']['num_hb_misses']
                                temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||serviceengine||%s||%s' %(s['config']['name'], 'missed_heartbeats')
                                endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func se_missed_hb completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func se_missed_hb encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)






    #-----------------------------------
    #----- SE Connected State
    def se_connected(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            discovered_se = []
            for t in self.tenants:
                if t['name'] in self.se_dict['tenants'] and self.se_dict['tenants'][t['name']]['count'] > 0:
                    for s in self.se_dict['tenants'][t['name']]['results']:
                        if s['uuid'] not in discovered_se:
                            discovered_se.append(s['uuid'])
                            if 'se_connected' in s['runtime']:
                                temp_payload = self.payload_template.copy()
                                temp_payload['timestamp']=int(time.time())
                                temp_payload['se_name'] = s['config']['name']
                                temp_payload['tenant'] = t['name']
                                temp_payload['metric_type'] = 'serviceengine_connected_state'
                                temp_payload['metric_name'] = 'connected'
                                if s['runtime']['se_connected'] == True:
                                    temp_payload['metric_value'] = 1
                                else:
                                    temp_payload['metric_value'] = 0
                                temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||serviceengine||%s||%s' %(s['config']['name'], 'connected_state')
                                endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func se_connected completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func se_connected encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)






    #-----------------------------------
    def cluster_status(self):
        try:
            temp_start_time = time.time()
            cluster_status = self.avi_request('cluster/runtime','admin').json()
            endpoint_payload_list = []
            active_members = 0
            #-----------------------------------
            #---- RETURN CLUSTER MEMBER ROLE
            #---- follower = 0, leader = 1
            for c in cluster_status['node_states']:
                if c['state'] == 'CLUSTER_ACTIVE':
                    active_members = active_members + 1
                if c['role'] == 'CLUSTER_FOLLOWER':
                    member_role = 0
                elif c['role'] == 'CLUSTER_LEADER':
                    member_role = 1
                try:
                    member_name = socket.gethostbyaddr(c['name'])[0]
                except:
                    member_name = c['name']
                temp_payload = self.payload_template.copy()
                temp_payload['timestamp']=int(time.time())
                temp_payload['cluster_name'] = member_name
                temp_payload['metric_type'] = 'cluster'
                temp_payload['metric_name'] = 'member_role'
                temp_payload['metric_value'] = member_role
                temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||cluster||%s||role' %member_name
                endpoint_payload_list.append(temp_payload)
            #-----------------------------------
            #---- ADD ACTIVE MEMBER COUNT TO LIST
            temp_payload = self.payload_template.copy()
            temp_payload['timestamp']=int(time.time())
            temp_payload['metric_type'] = 'cluster'
            temp_payload['metric_name'] = 'active_members'
            temp_payload['metric_value'] = active_members
            temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||cluster||active_members'
            endpoint_payload_list.append(temp_payload)
            #----- Send metrics
            send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func cluster_status completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func cluster_status encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)




    #-----------------------------------
    def avi_subnet_usage(self):
        try:
            if datetime.now().minute % 5 == 0: #----- run every 5 mins
                 temp_start_time = time.time()
                 subnets = self.avi_request('network-inventory?page_size=1000','admin').json()['results']
                 endpoint_payload_list = []
                 if len(subnets) > 0:
                     for s in subnets:
                         if 'subnet_runtime' in s['runtime'].keys():
                             pool_size = float(s['runtime']['subnet_runtime'][0]['total_ip_count'])
                             if pool_size > 0:
                                 network_name = s['runtime']['name'].replace('|','_').replace(':','_')
                                 pool_used = float(s['runtime']['subnet_runtime'][0]['used_ip_count'])
                                 percentage_used = int((pool_used/pool_size)*100)
                                 temp_payload = self.payload_template.copy()
                                 temp_payload['timestamp']=int(time.time())
                                 temp_payload['network_name'] = network_name
                                 temp_payload['metric_type'] = 'network_usage'
                                 temp_payload['metric_name'] = 'used'
                                 temp_payload['metric_value'] = percentage_used
                                 temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||networks||%s||used' %network_name
                                 endpoint_payload_list.append(temp_payload)
                 if len(endpoint_payload_list) > 0:
                     send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
                     temp_total_time = str(time.time()-temp_start_time)
                     if args.debug == True:
                         print(str(datetime.now())+' '+self.avi_cluster_ip+': func avi_subnet_usage completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func avi_subnet_usage encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)


    #-----------------------------------
    def virtual_service_hosted_se(self):
        try:
            temp_start_time = time.time()
            vs_dict = {}
            endpoint_payload_list = []
            discovered = []
            for t in self.tenants:
                if t['name'] in self.se_dict['tenants'] and self.se_dict['tenants'][t['name']]['count'] > 0:
                    for s in self.se_dict['tenants'][t['name']]['results']:
                        se_name = s['config']['name']
                        if 'virtualservice_refs' in s['config']:
                            for e in s['config']['virtualservice_refs']:
                                vs_name = self.vs_dict[e.split('/api/virtualservice/')[1]]
                                temp_payload = self.payload_template.copy()
                                temp_payload['timestamp']=int(time.time())
                                temp_payload['se_name'] = se_name
                                temp_payload['vs_name'] = vs_name
                                temp_payload['tenant'] = t['name']
                                temp_payload['metric_type'] = 'virtualservice_hosted_se'
                                temp_payload['metric_name'] = 'hosting_se'
                                temp_payload['metric_value'] = 1
                                temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||%s||serviceengine||%s' %(vs_name, se_name)
                                if temp_payload not in discovered:
                                    discovered.append(temp_payload)
                                    endpoint_payload_list.append(temp_payload)
                        elif 'vs_uuids' in s['config']: #---- 17.2.4 api changed
                            for e in s['config']['vs_uuids']:
                                vs_name = self.vs_dict[e.rsplit('api/virtualservice/')[1]]
                                temp_payload = self.payload_template.copy()
                                temp_payload['timestamp']=int(time.time())
                                temp_payload['se_name'] = se_name
                                temp_payload['vs_name'] = vs_name
                                temp_payload['tenant'] = t['name']
                                temp_payload['metric_type'] = 'virtualservice_hosted_se'
                                temp_payload['metric_name'] = 'hosting_se'
                                temp_payload['metric_value'] = 1
                                temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||%s||serviceengine||%s' %(vs_name, se_name)
                                if temp_payload not in discovered:
                                    discovered.append(temp_payload)
                                    endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func virtual_service_hosted_se completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func virtual_service_hosted_se encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)




    #-----------------------------------
    def vs_primary_se(self):
        try:
            temp_start_time = time.time()
            discovered_vs = []
            discovered_se = []
            endpoint_payload_list = []
            for t in self.tenants:
                if t['name'] in self.vs_dict['tenants'] and self.vs_dict['tenants'][t['name']]['count'] > 0:
                    for v in self.vs_dict['tenants'][t['name']]['results']:
                        if v['uuid'] not in discovered_vs:
                            for a in v['runtime']['vip_summary']:
                                if 'service_engine' in a:
                                    for s in a['service_engine']:
                                        if s['primary'] == True:
                                            discovered_vs.append(v['uuid'])
                                            se_name = self.se_dict[s['uuid']]
                                            vs_name = v['config']['name']
                                            temp_payload = self.payload_template.copy()
                                            temp_payload['timestamp']=int(time.time())
                                            temp_payload['vs_name'] = vs_name
                                            temp_payload['tenant'] = t['name']
                                            temp_payload['se_name'] = se_name
                                            temp_payload['metric_type'] = 'virtualservice_primary_se'
                                            temp_payload['metric_name'] = 'primary_se'
                                            temp_payload['metric_value'] = 1
                                            temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||%s||primary_se||%s' %(vs_name,se_name)
                                            endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func virtual_service_primary_se completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func virtual_service_primary_se encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)




    #-----------------------------------
    def license_usage(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            licensing = self.avi_request('licenseusage?limit=1&step=300','admin').json()
            lic_cores = licensing['licensed_cores']
            if lic_cores != None:
                cores_used = licensing['num_se_vcpus']
                percentage_used = (cores_used / float(lic_cores))*100
                temp_payload = self.payload_template.copy()
                temp_payload['timestamp']=int(time.time())
                temp_payload['metric_type'] = 'licensing'
                temp_payload['metric_name'] = 'licensed_cores'
                temp_payload['metric_value'] = lic_cores
                temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||licensing||licensed_cores'
                endpoint_payload_list.append(temp_payload)
                #-----
                temp1_payload = self.payload_template.copy()
                temp1_payload['timestamp']=int(time.time())
                temp1_payload['metric_type'] = 'licensing'
                temp1_payload['metric_name'] = 'cores_used'
                temp1_payload['metric_value'] = cores_used
                temp1_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||licensing||cores_used'
                endpoint_payload_list.append(temp1_payload)
                #-----
                temp2_payload = self.payload_template.copy()
                temp2_payload['timestamp']=int(time.time())
                temp2_payload['metric_type'] = 'licensing'
                temp2_payload['metric_name'] = 'percentage_used'
                temp2_payload['metric_value'] = percentage_used
                temp2_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||licensing||percentage_used'
                endpoint_payload_list.append(temp2_payload)
                temp_total_time = str(time.time()-temp_start_time)
                send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
                if args.debug == True:
                    print(str(datetime.now())+' '+self.avi_cluster_ip+': func license_usage completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func license_usage encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)





    #-----------------------------------
    def service_engine_vs_capacity(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            se_group_max_vs = {}
            discovered_vs = []
            se_vs = {}
            for t in self.tenants:
                if t['name'] in self.seg_dict['tenants'] and self.seg_dict['tenants'][t['name']]['count'] > 0:
                    for g in self.seg_dict['tenants'][t['name']]['results']:
                        se_group_max_vs[g['uuid']] = float(g['config']['max_vs_per_se'])
            for t in self.tenants:
                if t['name'] in self.se_dict['tenants'] and self.se_dict['tenants'][t['name']]['count'] > 0:
                    for s in self.se_dict['tenants'][t['name']]['results']:
                        se_name = s['config']['name']
                        if se_name not in se_vs:
                            max_vs = se_group_max_vs[s['config']['se_group_ref'].rsplit('api/serviceenginegroup/')[1]]
                            se_vs[se_name]={'max_vs': max_vs, 'total_vs':0, 'tenant':t['name']}
                        if 'virtualservice_refs' in s['config']:
                            for v in s['config']['virtualservice_refs']:
                                if se_name+v.rsplit('api/virtualservice/')[1] not in discovered_vs:
                                    discovered_vs.append(s['config']['name']+v.rsplit('api/virtualservice/')[1])
                                    se_vs[se_name]['total_vs'] += 1
                                    se_vs[se_name]['tenant'] = t['name']
            for entry in se_vs:
                vs_percentage_used = (se_vs[entry]['total_vs']/se_vs[entry]['max_vs'])*100
                temp_payload = self.payload_template.copy()
                temp_payload['timestamp']=int(time.time())
                temp_payload['se_name'] = entry
                temp_payload['metric_type'] = 'serviceengine_capacity'
                temp_payload['metric_name'] = 'vs_capacity_used'
                temp_payload['metric_value'] = vs_percentage_used
                temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||serviceengine||%s||vs_capacity_used' %entry
                endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func service_engine_vs_capacity completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func service_engine_vs_capacity encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)






    #-----------------------------------
    def license_expiration(self):
        try:
            if datetime.now().hour % 6 == 0: #----- run once every 6 hours
                current_time = datetime.today()
                temp_start_time = time.time()
                licenses = self.avi_request('license','admin').json()
                for l in licenses['licenses']:
                    license_id = l['license_id']
                    try:
                        expires = datetime.strptime(l['valid_until'],"%Y-%m-%d %H:%M:%S")
                    except:
                        expires = datetime.strptime(l['valid_until'],"%Y-%m-%dT%H:%M:%S")
                    days_to_expire = (expires - current_time).days
                    endpoint_payload_list = []
                    temp_payload = self.payload_template.copy()
                    temp_payload['timestamp']=int(time.time())
                    temp_payload['license_id'] = license_id
                    temp_payload['metric_type'] = 'license'
                    temp_payload['metric_name'] = 'license_expiration'
                    temp_payload['metric_value'] = days_to_expire
                    temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||licensing||expiration_days||'+license_id
                    endpoint_payload_list.append(temp_payload)
                    send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
                temp_total_time = str(time.time()-temp_start_time)
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func license_expiration completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func license_expiration encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)





    #-----------------------------------
    #----- GET AVI SOFTWARE VERSION NUMBER AND ASSIGN VALUE OF 1
    def get_avi_version(self):
        try:
            temp_start_time = time.time()
            #current_version = self.login.json()['version']['Version']+'('+str(self.login.json()['version']['build'])+')'
            current_version = self.login.json()['version']['Version']
            endpoint_payload_list = []
            temp_payload = self.payload_template.copy()
            temp_payload['timestamp']=int(time.time())
            temp_payload['metric_type'] = 'version'
            temp_payload['metric_name'] = 'current_version'
            temp_payload['version'] = current_version
            temp_payload['metric_value'] = 1
            temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||current_version||%s' %current_version
            endpoint_payload_list.append(temp_payload)
            send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            if args.debug == True:
                temp_total_time = str(time.time()-temp_start_time)
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func get_avi_version completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': get_avi_version encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)




    #-----------------------------------
    #----- GET Pool Member specific statistics
    def pool_server_stats(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            discovered_servers = []
            try:
                for t in self.tenants:
                    payload = {
                        "metric_requests": [
                            {
                                "step": 300,
                                "limit": 1,
                                "aggregate_entity": False,
                                "entity_uuid": "*",
                                "obj_id": "*",
                                "pool_uuid": "*",
                                "id": "collItemRequest:AllServers",
                                "metric_id": self.pool_server_metric_list
                            }
                            ]}
                    api_url = 'analytics/metrics/collection?pad_missing_data=false&dimension_limit=1000&include_name=true&include_refs=true'
                    resp = self.avi_post(api_url,t['name'],payload)
                    if 'series' in resp.json():
                        if len(resp.json()['series']['collItemRequest:AllServers']) != 0:
                            for p in resp.json()['series']['collItemRequest:AllServers']:
                                if p not in discovered_servers:
                                    discovered_servers.append(p)
                                    server_object = p.split(',')[2]
                                    for d in resp.json()['series']['collItemRequest:AllServers'][p]:
                                        if 'data' in d:
                                            pool_name = d['header']['pool_ref'].rsplit('#',1)[1]                                            
                                            metric_name = d['header']['name']
                                            temp_payload = self.payload_template.copy()
                                            temp_payload['timestamp']=int(time.time())
                                            temp_payload['pool_name'] = pool_name
                                            temp_payload['tenant'] = t['name']
                                            temp_payload['pool_member'] = server_object
                                            temp_payload['metric_type'] = 'pool_member_metrics'
                                            temp_payload['metric_name'] = metric_name
                                            temp_payload['metric_value'] = d['data'][0]['value']
                                            if 'entity_ref' in d['header']:
                                                vs_name = d['header']['entity_ref'].rsplit('#',1)[1]
                                                temp_payload['vs_name'] = vs_name
                                                temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||%s||pool||%s||%s||%s' %(vs_name, pool_name, server_object,metric_name)
                                                endpoint_payload_list.append(temp_payload)
                                            else:
                                                for x in self.pool_dict['tenants'][t['name']]['results']:
                                                    if x['config']['name'] == pool_name:
                                                        for v in x['virtualservices']:
                                                            vs_name = self.vs_dict[v.split('/api/virtualservice/')[1]]
                                                            temp_payload1 = temp_payload.copy()
                                                            temp_payload1['vs_name'] = vs_name
                                                            temp_payload1['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||virtualservice||%s||pool||%s||%s||%s' %(vs_name, pool_name, server_object,metric_name)
                                                            endpoint_payload_list.append(temp_payload1)
            except:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func pool_server_metrics encountered an error for tenant '+t['name'])
                exception_text = traceback.format_exc()
                print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': pool_server_metrics, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func pool_server_metrics encountered an error encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)




    #-----------------------------------
    #----- GET customer Member specific statistics
    def controller_cluster_metrics(self):
        try:
            temp_start_time = time.time()
            major,minor = self.login.json()['version']['Version'].rsplit('.',1)
            if (float(major) >= 17.2 and float(minor) >= 5) or float(major) >= 18.1: #----- controller metrics api introduced in 17.2.5
                cluster= self.avi_request('cluster','admin').json()
                cluster_nodes = {}
                temp_list=[]
                endpoint_payload_list = []
                for c in cluster['nodes']:
                    cluster_nodes[c['vm_uuid']]=c['ip']['addr']
                    #cluster_nodes[c['vm_uuid']]=c['vm_hostname']
                    resp = self.avi_request('analytics/metrics/controller/%s/?metric_id=%s&limit=1&step=300&?aggregate_entity=False' %(c['vm_uuid'],self.controller_metric_list),'admin').json()
                    temp_list.append(resp)
                for n in temp_list:
                    node = cluster_nodes[n['entity_uuid']]
                    for m in n['series']:
                        metric_name = m['header']['name']
                        temp_payload = self.payload_template.copy()
                        temp_payload['timestamp']=int(time.time())
                        temp_payload['cluster_node'] = node
                        temp_payload['metric_type'] = 'controller_metrics'
                        temp_payload['metric_name'] = metric_name
                        temp_payload['metric_value'] = m['data'][0]['value']
                        temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||controller||%s||%s' %(node,metric_name)
                        endpoint_payload_list.append(temp_payload)
                if len(endpoint_payload_list) > 0:
                    send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
            else:
                pass
            temp_total_time = str(time.time()-temp_start_time)
            if args.debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': controller_cluster_metrics, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func controller_cluster_metrics encountered an error encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)









#-----------------------------------
#-----------------------------------
#-----------------------------------

    #-----------------------------------
    #----- This is the method within the class that will execute the other methods.
    #----- all test methods will need to be added to test_functions list to be executed
    def gather_metrics(self):
        try:
            start_time = time.time()
            self.login = self.avi_login()
            self.tenants = self.login.json()['tenants']
            self.avi_controller = self.controller_to_poll()
            print '=====> Chose '+self.avi_controller
            self.vs_dict, self.se_dict, self.pool_dict, self.seg_dict = self.gen_inventory_dict()
            #---- remove metrics that are not available in the current version
            self.vs_metric_list, self.se_metric_list, self.controller_metric_list, self.pool_server_metric_list = self.remove_version_specific_metrics()
            #-----------------------------------
            #----- Add Test functions to list for threaded execution
            #-----------------------------------
            test_functions = []
            test_functions.append(self.virtual_service_stats_threaded)
            test_functions.append(self.vs_metrics_per_se_threaded)
            test_functions.append(self.srvc_engn_stats)
            test_functions.append(self.srvc_engn_vs_count)
            test_functions.append(self.srvc_engn_count)
            test_functions.append(self.vs_se_healthscores)
            test_functions.append(self.vs_oper_status)
            test_functions.append(self.se_missed_hb)
            test_functions.append(self.vs_active_pool_members)
            test_functions.append(self.cluster_status)
            test_functions.append(self.avi_subnet_usage)
            test_functions.append(self.virtual_service_hosted_se)
            test_functions.append(self.license_usage)
            test_functions.append(self.service_engine_vs_capacity)
            test_functions.append(self.license_expiration)
            test_functions.append(self.get_avi_version)
            test_functions.append(self.pool_server_stats)
            test_functions.append(self.controller_cluster_metrics)
            test_functions.append(self.se_connected)
            test_functions.append(self.vs_primary_se)
            #-----------------------------------
            #-----------------------------------
            #-----
            #-----------------------------------
            #----- BEGIN Running Test Functions
            #-----------------------------------
            proc = []
            for f in test_functions:
                p = Process(target = f, args = ())
                p.start()
                proc.append(p)
            for p in proc:
                p.join()
            #-----------------------------------
            #-----
            #-----------------------------------
            #----- Log time it took to execute script
            #-----------------------------------
            total_time = str(time.time()-start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': controller specific tests have completed, executed in '+total_time+' seconds')
            endpoint_payload_list = []
            temp_payload = self.payload_template.copy()
            temp_payload['timestamp']=int(time.time())
            temp_payload['metric_type'] = 'metricscript'
            temp_payload['metric_name'] = 'execution_time'
            temp_payload['metric_value'] = float(total_time)*1000
            temp_payload['name_space'] = 'avi||'+self.host_location+'||'+self.host_environment+'||'+self.avi_cluster_ip+'||metricscript||executiontime'
            endpoint_payload_list.append(temp_payload)
            send_metriclist_to_endpoint(endpoint_list, endpoint_payload_list)
        except:
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' Unable to login to: '+self.avi_cluster_ip)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)



    #--- THIS METHOD KICKS OFF THE EXECUTION
    def run(self):
        self.gather_metrics()



    #-----------------------------------
    #-----------------------------------
    #-----------------------------------


#--- Primary function to execute the metrics gathering
#--- This function will create a avi_metrics object for each controller
#--- and kick off the metrics gathering for them.
def main():
    start_time = time.time()
    proc = []
    for entry in avi_controller_list:
        avi_controller = entry['avi_controller']
        host_location = entry['location']
        host_environment = entry['environment']
        c = avi_metrics(avi_controller, host_location, host_environment, entry['avi_user'], isBase64(entry['avi_pass']))
        p = Process(target = c.run, args = ())
        p.start()
        proc.append(p)
    for p in proc:
        p.join()
    total_time = str(time.time()-start_time)
    print(str(datetime.now())+' AVI_SCRIPT: metric script has completed, executed in '+total_time+' seconds')






#----- START SCRIPT EXECUTION
#----- check for docker environment Variable
#----- if docker environment, runs as while loop
if 'EN_DOCKER' in os.environ:
    if 'EN_NOREALTIME' in os.environ:
        args.norealtime = True
    #----- Metrics db server
    fdir = os.path.abspath(os.path.dirname(__file__))
    args.metrics = (os.environ['EN_METRIC_ENDPOINT'].replace(' ','').lower().split(':'))
    endpoint_list = determine_endpoint_type()
    while True:
        loop_start_time = time.time()
        with open('avi_controllers.json') as amc:
            avi_controller_list = json.load(amc)['controllers']
        main()
        loop_total_time = time.time()-loop_start_time
        if loop_total_time < 60:
            print(str(datetime.now())+' AVI_SCRIPT: sleeping for '+str(60 - datetime.now().second)+' seconds')
            time.sleep(60 - datetime.now().second)
else:
    #----- Get the file path to import controllers, needed for cron
    fdir = os.path.abspath(os.path.dirname(__file__))
    #----- Import avi controller info from json file
    with open(os.path.join(fdir,'avi_controllers.json')) as amc:
        avi_controller_list = json.load(amc)['controllers']
    #----- Import endpoint info from json files
    endpoint_list = determine_endpoint_type()
    main()
