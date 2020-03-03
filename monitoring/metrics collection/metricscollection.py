#!/opt/local/bin/python3


version = 'v2019-12-20'



#########################################################################################
#                                                                                       #
#                                                                                       #
#                                                                                       #
#  REQUIREMENTS:                                                                        #
#    1. python 3.6+                                                                     #
#    2. python3 requests                                                                #
#    2. python3 yaml                                                                    #
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
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import json
import yaml
import time
import syslog
import socket
from multiprocessing import Process
from datetime import datetime
import base64
import logging
import traceback
import sys
import os
import _pickle as pickle
import socket
from requests.auth import HTTPBasicAuth




#---------------------------------------------------------------
#--------------- Metrics Endpoint functions Begin --------------
#---------------------------------------------------------------




#----- Send value to appdynamics
def send_value_appdynamics_machine(endpoint_info, appd_payload):
    try:
        for entry in appd_payload:
            if 'name_space' in entry:
                name_space = entry['name_space'].replace('||','|')
                #----- used for migration from old script
                if 'host_location' and 'host_environment' in entry:
                    name_space = name_space.replace('avi.', 'avi.'+entry['host_location']+'.'+entry['host_environment']+'.')            
                print('name=Custom Metrics|%s,value=%d,aggregator=OBSERVATION,time-rollup=CURRENT,cluster-rollup=INDIVIDUAL' % (name_space, int(entry['metric_value'])))
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+'   '+exception_text)




#----- this is to send to appdynamics machine agent http listener
def send_value_appdynamics_http(endpoint_info, appd_payload):
    try:
        payload = []
        for entry in appd_payload:
            if 'name_space' in entry:
                name_space = entry['name_space'].replace('||','|')
                #----- used for migration from old script
                if 'host_location' and 'host_environment' in entry:
                    name_space = name_space.replace('avi.', 'avi.'+entry['host_location']+'.'+entry['host_environment']+'.')            
                temp_payload = {}
                temp_payload['metricName'] = 'Custom Metrics|'+name_space
                temp_payload['aggregatorType'] = 'OBSERVATION'
                temp_payload['value'] = int(entry['metric_value'])
                payload.append(temp_payload)
        if len(payload) > 0:
            headers = ({'content-type': 'application/json'})
            resp = requests.post('http://%s:%s/api/v1/metrics' %(endpoint_info['server'],endpoint_info['server_port']),headers = headers, data=json.dumps(payload), timeout=15)
            if resp.status_code != 204:
                print(resp)
        #if resp.status_code != 202:
        #    print resp
    except:
        exception_text = traceback.format_exc()
        print(exception_text)




#----- Send value to datadog
def send_value_datadog(endpoint_info, datadog_payload):
    try:
        keys_to_remove=["avicontroller","timestamp","metric_value","metric_name","name_space"]
        series_list = []
        datadog_payload_template = {
             "metric":"",
             "points":"",
             "host":"",
             "tags":""
             }
        for entry in datadog_payload:
            temp_payload = datadog_payload_template.copy()
            temp_payload['metric'] = entry['metric_name']
            temp_payload['points'] = [[entry['timestamp'],entry['metric_value']]]
            temp_payload['host'] = entry['avicontroller']
            #for k in keys_to_remove:
            #    entry.pop(k, None)
            tag_list = []
            for e in entry:
                if e not in keys_to_remove:
                    tag_list.append(str(e+':'+entry[e]))
            temp_payload['tags'] = tag_list
            series_list.append(temp_payload)
        payload = {'series': series_list}
        headers = ({'content-type': 'application/json'})
        resp = requests.post('https://%s%s' %(endpoint_info['api_url'],endpoint_info['api_key']), verify=False, headers = headers, data=json.dumps(payload), timeout=15)
        if resp.status_code != 202:
            print(resp)
    except:
        exception_text = traceback.format_exc()
        print(exception_text)




#----- Send value to elasticsearch
def send_value_elasticsearch(endpoint_info, payload):
    try:
        keys_to_remove = ['name_space']
        for entry in payload:
            for k in keys_to_remove:
                entry.pop(k,None)
            entry[endpoint_info['timestamp']] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
            entry['metric_value'] = float(entry['metric_value'])
            headers = ({'content-type': 'application/json'})
            if str(endpoint_info['auth-enabled']).lower() == 'true':
                resp = requests.post('%s://%s:%s/%s/_doc' %(endpoint_info['protocol'],endpoint_info['server'], endpoint_info['server_port'], endpoint_info['index']) ,headers = headers, data=json.dumps(entry), timeout=15, auth=(endpoint_info['username'],endpoint_info['password']))
            else:
                resp = requests.post('%s://%s:%s/%s/_doc' %(endpoint_info['protocol'],endpoint_info['server'], endpoint_info['server_port'], endpoint_info['index']) ,headers = headers, data=json.dumps(entry), timeout=15)
            if resp.status_code != 201:
                print(resp.text)
    except:
        exception_text = traceback.format_exc()
        print(exception_text)




#----- Send value to graphite
def send_value_graphite(endpoint_info, graphite_payload):
    try:
        message_list = []
        name_space_prefix = 'network-script||'
        for entry in graphite_payload:
            if 'name_space' in entry:
                name_space = (name_space_prefix+entry['name_space']).replace('.','_').replace('||','.').replace(' ','_')
                #----- used for migration from old script
                if 'host_location' and 'host_environment' in entry:
                    name_space = name_space.replace('avi.', 'avi.'+entry['host_location']+'.'+entry['host_environment']+'.')            
                message_list.append('%s %f %d' %(name_space, entry['metric_value'], entry['timestamp']))
                #----- I believe there is a message list limit on graphite for plain text
                if sys.getsizeof(message_list) > 4915:
                    message = '\n'.join(message_list) + '\n'
                    socket.setdefaulttimeout(10)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((endpoint_info['server'], endpoint_info['server_port']))
                    sock.send(message.encode())
                    sock.close()
                    message_list = []
        if len(message_list) > 0:
            message = '\n'.join(message_list) + '\n'
            socket.setdefaulttimeout(10)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((endpoint_info['server'], endpoint_info['server_port']))
            sock.send(message.encode())
            sock.close()

    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+'   '+exception_text)
        print(message)




#----- Send value to influxdb
def send_value_influxdb(endpoint_info, influx_payload):
    try:
        tag_to_ignore = ['metric_name', 'timestamp', 'metric_value','name_space']
        if endpoint_info.get('metric_prefix') == None:
            metric_prefix = ''
        else:
            metric_prefix = endpoint_info['metric_prefix']
        message_list = []
        auth_enabled = False
        if 'auth-enabled' in endpoint_info:
            if str(endpoint_info['auth-enabled']).lower() == 'true':
                auth_enabled = True
        for entry in influx_payload:
            tag_list=[]
            for k in entry:
                if k not in tag_to_ignore:
                    tag_list.append((k+'='+entry[k]).replace(' ', '\\'))
            tag_list = ','.join(tag_list)
            temp_payload='%s%s,%s value=%f' %(metric_prefix, entry['metric_name'],tag_list,entry['metric_value'])
            message_list.append(temp_payload)
            if sys.getsizeof(message_list) > 4915:
                message = '\n'.join(message_list) + '\n'
                headers = ({'content-type': 'octet-stream'})
                if auth_enabled == True:
                    resp = requests.post('%s://%s:%s/write?db=%s' %(endpoint_info['protocol'],endpoint_info['server'],endpoint_info['server_port'],endpoint_info['db']),verify=False,headers = headers, data=message, timeout=15, auth=(endpoint_info['username'],endpoint_info['password']))
                    message_list = []
                else:
                    resp = requests.post('%s://%s:%s/write?db=%s' %(endpoint_info['protocol'],endpoint_info['server'],endpoint_info['server_port'],endpoint_info['db']),verify=False,headers = headers, data=message, timeout=15)
                    message_list = []
                if resp.status_code == 401:
                    print(str(datetime.now())+' '+endpoint_info['server']+': UNAUTHORIZED')
                elif resp.status_code == 403:
                    print(str(datetime.now())+' '+endpoint_info['server']+': FORBIDDEN')
        message = '\n'.join(message_list) + '\n'
        headers = ({'content-type': 'octet-stream'})
        if str(endpoint_info['auth-enabled']).lower() == 'true':
            resp = requests.post('%s://%s:%s/write?db=%s' %(endpoint_info['protocol'],endpoint_info['server'],endpoint_info['server_port'],endpoint_info['db']),verify=False,headers = headers, data=message, timeout=15, auth=(endpoint_info['username'],endpoint_info['password']))
        else:
            resp = requests.post('%s://%s:%s/write?db=%s' %(endpoint_info['protocol'],endpoint_info['server'],endpoint_info['server_port'],endpoint_info['db']),verify=False,headers = headers, data=message, timeout=15)
        if resp.status_code == 401:
            print(str(datetime.now())+' '+endpoint_info['server']+': UNAUTHORIZED')
        elif resp.status_code == 403:
            print(str(datetime.now())+' '+endpoint_info['server']+': FORBIDDEN')
    except:
        exception_text = traceback.format_exc()
        print(exception_text)
            



#----- Send value to logstash
def send_value_logstash(endpoint_info, payload):
    try:
        keys_to_remove = ['name_space','timestamp']
        proto = 'udp'
        if endpoint_info.get('protocol') != None:
            if endpoint_info['protocol'].lower() == 'tcp':
                proto = 'tcp'
        if proto == 'udp':
            for entry in payload:
                udpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                for k in keys_to_remove:
                    entry.pop(k,None)
                message = '\n'+(json.dumps(entry))+'\n'
                udpsock.sendto(message.encode(),(endpoint_info['server'],endpoint_info['server_port']))
                udpsock.close()
        else:
            message_list = []
            tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpsock.connect((endpoint_info['server'], endpoint_info['server_port']))
            socket.setdefaulttimeout(10)
            for entry in payload:
                for k in keys_to_remove:
                    entry.pop(k,None)
                message_list.append(json.dumps(entry))
                if sys.getsizeof(message_list) > 1450:
                    message = '\n'.join(message_list) + '\n'
                    tcpsock.send(message.encode())
                    message_list = []
            message = '\n'.join(message_list) + '\n'
            tcpsock.send(message.encode())
            tcpsock.close()

    except:
        exception_text = traceback.format_exc()
        print(exception_text)


#----- Send value to splunk HEC - destination is a metric index
def send_value_splunk_hec_metric(endpoint_info, splunk_payload):
    try:
        splunk_payload_template = {
            "source": "avi",
            "event" : "metric",
            "index": endpoint_info['index'],
            "time": "",
            "host": "",
            "fields": {
                "service": "avi",
                "environment": "",
                "_value": "",
                "location": "",
                "metric_name": ""
            }
        }
        hec_token = endpoint_info['hec_token']
        headers = ({'Authorization': 'Splunk '+hec_token})
        for entry in splunk_payload:
            temp_entry = entry
            keys_to_remove=["location","environment","avicontroller","timestamp","metric_value","metric_name","name_space"]
            payload = splunk_payload_template.copy()
            payload['host'] = temp_entry['avicontroller']
            payload['time'] = temp_entry['timestamp']
            payload['fields']['environment'] = temp_entry['environment']
            payload['fields']['location'] = temp_entry['location']
            payload['fields']['_value'] = temp_entry['metric_value']
            payload['fields']['metric_name'] = temp_entry['metric_name']
            for k in keys_to_remove:
                entry.pop(k, None)
            for e in entry:
                payload["fields"][e]=entry[e]
            resp = requests.post('%s://%s:%s/services/collector/event' %(endpoint_info['hec_protocol'], endpoint_info['server'], str(endpoint_info['hec_port'])) , verify=False, headers = headers, data=json.dumps(payload), timeout=15)
            if resp.status_code == 400:
                print(payload)
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+'   '+exception_text)
        print(entry)




#----- Send value to splunk HEC
def send_value_splunk_hec(endpoint_info, splunk_payload):
    try:
        splunk_payload_template = {
            #"source": "",
            "time": "",
            "host": "",
            "index": endpoint_info['index'],
            "sourcetype": "avi:metrics",
            "event": {
                "avi_controller": ""
            }
        }
        hec_token = endpoint_info['hec_token']
        headers = ({'Authorization': 'Splunk '+hec_token})
        for entry in splunk_payload:
            temp_entry = entry
            keys_to_remove=["avicontroller","name_space"]
            payload = splunk_payload_template.copy()
            payload['host'] = temp_entry['avicontroller']
            #payload['source'] = temp_entry['avicontroller']
            payload['time'] = temp_entry['timestamp']
            payload['sourcetype'] = 'avi:metrics'
            payload['event']['avi_controller'] = temp_entry['avicontroller']
            for k in keys_to_remove:
                entry.pop(k, None)
            for e in entry:
                payload["event"][e]=entry[e]
            resp = requests.post('%s://%s:%s/services/collector/event' %(endpoint_info['hec_protocol'], endpoint_info['server'], str(endpoint_info['hec_port'])) , verify=False, headers = headers, data=json.dumps(payload), timeout=15)
            if resp.status_code == 400:
                print(resp.text)
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+'   '+exception_text)
        print(entry)





def send_value_wavefront(endpoint_info, payload):
    try:
        keys_to_remove = ['name_space','timestamp','metric_name','metric_value']
        message_list = []
        if endpoint_info.get('api_key') != None:
            wf_key = endpoint_info['api_key']
            wf_proxy = False
        else:
            wf_proxy = True
            if 'proxy_port' in endpoint_info:
                wf_proxy_port = endpoint_info['proxy_port']
            else:
                wf_proxy_port = 2878
        wf_instance = endpoint_info['instance']
        for m in payload:
            tag_list = []
            metric_name = m['metric_name']
            metric_value = m['metric_value']
            for r in keys_to_remove:
                m.pop(r, None)
            for k,v in m.items():
                tag_list.append(k+'="'+v+'"')
            tag_list = (' '.join(tag_list))
            metric = '%s %f source=%s %s' %(metric_name, metric_value, m['avicontroller'], tag_list)
            message_list.append(metric)
        message = '\n'.join(message_list)
        if wf_proxy == False:    
            headers = ({'Authorization': 'Bearer '+wf_key, 'content-type': 'application/x-www-form-urlencoded'})
            resp = requests.post('https://'+wf_instance+'/report', verify=False, headers = headers, data=message, timeout=15)
            if resp.status_code != 202:
                print('======> ERROR: send_to_wavefront', resp.status_code, resp.text)
            #else:
            #    print(str(datetime.now())+' ======> Metrics sent to wavefront')
        else:
            try:
                socket.setdefaulttimeout(10)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((wf_instance, wf_proxy_port))       
                sock.send(message.encode())
                sock.close()
                #print(str(datetime.now())+' ======> Metrics sent to wavefront')
            except:
                print(str(datetime.now())+'  =====> ERROR: func send_to_wavefront encountered an error')
                exception_text = traceback.format_exc()
                print(str(datetime.now())+' : '+exception_text)
    except:
        exception_text = traceback.format_exc()
        print(exception_text)                





#---------------------------------          


def send_metriclist_to_endpoint(endpoint_list, payload):
    try:
        if endpoint_list != None:
            for endpoint_info in endpoint_list:
                if endpoint_info['type'] == 'graphite':
                    send_value_graphite(endpoint_info, payload)
                elif endpoint_info['type'] == 'splunk':
                    if endpoint_info['index_type'].lower() == 'metric':
                        send_value_splunk_hec_metric(endpoint_info, payload)
                    else:
                        send_value_splunk_hec(endpoint_info, payload)
                elif endpoint_info['type'] == 'appdynamics_http':
                    send_value_appdynamics_http(endpoint_info, payload)
                elif endpoint_info['type'] == 'appdynamics_machine':
                    send_value_appdynamics_machine(endpoint_info, payload)
                elif endpoint_info['type'] == 'datadog':
                    send_value_datadog(endpoint_info, payload)
                elif endpoint_info['type'] == 'influxdb':
                    send_value_influxdb(endpoint_info, payload)
                elif endpoint_info['type'] == 'logstash':
                    send_value_logstash(endpoint_info, payload)
                elif endpoint_info['type'] == 'elasticsearch':
                    send_value_elasticsearch(endpoint_info, payload)
                elif endpoint_info['type'] == 'wavefront':
                    send_value_wavefront(endpoint_info, payload)                    
    except:
        exception_text = traceback.format_exc()
        print(exception_text)





#----- Determine Metrics Endpoint Type Info
def determine_endpoint_type(configuration):
    endpoint_types = [
        'graphite',
        'appdynamics_http',
        'appdynamics_machine',
        'splunk',
        'datadog',
        'influxdb',
        'logstash',
        'elasticsearch',
        'wavefront'
        ]
    endpoint_list = []
    for a in configuration:
        if a['type'].lower() in endpoint_types and a['enable'] == True:
                endpoint_info = a
                endpoint_info['type'] = a['type'].lower()
                endpoint_list.append(endpoint_info)   
    if len(endpoint_list) == 0:
        print('=====> No end point will be used')
    print(endpoint_list)
    return endpoint_list



#---------------------------------------------------------------
#---------------- Metrics Endpoint functions END ---------------
#---------------------------------------------------------------



#----- This function allows for passwords to be either plaintext or base64 encoded
def isBase64(password):
    try:
        if base64.b64encode(base64.b64decode(password)).decode('utf-8') == password:
            if all(ord(c) < 128 for c in base64.b64decode(password).decode('utf-8')):
                return base64.b64decode(password).decode('utf-8')
            else:
                return password
        else:
            return password
    except Exception:
        return password




#----- This class is where all the test methods/functions exist and are executed
class avi_metrics():
    def __init__(self,avi_controller,avi_cluster_name, avi_user, avi_pass, controller_config):
        self.avi_cluster_ip = avi_controller
        self.avi_cluster_name = avi_cluster_name
        self.avi_user = avi_user
        self.avi_pass = avi_pass
        self.controller_config = controller_config
        #------ Default Metric Payload Template
        self.payload_template = {}
        #self.payload_template['location'] = self.host_location
        #self.payload_template['environment'] = self.host_environment
        self.payload_template['avicontroller'] = self.avi_cluster_name
        if controller_config.get('tags') != None:
            for k,v in controller_config['tags'].items():
                self.payload_template[k] = v
        if controller_config.get('metrics_endpoint_config') == None:
            if global_endpoint_config != None:
                self.endpoint_list = determine_endpoint_type(global_endpoint_config)
            else:   
                self.endpoint_list = determine_endpoint_type([])
        else:
            self.endpoint_list = determine_endpoint_type(controller_config['metrics_endpoint_config'])
        #------        
        if 'virtualservice_stats_config' in controller_config and controller_config.get('virtualservice_stats_config').get('virtualservice_realtime') == True:
            self.vs_realtime = True
        else:
            self.vs_realtime = False
        if 'serviceengine_stats_config' in controller_config and controller_config.get('serviceengine_stats_config').get('serviceengine_realtime') == True:
            self.se_realtime = True
        else:
            self.se_realtime = False
        if 'pool_stats_config' in controller_config and controller_config.get('pool_stats_config').get('pool_realtime') == True:
            self.pool_realtime = True
        else:
            self.pool_realtime = False
        #------
        if 'virtualservice_stats_config' in controller_config and controller_config.get('virtualservice_stats_config').get('virtualservice_runtime') == True:
            self.vs_runtime = True
        else:
            self.vs_runtime = False
        if 'serviceengine_stats_config' in controller_config and controller_config.get('serviceengine_stats_config').get('serviceengine_runtime') == True:
            self.se_runtime = True
        else:
            self.se_runtime = False
        if 'pool_stats_config' in controller_config and controller_config.get('pool_stats_config').get('pool_runtime') == True:
            self.pool_runtime = True
        else:
            self.pool_runtime = False
        if 'controller_stats_config' in controller_config and controller_config.get('controller_stats_config').get('controller_runtime') == True:
            self.controller_runtime = True
        else:
            self.controller_runtime = False
        #------ PRINT CONFIGURATION ------
        print('-------------------------------------------------------------------')
        print('============ CONFIGURATION FOR: '+avi_cluster_name+':'+self.avi_cluster_ip+ ' ============')
        if 'virtualservice_stats_config' in controller_config and controller_config.get('virtualservice_stats_config').get('virtualservice_metrics') == True:
            self.vs_metrics = True
            print('VIRTUALSERVICE METRICS:  True')
        else:
            self.vs_metrics = False
            print('VIRTUALSERVICE METRICS:  False')
        print('VIRTUALSERVICE REALTIME METRICS:  ' +str(self.vs_realtime))
        print('VIRTUALSERVICE RUNTIME:  '+str(self.vs_runtime))
        #------
        if 'serviceengine_stats_config' in controller_config and controller_config.get('serviceengine_stats_config').get('serviceengine_metrics') == True:
            self.se_metrics = True
            print('SERVICEENGINE METRICS:  True')
        else:
            self.se_metrics = False
            print('SERVICEENGINE METRICS:  False')
        print('SERVICEENGINE REALTIME METRICS:  ' +str(self.se_realtime))            
        print('SERVICEENGINE RUNTIME:  '+str(self.se_runtime))        
        #------
        if 'pool_stats_config' in controller_config and controller_config.get('pool_stats_config').get('pool_metrics') == True:
            self.pool_metrics = True
            print('POOL METRICS:  True')
        else:
            self.pool_metrics = False
            print('POOL METRICS:  False')
        print('POOL REALTIME METRICS:  ' +str(self.pool_realtime))
        print('POOL RUNTIME:  '+str(self.pool_runtime))
        #------
        if 'controller_stats_config' in controller_config and controller_config.get('controller_stats_config').get('controller_metrics') == True:
            self.controller_metrics = True
            print('CONTROLLER METRICS:  True')
        else:
            self.controller_metrics = False
            print('CONTROLLER METRICS:  False')
        print('CONTROLLER RUNTIME:  '+str(self.controller_runtime))        
        print('-------------------------------------------------------------------')
        print('-------------------------------------------------------------------')



        #------
        self.vs_metric_list  = [
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
            'l7_client.avg_resp_2xx',
            'l7_client.avg_resp_4xx',
            'l7_client.avg_resp_5xx',
            'l4_client.avg_total_rtt',
            'l7_client.avg_page_load_time',
            'l7_client.apdexr',
            'l7_client.avg_ssl_handshakes_new',
            'l7_client.avg_ssl_connections',
            'l7_client.sum_get_reqs',
            'l7_client.sum_post_reqs',
            'l7_client.sum_other_reqs',
            'l7_client.avg_frustrated_responses',
            'l7_client.avg_waf_attacks',
            'l7_client.pct_waf_attacks',
            'l7_client.sum_total_responses',
            'l7_client.avg_waf_rejected',
            'l7_client.avg_waf_evaluated',
            'l7_client.avg_waf_matched',
            'l7_client.avg_waf_disabled',
            'l7_client.pct_waf_disabled',
            'l7_client.avg_http_headers_count',
            'l7_client.avg_http_headers_bytes',
            'l7_client.pct_get_reqs',
            'l7_client.pct_post_reqs',
            'l7_client.avg_http_params_count',
            'l7_client.avg_uri_length',
            'l7_client.avg_post_bytes',
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
            'dns_server.avg_udp_queries',
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
            'l4_server.max_open_conns',
            'l4_server.avg_errored_connections',
            'l4_server.apdexc',
            'l4_server.avg_total_rtt',
            'l7_server.avg_resp_latency',
            'l7_server.apdexr',
            'l7_server.avg_application_response_time',
            'l7_server.pct_response_errors',
            'l7_server.avg_frustrated_responses',
            'l7_server.avg_total_requests',
            'healthscore.health_score_value'
            ]
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
            'se_stats.avg_packet_buffer_small_usage',
            'healthscore.health_score_value'
            ]
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
            'l4_server.max_open_conns',
            'l4_server.avg_errored_connections',
            'l4_server.apdexc',
            'l4_server.avg_total_rtt',
            'l7_server.avg_resp_latency',
            'l7_server.apdexr',
            'l7_server.avg_application_response_time',
            'l7_server.pct_response_errors',
            'l7_server.avg_frustrated_responses',
            'l7_server.avg_total_requests',
            'healthscore.health_score_value'
            ]


    def avi_login(self):
        try:
            login = pickle.load(open((os.path.join(fdir,self.avi_cluster_ip)),'rb'))
            cookies=dict()
            if 'avi-sessionid' in login.cookies.keys():
                cookies['avi-sessionid'] = login.cookies['avi-sessionid']
            else:
                cookies['sessionid'] = login.cookies['sessionid']
            headers = ({"X-Avi-Tenant": "admin", 'content-type': 'application/json'})
            resp = requests.get('https://%s/api/cluster' %self.avi_cluster_ip, verify=False, headers = headers,cookies=cookies,timeout=5)
            if resp.status_code == 200:
                return login
            else:
                login = requests.post('https://%s/login' %self.avi_cluster_ip, verify=False, data={'username': self.avi_user, 'password': self.avi_pass},timeout=15)
                pickle.dump(login, open((os.path.join(fdir,self.avi_cluster_ip)),'wb'))
                return login
        except:
            try:
                login = requests.post('https://%s/login' %self.avi_cluster_ip, verify=False, data={'username': self.avi_user, 'password': self.avi_pass},timeout=15)
                pickle.dump(login, open((os.path.join(fdir,self.avi_cluster_ip)),'wb'))
                return login
            except requests.exceptions.Timeout:
                class timedout:pass
                login = timedout()
                login.status_code = 'timedout'
                return login


    def avi_request(self,avi_api,tenant,api_version='17.2.1'):
        cookies=dict()
        if 'avi-sessionid' in self.login.cookies.keys():
            cookies['avi-sessionid'] = self.login.cookies['avi-sessionid']
        else:
            cookies['sessionid'] = self.login.cookies['sessionid']
        headers = ({'X-Avi-Tenant': '%s' %tenant, 'content-type': 'application/json', 'X-Avi-Version': '%s' %api_version})
        return requests.get('https://%s/api/%s' %(self.avi_controller,avi_api), verify=False, headers = headers,cookies=cookies,timeout=50)


    def avi_post(self,api_url,tenant,payload,api_version='17.2.1'):
        cookies=dict()
        if 'avi-sessionid' in self.login.cookies.keys():
            cookies['avi-sessionid'] = self.login.cookies['avi-sessionid']
        else:
            cookies['sessionid'] = self.login.cookies['sessionid']      
        headers = ({"X-Avi-Tenant": "%s" %tenant, 'content-type': 'application/json','referer': 'https://%s' %self.avi_controller, 'X-CSRFToken': dict(self.login.cookies)['csrftoken'],'X-Avi-Version':'%s' %api_version})
        cookies['csrftoken'] = self.login.cookies['csrftoken']
        return requests.post('https://%s/api/%s' %(self.avi_controller,api_url), verify=False, headers = headers,cookies=cookies, data=json.dumps(payload),timeout=50)



    #----- Tries to determine a follower controller to poll
    def controller_to_poll(self):
        cookies=dict()
        if 'avi-sessionid' in self.login.cookies.keys():
            cookies['avi-sessionid'] = self.login.cookies['avi-sessionid']
        else:
            cookies['sessionid'] = self.login.cookies['sessionid']        
        headers = ({"X-Avi-Tenant": "admin", 'content-type': 'application/json'})
        resp = (requests.get('https://%s/api/%s' %(self.avi_cluster_ip,'cluster/runtime'), verify=False, headers = headers,cookies=cookies,timeout=50)).json()
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
            #------
            vs_dict = {}
            se_dict = {}
            pool_dict = {}
            seg_dict = {}
            #------
            if self.vs_runtime == True:
                vs_runtime = '&join_subresources=runtime'
            else:
                vs_runtime = ''
            if self.se_runtime == True:
                se_runtime = '&join_subresources=runtime'
            else:
                se_runtime = '' 
            #------               
            for t in self.tenants:
                if self.vs_metrics == True or self.vs_runtime == True:
                    vs_inv = self.avi_request('virtualservice?fields=cloud_ref,tenant_ref,se_group_ref&page_size=200&include_name=true&'+vs_runtime,t['name'])
                    if vs_inv.status_code == 403:
                        print(str(datetime.now())+' =====> ERROR: virtualservice_inventory: %s' %vs_inv.text)
                    else:
                        vs_inv = vs_inv.json()
                        resp = vs_inv
                        page_number = 1
                        while 'next' in resp:
                            page_number += 1
                            resp = self.avi_request('virtualservice?fields=cloud_ref,tenant_ref,se_group_ref&page_size=200&include_name=true&page='+str(page_number)+vs_runtime,t['name']).json()
                            for v in resp['results']:
                                vs_inv['results'].append(v)
                        if vs_inv['count'] > 0:
                            for v in vs_inv['results']:
                                vs_dict[v['uuid']] = {}
                                vs_dict[v['uuid']]['name'] = v['name']
                                vs_dict[v['uuid']]['tenant'] = v['tenant_ref'].rsplit('#')[1]
                                vs_dict[v['uuid']]['cloud'] = v['cloud_ref'].rsplit('#')[1]
                                vs_dict[v['uuid']]['se_group'] = v['se_group_ref'].rsplit('#')[1]
                                vs_dict[v['uuid']]['results'] = v
                #---------------
                if self.se_metrics == True or self.se_runtime == True:
                    se_inv = self.avi_request('serviceengine?fields=cloud_ref,tenant_ref,se_group_ref,vs_refs&page_size=200&include_name=true'+se_runtime,t['name'])
                    if se_inv.status_code == 403:
                        print(str(datetime.now())+' =====> ERROR: serviceengine_inventory: %s' %se_inv.text)
                    else:
                        se_inv = se_inv.json()
                        resp = se_inv
                        page_number = 1
                        while 'next' in resp:
                            page_number += 1
                            resp = self.avi_request('serviceengine?fields=cloud_ref,tenant_ref,se_group_ref,vs_refs&page_size=200&include_name=true&page='+str(page_number)+se_runtime,t['name']).json()
                            for s in resp['results']:
                                se_inv['results'].append(s)
                        if se_inv['count'] > 0:
                            for s in se_inv['results']:
                                se_dict[s['uuid']] = {}
                                se_dict[s['uuid']]['name'] = s['name']
                                se_dict[s['uuid']]['tenant'] = s['tenant_ref'].rsplit('#')[1]
                                se_dict[s['uuid']]['cloud'] = s['cloud_ref'].rsplit('#')[1]
                                se_dict[s['uuid']]['se_group'] = s['se_group_ref'].rsplit('#')[1]
                                se_dict[s['uuid']]['se_group_uuid'] = s['se_group_ref'].split('/serviceenginegroup/')[1].rsplit('#')[0]
                                se_dict[s['uuid']]['results'] = s
                                se_dict[s['uuid']]['virtualservices'] = []
                                if 'vs_refs' in s:
                                    for v in s['vs_refs']:
                                        se_dict[s['uuid']]['virtualservices'].append(v.rsplit('#',1)[1])
                                else:
                                    se_dict[s['uuid']]['virtualservices'] = []
                #---------------     
                if self.pool_metrics == True or self.pool_runtime == True:                       
                    pool_inv = self.avi_request('pool-inventory?include_name=true&page_size=200',t['name'])
                    if pool_inv.status_code == 403:
                        print(str(datetime.now())+' =====> ERROR: pool_inventory: %s' %pool_inv.text)
                    else:
                        pool_inv = pool_inv.json()
                        resp = pool_inv
                        page_number = 1
                        while 'next' in resp:
                            page_number += 1
                            resp = self.avi_request('pool-inventory?include_name=true&page_size=200&page='+str(page_number),t['name']).json()
                            for p in resp['results']:
                                pool_inv['results'].append(p)   
                        if pool_inv['count'] > 0:
                            for p in pool_inv['results']:
                                pool_dict[p['uuid']] = {}
                                pool_dict[p['uuid']]['name'] = p['config']['name']
                                pool_dict[p['uuid']]['tenant'] = p['config']['tenant_ref'].rsplit('#')[1]
                                pool_dict[p['uuid']]['cloud'] = p['config']['cloud_ref'].rsplit('#')[1]
                                pool_dict[p['uuid']]['results'] = p                                                 
                #---------------                            
                seg_inv = self.avi_request('serviceenginegroup?fields=max_vs_per_se,cloud_ref,tenant_ref&include_name&page_size=200',t['name'])                       
                if seg_inv.status_code == 403:
                    print(str(datetime.now())+' =====> ERROR: serviceengine_group_inventory: %s' %seg_inv.text)
                else:
                    seg_inv = seg_inv.json()
                    if seg_inv['count'] > 0:
                        for seg in seg_inv['results']:
                            seg_dict[seg['uuid']] = {}
                            seg_dict[seg['uuid']]['name'] = seg['name']
                            seg_dict[seg['uuid']]['cloud'] = seg['cloud_ref'].rsplit('#')[1]
                            seg_dict[seg['uuid']]['tenant'] = seg['tenant_ref'].rsplit('#')[1]
                            seg_dict[seg['uuid']]['max_vs_per_se'] = seg['max_vs_per_se']
                            seg_dict[seg['uuid']]['results'] = seg
            temp_total_time = str(time.time()-start_time)
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
            available_metrics = {}
            resp = self.avi_request('analytics/metric_id',self.tenants[0]['name']).json()
            vs_metrics = []
            se_metrics = []
            pool_server_metrics = []
            controller_metrics = []
            for m in resp['results']:
                available_metrics[m['name']]=m['entity_types']
            if 'virtualservice_stats_config' in self.controller_config and self.controller_config.get('virtualservice_stats_config').get('virtualservice_metrics_list') != None:
                for vm in self.controller_config['virtualservice_stats_config']['virtualservice_metrics_list']:
                    vm = vm.replace(' ','').lower()
                    if vm in available_metrics:
                        if 'virtualservice' in available_metrics[vm]:
                            vs_metrics.append(vm)   
            else:                 
                for vm in self.vs_metric_list:
                    if vm in available_metrics:
                        if 'virtualservice' in available_metrics[vm]:
                            vs_metrics.append(vm)
            #------
            if 'serviceengine_stats_config' in self.controller_config and self.controller_config.get('serviceengine_stats_config').get('serviceengine_metrics_list') != None:
                for sm in self.controller_config['serviceengine_stats_config']['serviceengine_metrics_list']:
                    sm = sm.replace(' ','').lower()
                    if sm in available_metrics:
                        if 'serviceengine' in available_metrics[sm]:
                            se_metrics.append(sm)
            else:                 
                for sm in self.se_metric_list:
                    if sm in available_metrics:
                        if 'serviceengine' in available_metrics[sm]:
                            se_metrics.append(sm)
            #------
            if 'controller_stats_config' in self.controller_config and self.controller_config.get('controller_stats_config').get('controller_metrics_list') != None:
                for cm in self.controller_config['controller_stats_config']['controller_metrics_list']:
                    cm = cm.replace(' ','').lower()         
                    if cm in available_metrics:
                        if 'cluster' in available_metrics[cm]:
                            controller_metrics.append(cm)
            else:
                for cm in self.controller_metric_list:                
                    if cm in available_metrics:
                        if 'cluster' in available_metrics[cm]:
                            controller_metrics.append(cm)
            #------
            if 'pool_stats_config' in self.controller_config and self.controller_config.get('pool_stats_config').get('pool_metrics_list') != None:
                for pm in self.controller_config['pool_stats_config']['pool_metrics_list']:
                    pm = pm.replace(' ','').lower()
                    if pm in available_metrics:
                        if 'pool' in available_metrics[pm]:
                            pool_server_metrics.append(pm)
            else:
                for pm in self.pool_server_metric_list:
                    if pm in available_metrics:
                        if 'pool' in available_metrics[pm]:
                            pool_server_metrics.append(pm)
            #------                                      
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
            endpoint_payload_list = []
            for s in self.se_dict:
                if len(self.se_dict[s]['virtualservices']) > 0:
                    temp_payload = self.payload_template.copy()
                    temp_payload['metric_type'] = 'serviceengine_vs_count'
                    temp_payload['timestamp']=int(time.time())
                    temp_payload['se_name'] = self.se_dict[s]['name']
                    temp_payload['tenant'] = self.se_dict[s]['tenant']
                    temp_payload['se_group'] = self.se_dict[s]['se_group']
                    temp_payload['metric_type'] = 'serviceengine_vs_count'
                    temp_payload['metric_name'] = 'vs_count'
                    temp_payload['metric_value'] = len(self.se_dict[s]['virtualservices'])
                    temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||serviceengine||%s||vs_count' %self.se_dict[s]['name']
                    endpoint_payload_list.append(temp_payload)
            send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func srvc_engn_vs_count completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func srvc_engn_vs_count encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)

    #-----------------------------------

    def srvc_engn_count(self):
        try:
            temp_start_time = time.time()
            se_count = 0
            for s in self.se_dict:
                if 'name' in self.se_dict[s]:
                    se_count += 1
            endpoint_payload_list = []
            temp_payload = self.payload_template.copy()
            temp_payload['timestamp']=int(time.time())
            temp_payload['metric_type'] = 'serviceengine_count'
            temp_payload['metric_name'] = 'count'
            temp_payload['metric_value'] = se_count
            temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||serviceengine||count'
            endpoint_payload_list.append(temp_payload)
            send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func srvc_engn_count completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func srvc_engn_count encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)


    #-----------------------------------

    def srvc_engn_stats_threaded(self):
        proc = []
        for t in self.tenants:
            p = Process(target = self.srvc_engn_stats, args = (t['name'],))
            p.start()
            proc.append(p)
            if len(proc) > 9:
                for _p in proc:
                    _p.join()
                proc = []
        for p in proc:
            p.join()



    def srvc_engn_stats(self,tenant):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
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
            se_stat = self.avi_post('analytics/metrics/collection?pad_missing_data=false', tenant, payload).json()
            if self.se_realtime == True:
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
                realtime_stats = self.avi_post('analytics/metrics/collection?pad_missing_data=false', tenant, payload).json()
            for s in se_stat['series']['collItemRequest:AllSEs']:
                if s in self.se_dict:
                    se_name = self.se_dict[s]['name']
                    _tenant = self.se_dict[s]['tenant']
                    if tenant == 'admin' or (tenant !='admin' and _tenant != 'admin'):
                        for entry in se_stat['series']['collItemRequest:AllSEs'][s]:
                            if 'data' in entry:
                                temp_payload = self.payload_template.copy()
                                temp_payload['timestamp']=int(time.time())
                                temp_payload['se_name'] = se_name
                                temp_payload['cloud'] = self.se_dict[s]['cloud']
                                temp_payload['tenant'] = self.se_dict[s]['tenant']
                                temp_payload['se_group'] = self.se_dict[s]['se_group']
                                temp_payload['metric_type'] = 'serviceengine_metrics'
                                temp_payload['metric_name'] = entry['header']['name']
                                temp_payload['metric_value'] = entry['data'][0]['value']
                                temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||serviceengine||%s||%s' %(se_name, entry['header']['name'])
                                if self.se_realtime == True:
                                    if 'series' in realtime_stats:
                                        if s in realtime_stats['series']['collItemRequest:AllSEs']:
                                            for n in realtime_stats['series']['collItemRequest:AllSEs'][s]:
                                                 if n['header']['name'] == entry['header']['name']:
                                                     if 'data' in n:
                                                         temp_payload['metric_value'] = n['data'][0]['value']
                                endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
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
            p = Process(target = self.virtual_service_stats, args = (t['name'],))
            p.start()
            proc.append(p)
            if len(proc) > 9:
                for _p in proc:
                    _p.join()
                proc = []            
        for p in proc:
            p.join()




    def virtual_service_stats(self,tenant):
        try:
            temp_start_time = time.time()
            #-----
            endpoint_payload_list = []
            payload =  {'metric_requests': [{'step' : 300, 'limit': 1, 'id': 'allvs', 'entity_uuid' : '*', 'metric_id': self.vs_metric_list}]}
            vs_stats = self.avi_post('analytics/metrics/collection?pad_missing_data=false', tenant, payload).json()
            #----- this pulls 5 sec avg stats for vs that have realtime stats enabled
            if self.vs_realtime == True:
                payload =  {'metric_requests': [{'step' : 5, 'limit': 1, 'id': 'allvs', 'entity_uuid' : '*', 'metric_id': self.vs_metric_list}]}
                realtime_stats = self.avi_post('analytics/metrics/collection?pad_missing_data=false', tenant, payload).json()
            #----- 
            for v in vs_stats['series']['allvs']:
                if v in self.vs_dict:
                    vs_uuid = v
                    vs_name = self.vs_dict[vs_uuid]['name']
                    _tenant = self.vs_dict[vs_uuid]['tenant']
                    if tenant == 'admin' or (tenant !='admin' and _tenant != 'admin'):
                        for m in vs_stats['series']['allvs'][v]:
                            metric_name = m['header']['name']
                            if 'data' in m:
                                temp_payload = self.payload_template.copy().copy()
                                temp_payload['timestamp']=int(time.time())
                                temp_payload['vs_name'] = vs_name
                                temp_payload['tenant'] = _tenant
                                temp_payload['cloud'] = self.vs_dict[vs_uuid]['cloud']
                                temp_payload['se_group'] = self.vs_dict[vs_uuid]['se_group']
                                temp_payload['metric_type'] = 'virtualservice_metrics'
                                temp_payload['metric_name'] = metric_name
                                temp_payload['metric_value'] = m['data'][0]['value']
                                temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||virtualservice||%s||%s' %(vs_name, metric_name)
                                if self.vs_realtime == True:
                                    if 'series' in realtime_stats:
                                        if v in realtime_stats['series']['allvs']:
                                            for n in realtime_stats['series']['allvs'][v]:
                                                 if n['header']['name'] == m['header']['name']:
                                                     if 'data' in n:
                                                         temp_payload['metric_value'] = n['data'][0]['value']
                                endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func virtual_service_stats completed for tenant: '+tenant+', executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func virtual_service_stats encountered an error for tenant '+tenant)
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)




    def vs_metrics_per_se_threaded(self):
        try:
            temp_start_time = time.time()
            major,minor = self.login.json()['version']['Version'].rsplit('.',1)
            if (float(major) >= 17.2 and float(minor) >= 8) or float(major) >= 18.1:
                proc = []
                for t in self.tenants:
                    p = Process(target = self.vs_metrics_per_se, args = (t['name'],))
                    p.start()
                    proc.append(p)
                    if len(proc) > 9:
                        for _p in proc:
                            _p.join()
                        proc = []  
                for p in proc:
                        p.join()
                temp_total_time = str(time.time()-temp_start_time)
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_metrics_per_se_threaded completed, executed in '+temp_total_time+' seconds')
        except:
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)





    def vs_metrics_per_se(self,tenant):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            payload =  {'metric_requests': [{'step' : 300, 'limit': 1, 'id': 'vs_metrics_by_se', 'entity_uuid' : '*', 'serviceengine_uuid': '*', 'include_refs': True, 'metric_id': self.vs_metric_list}]}
            vs_stats = self.avi_post('analytics/metrics/collection?include_name=true&pad_missing_data=false', tenant, payload).json()
            #----- this will pull 5 sec stats for vs that have realtime stat enabled
            if self.vs_realtime == True:
                payload =  {'metric_requests': [{'step' : 5, 'limit': 1, 'id': 'vs_metrics_by_se', 'entity_uuid' : '*', 'serviceengine_uuid': '*', 'include_refs': True, 'metric_id': self.vs_metric_list}]}
                realtime_stats = self.avi_post('analytics/metrics/collection?include_name=true&pad_missing_data=false', tenant, payload).json()
            #------
            if len(vs_stats['series']['vs_metrics_by_se']) > 0:
                for entry in vs_stats['series']['vs_metrics_by_se']:
                    if entry in self.vs_dict:
                        vs_name = self.vs_dict[entry]['name']
                        _tenant = self.vs_dict[entry]['tenant']
                        if tenant == 'admin' or (tenant !='admin' and _tenant != 'admin'):                        
                            for d in vs_stats['series']['vs_metrics_by_se'][entry]:
                                if 'data' in d:
                                    if 'serviceengine_ref' in d['header']:
                                        se_name = d['header']['serviceengine_ref'].rsplit('#',1)[1]
                                        temp_payload = self.payload_template.copy()
                                        temp_payload['timestamp']=int(time.time())
                                        temp_payload['se_name'] = se_name
                                        temp_payload['tenant'] = self.vs_dict[entry]['tenant']
                                        temp_payload['cloud'] = self.vs_dict[entry]['cloud']
                                        temp_payload['se_group'] = self.vs_dict[entry]['se_group']
                                        temp_payload['vs_name'] = vs_name
                                        temp_payload['metric_type'] = 'virtualservice_metrics_per_serviceengine'
                                        #temp_payload['metric_name'] = d['header']['name']
                                        temp_payload['metric_value'] = d['data'][0]['value']
                                        if self.vs_realtime == True:
                                            if 'series' in realtime_stats:
                                                if entry in realtime_stats['series']['vs_metrics_by_se']:
                                                    for n in realtime_stats['series']['vs_metrics_by_se'][entry]:
                                                         if n['header']['name'] == d['header']['name'] and n['header']['serviceengine_ref'] == d['header']['serviceengine_ref']:
                                                             if 'data' in n:
                                                                 temp_payload['metric_value'] = n['data'][0]['value']
                                        metric_name = d['header']['name']
                                        temp_payload['metric_name'] = metric_name+'_per_se'
                                        temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||serviceengine||%s||virtualservice_stats||%s||%s' %(se_name,vs_name,temp_payload['metric_name'])
                                        endpoint_payload_list.append(temp_payload)
                if len(endpoint_payload_list) > 0:
                    send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
                temp_total_time = str(time.time()-temp_start_time)
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_metrics_per_se completed tenant: '+tenant+', executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_metrics_per_se for tenant: '+tenant+', encountered an error')
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
            vs_count=0
            for v in self.vs_dict:
                vs_name = self.vs_dict[v]['name']
                vs_count += 1
                metric_name = 'oper_status'
                if self.vs_dict[v]['results']['runtime']['oper_status']['state'] == 'OPER_UP':
                    metric_value = 2
                    vs_up_count += 1
                elif self.vs_dict[v]['results']['runtime']['oper_status']['state'] == 'OPER_DISABLED':
                    metric_value = 1
                    vs_disabled_count += 1
                else:
                    metric_value = 0
                    vs_down_count += 1
                temp_payload = self.payload_template.copy()
                temp_payload['timestamp']=int(time.time())
                temp_payload['vs_name'] = vs_name
                temp_payload['tenant'] = self.vs_dict[v]['tenant']
                temp_payload['cloud'] = self.vs_dict[v]['cloud']
                temp_payload['se_group'] = self.vs_dict[v]['se_group']
                temp_payload['metric_type'] = 'virtualservice_operstatus'
                temp_payload['metric_name'] = 'oper_status'
                temp_payload['metric_value'] = metric_value
                temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||virtualservice||%s||%s' %(vs_name, metric_name)
                endpoint_payload_list.append(temp_payload)
            temp_payload = self.payload_template.copy()
            temp_payload['timestamp']=int(time.time())
            #----- Total VS
            a = temp_payload.copy()
            a['metric_name'] = 'count'
            a['metric_value'] = vs_count
            a['metric_type'] = 'virtualservice_count'
            a['name_space'] = 'avi||'+self.avi_cluster_name+'||virtualservice||count'
            endpoint_payload_list.append(a)
            #----- Total VS UP
            b = temp_payload.copy()
            b['metric_type'] = 'virtualservice_up'
            b['metric_name'] = 'status_up'
            b['metric_value'] = vs_up_count
            b['name_space'] = 'avi||'+self.avi_cluster_name+'||virtualservice||status_up'
            endpoint_payload_list.append(b)
            #----- Total VS Down
            c = temp_payload.copy()
            c['metric_type'] = 'virtualservice_down'
            c['metric_name'] = 'status_down'
            c['metric_value'] = vs_down_count
            c['name_space'] = 'avi||'+self.avi_cluster_name+'||virtualservice||status_down'
            endpoint_payload_list.append(c)
            #----- Total VS Disabled
            d = temp_payload.copy()
            d['metric_type'] = 'virtualservice_disabled'
            d['metric_name'] = 'status_disabled'
            d['metric_value'] = vs_disabled_count
            d['name_space'] = 'avi||'+self.avi_cluster_name+'||virtualservice||status_disabled'
            endpoint_payload_list.append(d)
            send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_oper_status completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func vs_oper_status encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)



    #-----------------------------------
    #----- RETRIEVE THE NUMBER OF ENABLED, ACTIVE, AND TOTAL POOL MEMBERS FOR EACH VIRTUAL SERVER
    def active_pool_members(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            for pool in self.pool_dict:
                p = self.pool_dict[pool]['results']
                try:
                    vs_list = []
                    if 'num_servers' in p['runtime']:
                        if 'virtualservice' in p:
                            vs_list.append(p['virtualservice']['name'])
                        elif 'virtualservices' in p:
                            for v in p['virtualservices']:
                                vs_list.append(v.rsplit('#',1)[1])
                        pool_name = p['config']['name']
                        pool_members_up = p['runtime']['num_servers_up']
                        pool_members_enabled = p['runtime']['num_servers_enabled']
                        pool_members = p['runtime']['num_servers']
                        for vs_entry in vs_list:
                            #----- pool members enabled
                            temp_payload = self.payload_template.copy()
                            temp_payload['timestamp']=int(time.time())
                            temp_payload['vs_name'] = vs_entry
                            temp_payload['tenant'] = self.pool_dict[p['config']['uuid']]['tenant']
                            temp_payload['cloud'] = self.pool_dict[p['config']['uuid']]['cloud']
                            temp_payload['pool_name'] = pool_name
                            temp_payload['metric_type'] = 'virtualservice_pool_members'
                            temp_payload['metric_name'] = 'virtualservice_pool_members_enabled'
                            temp_payload['metric_value'] = pool_members_enabled
                            temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||virtualservice||%s||pool||%s||%s' %(vs_entry, pool_name, 'pool_members_enabled')
                            endpoint_payload_list.append(temp_payload)
                            #----- pool members up
                            temp1_payload = self.payload_template.copy()
                            temp1_payload['timestamp']=int(time.time())
                            temp1_payload['vs_name'] = vs_entry
                            temp1_payload['tenant'] = self.pool_dict[p['config']['uuid']]['tenant']
                            temp1_payload['cloud'] = self.pool_dict[p['config']['uuid']]['cloud']
                            temp1_payload['pool_name'] = pool_name
                            temp1_payload['metric_type'] = 'virtualservice_pool_members'
                            temp1_payload['metric_name'] = 'virtualservice_pool_members_up'
                            temp1_payload['metric_value'] = pool_members_up
                            temp1_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||virtualservice||%s||pool||%s||%s' %(vs_entry, pool_name, 'pool_members_up')
                            endpoint_payload_list.append(temp1_payload)
                            #----- pool members configured
                            temp2_payload = self.payload_template.copy()
                            temp2_payload['timestamp']=int(time.time())
                            temp2_payload['vs_name'] = vs_entry
                            temp2_payload['tenant'] = self.pool_dict[p['config']['uuid']]['tenant']
                            temp2_payload['cloud'] = self.pool_dict[p['config']['uuid']]['cloud']                               
                            temp2_payload['pool_name'] = pool_name
                            temp2_payload['metric_type'] = 'virtualservice_pool_members'
                            temp2_payload['metric_name'] = 'virtualservice_pool_members'
                            temp2_payload['metric_value'] = pool_members
                            temp2_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||virtualservice||%s||pool||%s||%s' %(vs_entry, pool_name, 'pool_members')
                            endpoint_payload_list.append(temp2_payload)
                except:
                    exception_text = traceback.format_exc()
                    print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func active_pool_members completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func active_pool_members encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)







    #-----------------------------------
    #----- SE missed heartbeats
    def se_missed_hb(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            discovered_se = []
            for s in self.se_dict:
                if s not in discovered_se:
                    discovered_se.append(s)
                    if 'hb_status' in self.se_dict[s]['results']['runtime']:
                        temp_payload = self.payload_template.copy()
                        temp_payload['timestamp']=int(time.time())
                        temp_payload['se_name'] = self.se_dict[s]['name']
                        temp_payload['tenant'] = self.se_dict[s]['tenant']
                        temp_payload['cloud'] = self.se_dict[s]['cloud']
                        temp_payload['se_group'] = self.se_dict[s]['se_group']
                        temp_payload['metric_type'] = 'serviceengine_missed_heartbeats'
                        temp_payload['metric_name'] = 'missed_heartbeats'
                        temp_payload['metric_value'] = self.se_dict[s]['results']['runtime']['hb_status']['num_hb_misses']
                        temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||serviceengine||%s||%s' %(self.se_dict[s]['name'], 'missed_heartbeats')
                        endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
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
            for s in self.se_dict:
                if s not in discovered_se:
                    discovered_se.append(s)
                    if 'se_connected' in self.se_dict[s]['results']['runtime']:
                        temp_payload = self.payload_template.copy()
                        temp_payload['timestamp']=int(time.time())
                        temp_payload['se_name'] = self.se_dict[s]['name']
                        temp_payload['tenant'] = self.se_dict[s]['tenant']
                        temp_payload['cloud'] = self.se_dict[s]['cloud']
                        temp_payload['se_group'] = self.se_dict[s]['se_group']
                        temp_payload['metric_type'] = 'serviceengine_connected_state'
                        temp_payload['metric_name'] = 'connected'
                        if self.se_dict[s]['results']['runtime']['se_connected'] == True:
                            temp_payload['metric_value'] = 1
                        else:
                            temp_payload['metric_value'] = 0
                        temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||serviceengine||%s||%s' %(self.se_dict[s]['name'], 'connected_state')
                        endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
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
                temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||cluster||%s||role' %member_name
                endpoint_payload_list.append(temp_payload)
            #-----------------------------------
            #---- ADD ACTIVE MEMBER COUNT TO LIST
            temp_payload = self.payload_template.copy()
            temp_payload['timestamp']=int(time.time())
            temp_payload['metric_type'] = 'cluster'
            temp_payload['metric_name'] = 'active_members'
            temp_payload['metric_value'] = active_members
            temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||cluster||active_members'
            endpoint_payload_list.append(temp_payload)
            #----- Send metrics
            send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
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
                subnets = self.avi_request('network-inventory?page_size=200','admin').json()['results']
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
                                temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||networks||%s||used' %network_name
                                endpoint_payload_list.append(temp_payload)
                if len(endpoint_payload_list) > 0:
                    send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
                temp_total_time = str(time.time()-temp_start_time)
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func avi_subnet_usage completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func avi_subnet_usage encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)


    #-----------------------------------
    def virtual_service_hosted_se(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            discovered = []
            for v in self.vs_dict:
                if 'service_engine' in self.vs_dict[v]['results']['runtime']['vip_summary'][0]:
                    vs_name = self.vs_dict[v]['name']
                    for r in self.vs_dict[v]['results']['runtime']['vip_summary']:
                        for s in r['service_engine']:
                            se_name = s['url'].rsplit('#',1)[1]
                            temp_payload = self.payload_template.copy()
                            temp_payload['timestamp']=int(time.time())
                            temp_payload['se_name'] = se_name
                            temp_payload['vs_name'] = vs_name
                            temp_payload['tenant'] = self.vs_dict[v]['tenant']
                            temp_payload['cloud'] = self.vs_dict[v]['cloud']
                            temp_payload['se_group'] = self.vs_dict[v]['se_group']
                            temp_payload['metric_type'] = 'virtualservice_hosted_se'
                            temp_payload['metric_name'] = 'hosting_se'
                            temp_payload['metric_value'] = 1
                            temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||virtualservice||%s||serviceengine||%s' %(vs_name, se_name)
                            if temp_payload not in discovered:
                                discovered.append(temp_payload)
                                endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
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
            endpoint_payload_list = []
            for v in self.vs_dict:
                if v not in discovered_vs:
                    for a in self.vs_dict[v]['results']['runtime']['vip_summary']:
                        if 'service_engine' in a:
                            for s in a['service_engine']:
                                if s['primary'] == True:
                                    discovered_vs.append(v)
                                    se_name = s['url'].rsplit('#',1)[1]
                                    vs_name = self.vs_dict[v]['name']
                                    temp_payload = self.payload_template.copy()
                                    temp_payload['timestamp']=int(time.time())
                                    temp_payload['vs_name'] = vs_name
                                    temp_payload['tenant'] = self.vs_dict[v]['tenant']
                                    temp_payload['cloud'] = self.vs_dict[v]['cloud']
                                    temp_payload['se_group'] = self.vs_dict[v]['se_group']
                                    temp_payload['se_name'] = se_name
                                    temp_payload['metric_type'] = 'virtualservice_primary_se'
                                    temp_payload['metric_name'] = 'primary_se'
                                    temp_payload['metric_value'] = 1
                                    temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||virtualservice||%s||primary_se||%s' %(vs_name,se_name)
                                    endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
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
                temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||licensing||licensed_cores'
                endpoint_payload_list.append(temp_payload)
                #-----
                temp1_payload = self.payload_template.copy()
                temp1_payload['timestamp']=int(time.time())
                temp1_payload['metric_type'] = 'licensing'
                temp1_payload['metric_name'] = 'cores_used'
                temp1_payload['metric_value'] = cores_used
                temp1_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||licensing||cores_used'
                endpoint_payload_list.append(temp1_payload)
                #-----
                temp2_payload = self.payload_template.copy()
                temp2_payload['timestamp']=int(time.time())
                temp2_payload['metric_type'] = 'licensing'
                temp2_payload['metric_name'] = 'percentage_used'
                temp2_payload['metric_value'] = percentage_used
                temp2_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||licensing||percentage_used'
                endpoint_payload_list.append(temp2_payload)
                temp_total_time = str(time.time()-temp_start_time)
                send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
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
            discovered_vs = []
            se_vs = {}
            for s in self.se_dict:
                se_name = self.se_dict[s]['name']
                if se_name not in se_vs:
                    seg = self.se_dict[s]['results']['se_group_ref'].rsplit('#',1)[0].split('/api/serviceenginegroup/')[1]
                    max_vs = self.seg_dict[seg]['max_vs_per_se']
                    se_vs[se_name]={'max_vs': max_vs, 'total_vs': 0,'tenant': self.se_dict[s]['tenant']}
                    se_vs[se_name]['se_group'] = self.se_dict[s]['se_group']
                    se_vs[se_name]['cloud'] = self.se_dict[s]['cloud'] 
                    if 'vs_refs' in self.se_dict[s]['results']:
                        for v in self.se_dict[s]['results']['vs_refs']:
                            if se_name+v.rsplit('api/virtualservice/')[1].rsplit('#',1)[0] not in discovered_vs:
                                discovered_vs.append(se_name+v.rsplit('api/virtualservice/')[1].rsplit('#',1)[0])
                                se_vs[se_name]['total_vs'] += 1
            for entry in se_vs:
                vs_percentage_used = (se_vs[entry]['total_vs']/se_vs[entry]['max_vs'])*100
                temp_payload = self.payload_template.copy()
                temp_payload['timestamp']=int(time.time())
                temp_payload['se_name'] = entry
                temp_payload['se_group'] = se_vs[entry]['se_group']
                temp_payload['tenant'] = se_vs[entry]['tenant']
                temp_payload['cloud'] = se_vs[entry]['cloud']
                temp_payload['metric_type'] = 'serviceengine_capacity'
                temp_payload['metric_name'] = 'vs_capacity_used'
                temp_payload['metric_value'] = vs_percentage_used
                temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||serviceengine||%s||vs_capacity_used' %entry
                endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
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
                    temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||licensing||expiration_days||'+license_id
                    endpoint_payload_list.append(temp_payload)
                    send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
                temp_total_time = str(time.time()-temp_start_time)
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func license_expiration completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func license_expiration encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)





    #-----------------------------------
    #----- GET AVI SOFTWARE VERSION NUMBER AND ASSIGN VALUE OF 1
    def get_serviceengine_version(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            for s in self.se_dict:
                current_version = self.se_dict[s]['results']['runtime']['version'].split(' ',1)[0]
                temp_payload = self.payload_template.copy()
                temp_payload['timestamp']=int(time.time())
                temp_payload['metric_type'] = 'se_version'
                temp_payload['metric_name'] = 'current_version'
                temp_payload['version'] = current_version
                temp_payload['se_name'] = self.se_dict[s]['name']
                temp_payload['se_group'] = self.se_dict[s]['se_group']
                temp_payload['tenant'] = self.se_dict[s]['tenant']
                temp_payload['cloud'] = self.se_dict[s]['cloud']
                temp_payload['metric_value'] = 1
                temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||current_version||%s' %current_version
                endpoint_payload_list.append(temp_payload)
            send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func get_serviceengine_version completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': get_serviceengine_version encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)


    #-----------------------------------
    #----- GET AVI SOFTWARE VERSION NUMBER AND ASSIGN VALUE OF 1
    def get_controller_version(self):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            #current_version = self.login.json()['version']['Version']+'('+str(self.login.json()['version']['build'])+')'
            cluster_status = self.avi_request('cluster/runtime','admin').json()
            current_version = cluster_status['node_info']['version'].split(' ',1)[0]
            temp_payload = self.payload_template.copy()
            temp_payload['timestamp']=int(time.time())
            temp_payload['metric_type'] = 'controller_version'
            temp_payload['metric_name'] = 'current_version'
            temp_payload['version'] = current_version
            temp_payload['metric_value'] = 1
            temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||current_version||%s' %current_version
            endpoint_payload_list.append(temp_payload)
            send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func get_avi_version completed, executed in '+temp_total_time+' seconds')
        except:
            print(str(datetime.now())+' '+self.avi_cluster_ip+': get_avi_version encountered an error')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)



    #-----------------------------------
    #----- GET Pool Member specific statistics
    def pool_server_stats_threaded(self):
        try:
            temp_start_time = time.time()
            proc = []
            for t in self.tenants:
                p = Process(target = self.pool_server_stats, args = (t['name'],))
                p.start()
                proc.append(p)
                if len(proc) > 9:
                    for _p in proc:
                        _p.join()
                    proc = []            
            for p in proc:
                p.join()
            temp_total_time = str(time.time()-temp_start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func pool_server_stats_threaded completed, executed in '+temp_total_time+' seconds')
        except:
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' '+self.avi_cluster_ip+': '+exception_text)





    #-----------------------------------
    #----- GET Pool Member specific statistics
    def pool_server_stats(self,tenant):
        try:
            temp_start_time = time.time()
            endpoint_payload_list = []
            discovered_servers = []
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
            resp = self.avi_post(api_url,tenant,payload).json()
            if self.pool_realtime == True:
                payload = {
                    "metric_requests": [
                        {
                            "step": 5,
                            "limit": 1,
                            "aggregate_entity": False,
                            "entity_uuid": "*",
                            "obj_id": "*",
                            "pool_uuid": "*",
                            "id": "collItemRequest:AllServers",
                            "metric_id": self.pool_server_metric_list
                        }
                        ]}
                realtime_stats = self.avi_post('analytics/metrics/collection?pad_missing_data=false&dimension_limit=1000&include_name=true&include_refs=true', tenant, payload).json()
            if 'series' in resp:
                if len(resp['series']['collItemRequest:AllServers']) != 0:
                    for p in resp['series']['collItemRequest:AllServers']:
                        if p not in discovered_servers:
                            discovered_servers.append(p)
                            server_object = p.split(',')[2]
                            for d in resp['series']['collItemRequest:AllServers'][p]:
                                if 'data' in d:
                                    pool_name = d['header']['pool_ref'].rsplit('#',1)[1]                                            
                                    metric_name = d['header']['name']
                                    temp_payload = self.payload_template.copy()
                                    temp_payload['timestamp']=int(time.time())
                                    temp_payload['pool_name'] = pool_name
                                    temp_payload['tenant'] = self.pool_dict[d['header']['pool_ref'].rsplit('#',1)[0].split('/api/pool/')[1]]['tenant']
                                    temp_payload['cloud'] = self.pool_dict[d['header']['pool_ref'].rsplit('#',1)[0].split('api/pool/')[1]]['cloud']
                                    temp_payload['pool_member'] = server_object
                                    temp_payload['metric_type'] = 'pool_member_metrics'
                                    temp_payload['metric_name'] = metric_name
                                    temp_payload['metric_value'] = d['data'][0]['value']
                                    if 'entity_ref' in d['header']:
                                        vs_name = d['header']['entity_ref'].rsplit('#',1)[1]
                                        temp_payload['vs_name'] = vs_name
                                        temp_payload['name_space'] = 'avi||%s||virtualservice||%s||pool||%s||%s||%s' %(self.avi_cluster_name,vs_name, pool_name, server_object,metric_name)
                                        #endpoint_payload_list.append(temp_payload)
                                    else:
                                        for v in self.pool_dict[d['header']['pool_ref'].rsplit('#',1)[0].split('api/pool/')[1]]['results']['virtualservices']:
                                            vs_name = v.rsplit('#',1)[1]
                                            #temp_payload1 = temp_payload.copy()
                                            temp_payload['vs_name'] = vs_name
                                            temp_payload['name_space'] = 'avi||%s||virtualservice||%s||pool||%s||%s||%s' %(self.avi_cluster_name,vs_name, pool_name, server_object,metric_name)
                                    if self.pool_realtime == True:
                                        if 'series' in realtime_stats:
                                            if p in realtime_stats['series']['collItemRequest:AllServers']:
                                                for n in realtime_stats['series']['collItemRequest:AllServers'][p]:
                                                    if n['header']['name'] == d['header']['name']:
                                                        if 'data' in n:
                                                            temp_payload['metric_value'] = n['data'][0]['value']
                                    endpoint_payload_list.append(temp_payload)
            if len(endpoint_payload_list) > 0:
                send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            temp_total_time = str(time.time()-temp_start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func pool_server_stats for tenant '+tenant+', executed in '+temp_total_time+' seconds')
        except:
                print(str(datetime.now())+' '+self.avi_cluster_ip+': func pool_server_stats  encountered an error for tenant '+tenant)
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
                        temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||controller||%s||%s' %(node,metric_name)
                        endpoint_payload_list.append(temp_payload)
                if len(endpoint_payload_list) > 0:
                    send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            else:
                pass
            temp_total_time = str(time.time()-temp_start_time)
            print(str(datetime.now())+' '+self.avi_cluster_ip+': func controller_cluster_metrics, executed in '+temp_total_time+' seconds')
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
            if self.login.status_code == 200:
                self.tenants = self.login.json()['tenants']
                #self.avi_controller = self.controller_to_poll()
                #-----------------------------------
                #----- Add Test functions to list for threaded execution
                #-----------------------------------
                test_functions = []
                if self.vs_metrics == True:
                    test_functions.append(self.virtual_service_stats_threaded)
                    test_functions.append(self.vs_metrics_per_se_threaded)                    
                if self.vs_runtime == True:
                    test_functions.append(self.vs_oper_status)
                    test_functions.append(self.vs_primary_se)
                    test_functions.append(self.virtual_service_hosted_se)
                #------
                if self.se_metrics == True:
                    test_functions.append(self.srvc_engn_stats_threaded)
                if self.se_runtime == True:
                    test_functions.append(self.srvc_engn_vs_count)
                    test_functions.append(self.srvc_engn_count)
                    test_functions.append(self.se_missed_hb)
                    test_functions.append(self.service_engine_vs_capacity)
                    test_functions.append(self.se_connected)
                    test_functions.append(self.get_serviceengine_version)
                #------
                if self.pool_metrics == True:
                    test_functions.append(self.pool_server_stats_threaded)  
                if self.pool_runtime == True:
                    test_functions.append(self.active_pool_members)
                #------
                if self.controller_metrics == True:
                    test_functions.append(self.controller_cluster_metrics)
                if self.controller_runtime == True:
                    test_functions.append(self.cluster_status)
                    test_functions.append(self.avi_subnet_usage)
                    test_functions.append(self.license_usage)
                    test_functions.append(self.license_expiration)
                    test_functions.append(self.get_controller_version)
                #-----------------------------------
                _flist = []
                for _t in test_functions:
                    _flist.append(str(_t).split('bound method ')[1].split(' ',1)[0])
                print('=====> Running the following metrics functions: ')
                for _f in _flist:
                     print('        ',_f)
                print('-------------------------------------------------------------------')
                #-----------------------------------
                self.avi_controller = self.avi_cluster_ip
                print('=====> Chose '+self.avi_controller)
                self.vs_dict, self.se_dict, self.pool_dict, self.seg_dict = self.gen_inventory_dict()
                #---- remove metrics that are not available in the current version
                self.vs_metric_list, self.se_metric_list, self.controller_metric_list, self.pool_server_metric_list = self.remove_version_specific_metrics()
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
                temp_payload['name_space'] = 'avi||'+self.avi_cluster_name+'||metricscript||executiontime'
                endpoint_payload_list.append(temp_payload)
                send_metriclist_to_endpoint(self.endpoint_list, endpoint_payload_list)
            elif self.login.status_code == 'timedout':
                print(self.avi_cluster_ip+': AVI ERROR: timeout trying to access '+self.avi_cluster_ip)
            elif self.login.status_code == '401':
                print(self.avi_cluster_ip+': AVI ERROR: unable to login to '+self.avi_cluster_ip+' : '+self.login.text)
            else:
                print(self.avi_cluster_ip+': AVI ERROR: unknown login error to '+self.avi_cluster_ip)
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
        avi_cluster_name = entry['avi_cluster_name']
        c = avi_metrics(avi_controller, avi_cluster_name, entry['avi_user'], isBase64(entry['avi_pass']), entry)
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
    fdir = os.path.abspath(os.path.dirname(__file__))
    configuration = False
    global_endpoint_config = None
    if 'EN_CONFIGURATION' in os.environ:
        try:
            import yaml
            configuration = yaml.safe_load(os.environ['EN_CONFIGURATION'].replace('\t','  '))
            with open('configuration.bak', 'w') as yaml_file:
                 yaml.dump(configuration, yaml_file, default_flow_style=False)
        except:
            print(str(datetime.now())+' Error with Provided Configuration YAML')
            exception_text = traceback.format_exc()
            print(str(datetime.now())+' : '+exception_text)
            sys.exit(1)        
        while True:
            loop_start_time = time.time()
            avi_controller_list = configuration['controllers']
            if 'metrics_endpoint_config' in configuration:
                global_endpoint_config = configuration['metrics_endpoint_config']
            main()
            loop_total_time = time.time()-loop_start_time
            if loop_total_time < 60:
                print(str(datetime.now())+' AVI_SCRIPT: sleeping for '+str(60 - datetime.now().second)+' seconds')
                time.sleep(60 - datetime.now().second)
    else:
        print(str(datetime.now())+' No Configuration provided')
else:
    #----- Get the file path to import configuration, needed for cron
    try:
        fdir = os.path.abspath(os.path.dirname(__file__))
        configuration = False
        global_endpoint_config = None
        import yaml
        print(fdir)
        if os.path.isfile(fdir+'/configuration.yaml') == True:
            with open(fdir+'/configuration.yaml', 'r') as yaml_file:
                configuration = yaml.safe_load(yaml_file)
            #----- Import avi controller info from json file
            if 'metrics_endpoint_config' in configuration:
                global_endpoint_config = configuration['metrics_endpoint_config']
            avi_controller_list = configuration['controllers']
            main()
        else:
            print(str(datetime.now())+' No Configuration provided')    
    except:
        print(str(datetime.now())+' Error with Provided Configuration YAML')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)
        sys.exit(1)
