#!/usr/bin/python


version = 'v2018-04-12'

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
import cPickle as pickle




#----- Logging Information
logging_enabled = True   #---True/False
enable_debug = True   #---True/False, default logging is ERROR
fdir = os.path.abspath(os.path.dirname(__file__))
log_file = fdir+'/avi_metrics.log'






#----- Send value to appdynamics
def send_value_appdynamics(name, value, timestamp):
    print('name=Custom Metrics|%s,value=%d,aggregator=OBSERVATION,time-rollup=CURRENT,cluster-rollup=INDIVIDUAL' % (name.replace('.','|'), long(value)))



#----- This function is used to loop through a list of Classes and send to
#----- appdynamics.
#-----    1.  name_space
#-----    2.  value
#-----    3.  timestamp
def send_class_list_appdynamics(class_list):
    for entry in class_list:
        print('name=Custom Metrics|%s,value=%d,aggregator=OBSERVATION,time-rollup=CURRENT,cluster-rollup=INDIVIDUAL' % (entry.name_space.replace('.','|'), long(entry.value)))




#----- This function allows for passwords to be either plaintext or base64 encoded
def isBase64(password):
    try:
        if base64.b64encode(base64.b64decode(password)) == password:
            return base64.b64decode(password)
        else:
            return password
    except Exception:
        return password




#----- This class is where all the test methods/functions exist and are executed
class avi_metrics():
    def __init__(self,avi_controller,host_location,host_environment, avi_user, avi_pass):
        self.avi_cluster_ip = avi_controller
        self.avi_controller = avi_controller
        self.host_location = host_location
        self.host_environment = host_environment
        self.avi_user = avi_user
        self.avi_pass = avi_pass
        #------
        vs_metric_list  = [
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
        self.vs_metric_list = ','.join(vs_metric_list)
        se_metric_list = [
            'se_if.avg_bandwidth',
            'se_stats.avg_connection_mem_usage',
            'se_stats.avg_connections',
            'se_stats.avg_connections_dropped',
            'se_stats.avg_cpu_usage',
            'se_stats.avg_disk1_usage',
            'se_stats.avg_mem_usage',
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
        self.se_metric_list = ','.join(se_metric_list)
        controller_metric_list  = [
            'controller_stats.avg_cpu_usage',
            'controller_stats.avg_disk_usage',
            'controller_stats.avg_mem_usage']
        self.controller_metric_list = ','.join(controller_metric_list)
        controller_process_metric_list = [
            'process_stats.avg_rss',
            'process_stats.avg_swap',
            'process_stats.max_cpu_pct',
            'process_stats.avg_num_threads',
            'process_stats.avg_fds',
            'process_stats.avg_pss',
            'process_stats.avg_vms']
        self.controller_process_metric_list = ','.join(controller_process_metric_list)
        #----
        pool_server_metric_list = [
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
        self.pool_server_metric_list = ','.join(pool_server_metric_list)



    def avi_login(self):
        try:
            login = pickle.load(open((os.path.join(fdir,self.avi_cluster_ip)),'rb'))
            for c in login.cookies:
                expires = c.expires
            headers = ({"X-Avi-Tenant": "admin", 'content-type': 'application/json'})
            resp = requests.get('https://%s/api/cluster' %self.avi_cluster_ip, verify=False, headers = headers,cookies=dict(sessionid= login.cookies['sessionid']),timeout=5)
            #if expires > time.time():
            if resp.status_code() == 200:
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
                vs_inv = self.avi_request('virtualservice-inventory?page_size=1000','*').json()
                vs_total_pages = (vs_inv['count']/1000) + (vs_inv['count'] % 1000 > 0)
                page_number = 1
                while vs_total_pages > page_number:
                    page_number += 1
                    resp = self.avi_request('virtualservice-inventory?page_size=1000&page='+page_number,'*').json()
                    vs_inv['results'].append(resp['results'])
                #------------------
                se_inv = self.avi_request('serviceengine-inventory?page_size=1000','*').json()
                #------------------
                pool_inv = self.avi_request('pool-inventory?page_size=1000','*').json()
                pool_total_pages = (pool_inv['count']/1000) + (pool_inv['count'] % 1000 > 0)
                page_number = 1
                while pool_total_pages > page_number:
                    page_number += 1
                    resp = self.avi_request('pool-inventory?page_size=1000&page='+page_number,'*').json()
                    pool_inv['results'].append(resp['results'])
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
                    vs_inv = self.avi_request('virtualservice-inventory?page_size=1000',t['name']).json()
                    vs_total_pages = (vs_inv['count']/1000) + (vs_inv['count'] % 1000 > 0)
                    page_number = 1
                    while vs_total_pages > page_number:
                        page_number += 1
                        resp = self.avi_request('virtualservice-inventory?page_size=1000&page='+page_number,t['name']).json()
                        vs_inv['results'].append(resp['results'])
                    #------------------
                    se_inv = self.avi_request('serviceengine-inventory?page_size=1000',t['name']).json()
                    #------------------
                    pool_inv = self.avi_request('pool-inventory?page_size=1000',t['name']).json()
                    pool_total_pages = (pool_inv['count']/1000) + (pool_inv['count'] % 1000 > 0)
                    page_number = 1
                    while pool_total_pages > page_number:
                        page_number += 1
                        resp = self.avi_request('pool-inventory?page_size=1000&page='+page_number,'*').json()
                        pool_inv['results'].append(resp['results'])
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
            if enable_debug == True:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func gen_inventory_dict completed, executed in '+temp_total_time+' seconds')
            return vs_dict, se_dict, pool_dict, seg_dict
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func gen_inventory_dict encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)
            sys.exit(1)





    #-----------------------------------
    #----- Add Test functions
    #-----------------------------------
    def srvc_engn_vs_count(self):
        try:
            temp_start_time = time.time()
            discovered_vs = []  #--- this is used b/c vs in admin show up in other tenants
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
                for entry in srvc_engn_dict:
                    send_value_appdynamics('avi.'+self.avi_controller.replace('.','_')+'.serviceengine.%s.vs_count' %entry.replace('.','_'), srvc_engn_dict[entry], int(time.time()))
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': func srvc_engn_vs_count completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func srvc_engn_vs_count encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)

    #-----------------------------------

    def srvc_engn_count(self):
        try:
            temp_start_time = time.time()
            discovered_ses = []  #--- this is used b/c se in admin show up in other tenants
            se_count = len(self.se_dict) - 2
            send_value_appdynamics('avi.'+self.avi_controller.replace('.','_')+'.serviceengine.count',se_count, int(time.time()))
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': func srvc_engn_count completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func srvc_engn_count encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)


    #-----------------------------------

    def srvc_engn_stats(self):
        try:
            temp_start_time = time.time()
            appdynamics_class_list = []
            discovered_ses = []  #--- this is used b/c se in admin show up in other tenants
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
                                        class appdynamics_class(): pass
                                        metric_name = entry['header']['name'].replace('.','_')
                                        metric_value = entry['data'][0]['value']
                                        x = appdynamics_class
                                        x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.serviceengine.%s.%s' %(se_name.replace('.','_'), metric_name)
                                        x.value = metric_value
                                        x.timestamp = int(time.time())
                                        appdynamics_class_list.append(x)
            if len(appdynamics_class_list) > 0:
                send_class_list_appdynamics(appdynamics_class_list)
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': func srvc_engn_stats completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func srvc_engn_stats encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)


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
            appdynamics_class_list = []
            vs_dict= {}
            #-----
            if tenant in self.vs_dict['tenants'] and self.vs_dict['tenants'][tenant]['count'] > 0:
                endpoint_payload_list = []
                payload =  {'metric_requests': [{'step' : 300, 'limit': 1, 'id': 'allvs', 'entity_uuid' : '*', 'metric_id': self.vs_metric_list}]}
                vs_stats = self.avi_post('analytics/metrics/collection?pad_missing_data=false', tenant, payload).json()
                #----- this pulls 1 min avg stats for vs that have realtime stats enabled
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
                            class appdynamics_class(): pass #----- class will be used to create a list for optimized graphite metric sending
                            metric_name = m['header']['name'].replace('.','_')
                            if 'data' in m:
                                metric_value = m['data'][0]['value']
                                x = appdynamics_class
                                x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.virtualservice.%s.%s' %(vs_name, metric_name)
                                x.value = metric_value
                                x.timestamp = int(time.time())
                                appdynamics_class_list.append(x)
                if len(appdynamics_class_list) > 0:
                    send_class_list_appdynamics(appdynamics_class_list)
            #-----------------------------------
            #----- SEND SUM OF VS_COUNT LIST - TOTAL NUMBER OF VS
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': func virtual_service_stats completed for tenant: '+tenant+', executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func virtual_service_stats encountered an error for tenant'+tenant)
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)



    def vs_metrics_per_se_threaded(self):
        try:
            temp_start_time = time.time()
            major,minor = self.login.json()['version']['Version'].rsplit('.',1)
            if float(major) >= 17.2 and float(minor) >= 8: #----- controller metrics api introduced in 17.2.5
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
                if enable_debug == True:
                    logging.info(self.avi_controller+': func vs_metrics_per_se_threaded completed, executed in '+temp_total_time+' seconds')
        except:
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)





    def vs_metrics_per_se(self,tenant):
        try:
            temp_start_time = time.time()
            appdynamics_class_list = []
            payload =  {'metric_requests': [{'step' : 300, 'limit': 1, 'id': 'vs_metrics_by_se', 'entity_uuid' : '*', 'serviceengine_uuid': '*', 'include_refs': True, 'metric_id': self.vs_metric_list}]}
            vs_stats = self.avi_post('analytics/metrics/collection?pad_missing_data=false', tenant, payload).json()
            #----- this will pull 1 min stats for vs that have realtime stat enabled
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
                                class appdynamics_class(): pass
                                se_name = self.se_dict[d['header']['serviceengine_ref'].split('serviceengine/')[1]]
                                metric_name = d['header']['name'].replace('.','_')
                                metric_value = d['data'][0]['value']
                                x = appdynamics_class
                                x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.serviceengine.%s.virtualservice_stats.%s.%s' %(se_name.replace('.','_'),vs_name,metric_name)
                                x.value = metric_value
                                x.timestamp = int(time.time())
                                appdynamics_class_list.append(x)
                if len(appdynamics_class_list) > 0:
                    send_class_list_appdynamics(appdynamics_class_list)
                temp_total_time = str(time.time()-temp_start_time)
                if enable_debug == True:
                    logging.info(self.avi_controller+': func vs_metrics_per_se completed for se '+se_dict[se]+' tenant: '+tenant+', executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func vs_metrics_per_se for se '+se_dict[se]+' tenant: '+tenant+', encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)








    #----- PULL VS HEALTHSCORES
    def vs_se_healthscores(self):
        #----- PULL VS HEALTHSCORES
        try:
            temp_start_time = time.time()
            appdynamics_class_list = []
            discovered_vs = []
            discovered_se = []
            endpoint_payload_list = []
            for t in self.tenants:
                if t['name'] in self.vs_dict['tenants'] and self.vs_dict['tenants'][t['name']]['count'] > 0:
                    for v in self.vs_dict['tenants'][t['name']]['results']:
                        if v['uuid'] not in discovered_vs:
                            vs_name = v['config']['name'].replace('.','_')
                            vs_healthscore = v['health_score']['health_score']
                            class appdynamics_class(): pass #----- class will be used to create a list for optimized graphite metric sending
                            x = appdynamics_class
                            x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.virtualservice.%s.healthscore' %vs_name
                            x.value = vs_healthscore
                            x.timestamp = int(time.time())
                            appdynamics_class_list.append(x)
                if t['name'] in self.se_dict['tenants'] and self.se_dict['tenants'][t['name']]['count'] > 0:
                    for s in self.se_dict['tenants'][t['name']]['results']:
                        if s['uuid'] not in discovered_se:
                            discovered_se.append(s['uuid'])
                            se_name = self.se_dict[s['uuid']]
                            se_healthscore = s['health_score']['health_score']
                            class appdynamics_class(): pass #----- class will be used to create a list for optimized graphite metric sending
                            y = appdynamics_class
                            y.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.serviceengine.%s.healthscore' %se_name
                            y.value = se_healthscore
                            y.timestamp = int(time.time())
                            appdynamics_class_list.append(y)
            if len(send_class_list_appdynamics) > 0:
                send_class_list_appdynamics(appdynamics_class_list)
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': func vs_healthscores completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func vs_healthscores encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)




    def vs_oper_status(self):
        #----- PULL VS UP/DOWN STATUS
        try:
            temp_start_time = time.time()
            appdynamics_class_list = []
            vs_up_count = 0
            vs_down_count = 0
            vs_disabled_count = 0
            vs_count = 0
            for t in self.tenants:
                if t['name'] in self.vs_dict['tenants'] and self.vs_dict['tenants'][t['name']]['count'] > 0:
                    for v in self.vs_dict['tenants'][t['name']]['results']:
                        class appdynamics_class(): pass
                        vs_name = v['config']['name'].replace('.','_')
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
                        x = appdynamics_class
                        x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.virtualservice.%s.%s' %(vs_name, metric_name)
                        x.value = metric_value
                        x.timestamp = int(time.time())
                        appdynamics_class_list.append(x)
            send_value_appdynamics('avi.'+self.avi_controller.replace('.','_')+'.virtualservice.count', vs_count, int(time.time()))
            send_value_appdynamics('avi.'+self.avi_controller.replace('.','_')+'.virtualservice.status_up', vs_up_count, int(time.time()))
            send_value_appdynamics('avi.'+self.avi_controller.replace('.','_')+'.virtualservice.status_down', vs_down_count, int(time.time()))
            send_value_appdynamics('avi.'+self.avi_controller.replace('.','_')+'.virtualservice.status_disabled', vs_disabled_count, int(time.time()))
            send_class_list_appdynamics(appdynamics_class_list)
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': func vs_oper_status completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func vs_oper_status encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)



    #-----------------------------------
    #----- RETRIEVE THE NUMBER OF ENABLED, ACTIVE, AND TOTAL POOL MEMBERS FOR EACH VIRTUAL SERVER
    def vs_active_pool_members(self):
        try:
            temp_start_time = time.time()
            appdynamics_class_list = []
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
                                pool_name = p['config']['name'].replace('.','_')
                                pool_members_up = p['runtime']['num_servers_up']
                                pool_members_enabled = p['runtime']['num_servers_enabled']
                                pool_members = p['runtime']['num_servers']
                                for vs_entry in vs_list:
                                    class appdynamics_class(): pass #----- class will be used to create a list for optimized graphite metric sending
                                    x = appdynamics_class
                                    x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.virtualservice.%s.pool.%s.%s' %(vs_entry, pool_name, 'pool_members_enabled')
                                    x.value = pool_members_enabled
                                    x.timestamp = int(time.time())
                                    appdynamics_class_list.append(x)
                                    class appdynamics_class(): pass #----- class will be used to create a list for optimized graphite metric sending
                                    y = appdynamics_class
                                    y.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.virtualservice.%s.pool.%s.%s' %(vs_entry, pool_name, 'pool_members_up')
                                    y.value = pool_members_up
                                    y.timestamp = int(time.time())
                                    appdynamics_class_list.append(y)
                                    class appdynamics_class(): pass #----- class will be used to create a list for optimized graphite metric sending
                                    z = appdynamics_class
                                    z.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.virtualservice.%s.pool.%s.%s' %(vs_entry, pool_name, 'pool_members')
                                    z.value = pool_members
                                    z.timestamp = int(time.time())
                                    appdynamics_class_list.append(z)
                        except:
                            exception_text = traceback.format_exc()
                            logging.exception(self.avi_controller+': '+exception_text)
            if len(appdynamics_class_list) > 0:
                send_class_list_appdynamics(appdynamics_class_list)
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': func vs_active_pool_members completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func vs_active_pool_members encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)


    #-----------------------------------
    #----- called by service_engine_stats function
    def se_missed_hb(self):
        try:
            temp_start_time = time.time()
            appdynamics_class_list = []
            discovered_se = []
            for t in self.tenants:
                if t['name'] in self.se_dict['tenants'] and self.se_dict['tenants'][t['name']]['count'] > 0:
                    for s in self.se_dict['tenants'][t['name']]['results']:
                        if s['uuid'] not in discovered_se:
                            discovered_se.append(s['uuid'])
                            if 'hb_status' in s['runtime']:
                                class appdynamics_class(): pass
                                x = appdynamics_class
                                se_name = s['config']['name']
                                x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.serviceengine.%s.%s' %(se_name.replace('.','_'), 'missed_heartbeats')
                                x.value = s['runtime']['hb_status']['num_hb_misses']
                                x.timestamp = int(time.time())
                                appdynamics_class_list.append(x)
            if len(appdynamics_class_list) > 0:
                send_class_list_appdynamics(appdynamics_class_list)
        except:
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)




    #-----------------------------------
    def cluster_status(self):
        try:
            temp_start_time = time.time()
            cluster_status = self.avi_request('cluster/runtime','admin').json()
            appdynamics_class_list = []
            active_members = 0
            #-----------------------------------
            #---- RETURN CLUSTER MEMBER ROLE
            #---- follower = 0, leader = 1
            for c in cluster_status['node_states']:
                class appdynamics_class: pass
                if c['state'] == 'CLUSTER_ACTIVE':
                    active_members = active_members + 1
                if c['role'] == 'CLUSTER_FOLLOWER':
                    member_role = 0
                elif c['role'] == 'CLUSTER_LEADER':
                    member_role = 1
                try:
                    member_name = socket.gethostbyaddr(c['name'])[0].replace('.','_')
                except:
                    member_name = c['name'].replace('.','_')
                x = appdynamics_class
                x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.cluster.%s.role' %member_name
                x.value = member_role
                x.timestamp = int(time.time())
                appdynamics_class_list.append(x)
            #-----------------------------------
            #---- ADD ACTIVE MEMBER COUNT TO LIST
            class appdynamics_class: pass
            x = appdynamics_class
            x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.cluster.active_members'
            x.value = active_members
            x.timestamp = int(time.time())
            appdynamics_class_list.append(x)
            send_class_list_appdynamics(appdynamics_class_list)
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': func cluster_status completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func cluster_status encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)




    #-----------------------------------
    def avi_subnet_usage(self):
        try:
            if datetime.now().minute % 5 == 0: #----- run every 5 mins
                 temp_start_time = time.time()
                 appdynamics_class_list = []
                 subnets = self.avi_request('network-inventory?page_size=1000','admin').json()['results']
                 endpoint_payload_list = []
                 if len(subnets) > 0:
                     for s in subnets:
                         if 'subnet_runtime' in s['runtime'].keys():
                             pool_size = float(s['runtime']['subnet_runtime'][0]['total_ip_count'])
                             if pool_size > 0:
                                 class appdynamics_class(): pass
                                 x = appdynamics_class
                                 network_name = s['name'].replace('|','_').replace(':','_').replace('.','-')
                                 pool_size = float(s['subnet_runtime'][0]['total_ip_count'])
                                 pool_used = float(s['subnet_runtime'][0]['used_ip_count'])
                                 percentage_used = int((pool_used/pool_size)*100)
                                 x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.networks.%s.used' %network_name
                                 x.value = percentage_used
                                 x.timestamp = int(time.time())
                                 appdynamics_class_list.append(x)
            if len(appdynamics_class_list) > 0:
                send_class_list_appdynamics(appdynamics_class_list)
                temp_total_time = str(time.time()-temp_start_time)
                if enable_debug == True:
                    logging.info(self.avi_controller+': func avi_subnet_usage completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func avi_subnet_usage encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)




    #-----------------------------------
    def virtual_service_hosted_se(self):
        try:
            temp_start_time = time.time()
            vs_dict = {}
            appdynamics_class_list = []
            discovered = []
            for t in self.tenants:
                if t['name'] in self.se_dict['tenants'] and self.se_dict['tenants'][t['name']]['count'] > 0:
                    for s in self.se_dict['tenants'][t['name']]['results']:
                        se_name = s['config']['name']
                        if 'virtualservice_refs' in s['config']:
                            for e in s['config']['virtualservice_refs']:
                                vs_name = self.vs_dict[e.split('/api/virtualservice/')[1]].replace('.','_')
                                class appdynamics_class(): pass
                                x = appdynamics_class
                                x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.virtualservice.%s.serviceengine.%s' %(vs_name, se_name.replace('.','_'))
                                x.value = 1
                                if x not in discovered:
                                    discovered.append(x)
                                    x.timestamp = int(time.time())
                                    appdynamics_class_list.append(x)
                        elif 'vs_uuids' in s['config']: #---- 17.2.4 api changed
                            for e in s['config']['vs_uuids']:
                                vs_name = self.vs_dict[e.rsplit('api/virtualservice/')[1]].replace('.','_')
                                class appdynamics_class(): pass
                                x = appdynamics_class
                                x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.virtualservice.%s.serviceengine.%s' %(vs_name, se_name.replace('.','_'))
                                x.value = 1
                                if x not in discovered:
                                    discovered.append(x)
                                    x.timestamp = int(time.time())
                                    appdynamics_class_list.append(x)
            if len(appdynamics_class_list) > 0:
                send_class_list_appdynamics(appdynamics_class_list)
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': func virtual_service_hosted_se completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func virtual_service_hosted_se encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)





    #-----------------------------------
    def license_usage(self):
        try:
            temp_start_time = time.time()
            licensing = self.avi_request('licenseusage?limit=1&step=300','admin').json()
            lic_cores = licensing['licensed_cores']
            if lic_cores != None:
                cores_used = licensing['num_se_vcpus']
                percentage_used = (cores_used / float(lic_cores))*100
                name_space = 'avi.'+self.avi_controller.replace('.','_')+'.licensing.licensed_cores'
                send_value_appdynamics('avi.'+self.avi_controller.replace('.','_')+'.licensing.licensed_cores', lic_cores, int(time.time()))
                send_value_appdynamics('avi.'+self.avi_controller.replace('.','_')+'.licensing.cores_used', cores_used, int(time.time()))
                send_value_appdynamics('avi.'+self.avi_controller.replace('.','_')+'.licensing.percentage_used', percentage_used, int(time.time()))
                temp_total_time = str(time.time()-temp_start_time)
                if enable_debug == True:
                    logging.info(self.avi_controller+': func license_usage completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func license_usage encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)





    #-----------------------------------
    def service_engine_vs_capacity(self):
        try:
            temp_start_time = time.time()
            appdynamics_class_list = []
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
                            se_vs[se_name]={'max_vs': max_vs, 'total_vs':0}
                        if 'virtualservice_refs' in s['config']:
                            for v in s['config']['virtualservice_refs']:
                                if se_name+v.rsplit('api/virtualservice/')[1] not in discovered_vs:
                                    discovered_vs.append(s['config']['name']+v.rsplit('api/virtualservice/')[1])
                                    se_vs[se_name]['total_vs'] += 1
            for entry in se_vs:
                vs_percentage_used = (se_dict[entry]['total_vs']/se_dict[entry]['max_vs'])*100
                class appdynamics_class(): pass
                x = appdynamics_class
                x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.serviceengine.%s.vs_capacity_used' %entry.replace('.','_')
                x.value = vs_percentage_used
                x.timestamp = int(time.time())
                appdynamics_class_list.append(x)
            if len(appdynamics_class_list) > 0:
                send_class_list_appdynamics(appdynamics_class_list)
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': func service_engine_vs_capacity completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func service_engine_vs_capacity encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)







    #-----------------------------------
    def license_expiration(self):
        try:
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
                send_value_appdynamics('avi.'+self.avi_controller.replace('.','_')+'.licensing.expiration_days.'+license_id, days_to_expire, int(time.time()))
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': func license_expiration completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func license_expiration encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)



    #-----------------------------------
    #----- GET AVI SOFTWARE VERSION NUMBER AND ASSIGN VALUE OF 1
    def get_avi_version(self):
        try:
            temp_start_time = time.time()
            current_version = self.login.json()['version']['Version'].replace('.','_')
            send_value_appdynamics('avi.'+self.avi_controller.replace('.','_')+'.current_version.%s' %current_version, 1, int(time.time()))
            if enable_debug == True:
                temp_total_time = str(time.time()-temp_start_time)
                logging.info(self.avi_controller+': func get_avi_version completed, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': get_avi_version encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)




    #-----------------------------------
    #----- GET Pool Member specific statistics
    def pool_server_metrics(self):
        try:
            temp_start_time = time.time()
            appdynamics_class_list = []
            discovered_servers = [] #--- this is used b/c members in admin show up in other tenants
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
                                "metric_id": pool_server_metric_list
                            }
                            ]}
                    api_url = 'analytics/metrics/collection?pad_missing_data=false&dimension_limit=1000&include_name=true&include_refs=true'
                    resp = self.avi_post(api_url,t['name'],payload)
                    if len(resp.json()['series']['collItemRequest:AllServers']) != 0:
                        for p in resp.json()['series']['collItemRequest:AllServers']:
                            if p not in discovered_servers:
                                discovered_servers.append(p)
                                server_object = p.split(',')[2]
                                for d in resp.json()['series']['collItemRequest:AllServers'][p]:
                                    if 'data' in d:
                                        pool_name = d['header']['pool_ref'].rsplit('#',1)[1]
                                        vs_name = d['header']['entity_ref'].rsplit('#',1)[1]
                                        metric_name = d['header']['name'].replace('.','_')
                                        class appdynamics_class(): pass
                                        x = appdynamics_class
                                        x.name_space = 'avi.'+self.avi_controller.replace('.','_')+'.virtualservice.%s.pool.%s.%s.%s' %(vs_name.replace('.','_'), pool_name.replace('.','_'), server_object.replace('.','_'),metric_name)
                                        x.value = d['data'][0]['value']
                                        x.timestamp = int(time.time())
                                        appdynamics_class_list.append(x)
            except:
                logging.exception(self.avi_controller+': func pool_server_metrics encountered an error for tenant '+t['name'])
                exception_text = traceback.format_exc()
                logging.exception(+self.avi_controller+': '+exception_text)
            if len(appdynamics_class_list) > 0:
                send_class_list_appdynamics(appdynamics_class_list)
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': pool_server_metrics, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func pool_server_metrics encountered an error encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)



    #-----------------------------------
    #----- GET cluster member specific statistics
    def controller_cluster_metrics(self):
        try:
            temp_start_time = time.time()
            major,minor = self.login.json()['version']['Version'].rsplit('.',1)
            if float(major) >= 17.2 and float(minor) >= 5: #----- controller metrics api introduced in 17.2.5
                cluster= self.avi_request('cluster','admin').json()
                cluster_nodes = {}
                temp_list=[]
                appdynamics_class_list = []
                for c in cluster['nodes']:
                    cluster_nodes[c['vm_uuid']]=c['ip']['addr']
                    #cluster_nodes[c['vm_uuid']]=c['vm_hostname']
                    resp = self.avi_request('analytics/metrics/controller/%s/?metric_id=%s&limit=1&step=300&?aggregate_entity=False' %(c['vm_uuid'],self.controller_metric_list),'admin').json()
                    temp_list.append(resp)
                for n in temp_list:
                    node = cluster_nodes[n['entity_uuid']]
                    for m in n['series']:
                        metric_name = m['header']['name']
                        class appdynamics_class(): pass
                        x = appdynamics_class
                        x.value = m['data'][0]['value']
                        x.timestamp = int(time.time())
                        x.namespace = 'avi.'+self.host_location+'.'+self.host_environment+'.'+self.avi_cluster_ip+'.controller.%s.%s' %(node,metric_name)
                        appdynamics_class_list.append(x)
                if len(appdynamics_class_list) > 0:
                    send_class_list_appdynamics(appdynamics_class_list)
            else:
                pass
            temp_total_time = str(time.time()-temp_start_time)
            if enable_debug == True:
                logging.info(self.avi_controller+': controller_cluster_metrics, executed in '+temp_total_time+' seconds')
        except:
            logging.exception(self.avi_controller+': func controller_cluster_metrics encountered an error encountered an error')
            exception_text = traceback.format_exc()
            logging.exception(self.avi_controller+': '+exception_text)

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
            test_functions.append(self.pool_server_metrics)
            test_functions.append(self.controller_cluster_metrics)
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
            logging.info(self.avi_controller+': controller specific tests have completed, executed in '+total_time+' seconds')
            send_value_appdynamics('avi.'+self.avi_controller.replace('.','_')+'.metricscript.executiontime', float(total_time)*1000, int(time.time()))
        except:
            exception_text = traceback.format_exc()
            logging.exception('Unable to login to: '+self.avi_controller)
            logging.exception(self.avi_controller+': '+exception_text)



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
    #---- setup logging
    if logging_enabled == True:
        #----- Disable requests and urlib3 logging
        logging.getLogger("requests").setLevel(logging.WARNING)
        try:
            urllib3_log = logging.getLogger("urllib3")
            urllib3_log.setLevel(logging.CRITICAL)
        except:
            _1=1
        if enable_debug != False:
            logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%b %d %H:%M:%S',filename=log_file,level=logging.DEBUG)
        else:
            logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%b %d %H:%M:%S',filename=log_file,level=logging.ERROR)
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
    logging.info('AVI_SCRIPT: metric script has completed, executed in '+total_time+' seconds')





#----- START SCRIPT EXECUTION
fdir = os.path.abspath(os.path.dirname(__file__))
#----- Import avi controller info from json file
with open(os.path.join(fdir,'avi_controllers.json')) as amc:
    avi_controller_list = json.load(amc)['controllers']
main()
