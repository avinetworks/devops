
import json, requests, urllib3
from flask import Flask, request, jsonify
from datetime import datetime
import time
import traceback
import os
import redis
import cPickle as pickle
import virtualservice_static
import serviceengine_static
import servicediscovery
import pool_static
import controller_static
from multiprocessing import Process



if hasattr(requests.packages.urllib3, 'disable_warnings'):
    requests.packages.urllib3.disable_warnings()

if hasattr(urllib3, 'disable_warnings'):
    urllib3.disable_warnings()
    
#------------------------------------    

avi_controller = os.environ['AVICONTROLLER']
avi_user = os.environ['AVIUSER']
avi_pass = os.environ['AVIPASSWORD']


#------------------------------------

#----- entity lists greater than this value will be replaced with wildcard


#----- interval in seconds to refresh the metrics cache
if 'EN_METRIC_REFRESH_INTERVAL' in os.environ:
    metric_refresh_interval = int(os.environ['EN_METRIC_REFRESH_INTERVAL'])
    if metric_refresh_interval < 60:
        metric_refresh_interval = 60
else:
    metric_refresh_interval = 300


#----- When refreshing cache, if wait is true the cache is refreshed first before returning metrics
#----- if wait is False, metrics from current cache are returned and then the cache is refreshed
#----- set to false if very large config resulting in timeouts while cache is being refreshed
if 'EN_WAIT_FOR_CACHE' in os.environ:
    wait_for_cache = os.environ['EN_WAIT_FOR_CACHE'].lower()
    if 'false' in wait_for_cache:
        wait_for_cache = False
    else:
        wait_for_cache = True
else:
    wait_for_cache = True


#------------------------------------
#----- Default List of Metrics for each entity type

default_vs_metric_list  = [
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
default_vs_metric_list = ','.join(default_vs_metric_list)   
#------        
default_se_metric_list = [
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
default_se_metric_list = ','.join(default_se_metric_list)
#------          
default_controller_metric_list  = [
    'controller_stats.avg_cpu_usage',
    'controller_stats.avg_disk_usage',
    'controller_stats.avg_mem_usage'
    ]
default_controller_metric_list = ','.join(default_controller_metric_list)
#----
default_pool_metric_list = [
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
default_pool_metric_list = ','.join(default_pool_metric_list)


#------------------------------------

def avi_login():
    global login
    try:
        if r.get('avi_login') == None:
            login = requests.post('https://%s/login' %avi_controller, verify=False, data={'username': avi_user, 'password': avi_pass},timeout=15)
            r.set('avi_login',pickle.dumps(login))
            return login
        else:
            cookies=dict()
            login = pickle.loads(r.get('avi_login'))
            if 'avi-sessionid' in login.cookies.keys():
                cookies['avi-sessionid'] = login.cookies['avi-sessionid']
            else:
                cookies['sessionid'] = login.cookies['sessionid']
            headers = ({"X-Avi-Tenant": "admin", 'content-type': 'application/json'})
            resp = requests.get('https://%s/api/cluster' %avi_controller, verify=False, headers = headers,cookies=cookies,timeout=5)
            if resp.status_code == 200:
                return login
            else:
                login = requests.post('https://%s/login' %avi_controller, verify=False, data={'username': avi_user, 'password': avi_pass},timeout=15)
                r.set('avi_login',pickle.dumps(login))
                return login

    except:
        login = requests.post('https://%s/login' %avi_controller, verify=False, data={'username': avi_user, 'password': avi_pass},timeout=15)
        r.set('avi_login',pickle.dumps(login))
        return login


def avi_request(avi_api,tenant,api_version='17.2.1'):
    cookies=dict()
    if 'avi-sessionid' in login.cookies.keys():
        cookies['avi-sessionid'] = login.cookies['avi-sessionid']
    else:
        cookies['sessionid'] = login.cookies['sessionid']
    headers = ({'X-Avi-Tenant': '%s' %tenant, 'content-type': 'application/json', 'X-Avi-Version': '%s' %api_version})
    return requests.get('https://%s/api/%s' %(avi_controller,avi_api), verify=False, headers = headers,cookies=cookies,timeout=50)


def avi_post(api_url,tenant,payload,api_version='17.2.1'):
    cookies=dict()
    if 'avi-sessionid' in login.cookies.keys():
        cookies['avi-sessionid'] = login.cookies['avi-sessionid']
    else:
        cookies['sessionid'] = login.cookies['sessionid']
    headers = ({"X-Avi-Tenant": "%s" %tenant, 'content-type': 'application/json','referer': 'https://%s' %avi_controller, 'X-CSRFToken': dict(login.cookies)['csrftoken'],'X-Avi-Version':'%s' %api_version})
    cookies['csrftoken'] = login.cookies['csrftoken']
    return requests.post('https://%s/api/%s' %(avi_controller,api_url), verify=False, headers = headers,cookies=cookies, data=json.dumps(payload),timeout=50)




def remove_version_specific_metrics(entity_type,metric_list):
    try:
    #----- Generate List of Available Metrics
        if r.get('available_metrics_last_poll_time') == None:
            r.set('available_metrics_last_poll_time', (time.time()-3601))
        if r.get('metric_id_polling') == None:
            r.set('metric_id_polling', 'False')
        if (time.time() - float(r.get('available_metrics_last_poll_time')) > 3600 or r.get('available_metrics') == None) and r.get('metric_id_polling') == 'False':
            r.set('metric_id_polling', 'True')
            resp = avi_request('analytics/metric_id',login.json()['tenants'][0]['name']).json()
            _available_metrics = {}
            for m in resp['results']:
                _available_metrics[m['name']]=m['entity_types']
            r.set('available_metrics', pickle.dumps(_available_metrics))
            r.set('available_metrics_last_poll_time', time.time())
            r.set('metric_id_polling', 'False')
        available_metrics = pickle.loads(r.get('available_metrics'))
        _metrics = metric_list.replace(' ','').split(',')
        _metric_list = []
        if entity_type == 'virtualservice':
            for m in _metrics:
                if m.lower() in available_metrics:
                    if 'virtualservice' in available_metrics[m.lower()]:
                        _metric_list.append(m)
        elif entity_type == 'serviceengine':
            for m in _metrics:
                if m.lower() in available_metrics:
                    if 'serviceengine' in available_metrics[m.lower()]:
                        _metric_list.append(m)
        elif entity_type == 'pool':
            for m in _metrics:
                if m.lower() in available_metrics:
                    if 'pool' in available_metrics[m.lower()]:
                        _metric_list.append(m)
        elif entity_type == 'controller':
            for m in _metrics:
                if m.lower() in available_metrics:
                    if 'cluster' in available_metrics[m.lower()]:
                        _metric_list.append(m)
        _metric_list = ','.join(_metric_list)
        return _metric_list
    except:
        r.set('metric_id_polling', 'False')
        print(str(datetime.now())+' '+avi_controller+': remove_version_specific_metrics encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)





#----------
def generate_params_list(request):
    d=request.args.to_dict()
    tenant_list = []
    all_tenants = []
    ten_inv = avi_request('tenant?fields=name&page_size=200','admin')
    if ten_inv.status_code != 403:
        resp = ten_inv.json()
        page_number = 1
        while 'next' in resp:
            page_number += 1
            resp = avi_request('tenant?fields=name&page_size=200&page='+str(page_number),'admin').json()
            for v in resp['results']:
                ten_inv.json()['results'].append(v)
        for t in ten_inv.json()['results']:
            all_tenants.append(t['name'])
    else:
        for t in login.json()['tenants']:
            all_tenants.append(t['name'])
    if 'tenant' in d:
        for t in all_tenants:
            if t.lower() in request.args.get('tenant').lower().split(','):
                tenant_list.append(t)
    else:
        for t in all_tenants:
            tenant_list.append(t)
    if 'cloud' in d:
        cloud_list = request.args.get('cloud').lower().split(',')
    else:
        cloud_list = ['*']
    if 'entity_uuid' in d:
        uuid_list = request.args.get('entity_uuid').lower().split(',') 
    else:
        uuid_list = '*'
    r.set('tenant_list', pickle.dumps(all_tenants)) 
    return tenant_list,cloud_list, uuid_list


#---------------------------------------------------------------------------------------------------------

#-----------------------------------
#----- Service engine statistics


#----- build lists for requested params, allows for multiple jobs servers to scrape different metrics
def serviceengine_metrics_params(request):
    if r.get('se_entity_uuid') == None:
        r.set('se_entity_uuid',pickle.dumps({}))
    if r.get('se_metric_id') == None:
        r.set('se_metric_id',pickle.dumps({}))
    if r.get('se_tenant') == None:
        r.set('se_tenant',pickle.dumps({}))
    if r.get('se_cloud') == None:
        r.set('se_cloud',pickle.dumps({}))
    if r.get('se_runtime') == None:
        r.set('se_runtime',pickle.dumps({}))     
    d=request.args.to_dict()
    tenant_list,cloud_list,uuid_list = generate_params_list(request)
    if 'metric_id' in d:
        metric_id = request.args.get('metric_id').lower()
    else:
        metric_id = default_se_metric_list
    se_metric_list = remove_version_specific_metrics('serviceengine',metric_id)
    _metric_list = se_metric_list.split(',')
    #---- define metric id list
    _se_metric_id = pickle.loads(r.get('se_metric_id'))
    for m in _metric_list:
        _se_metric_id[m] = time.time()
    _removal = []
    for m in _se_metric_id:
        if (time.time() - _se_metric_id[m]) > (metric_refresh_interval*2):
            _removal.append(m)
    for m in _removal:
        _se_metric_id.pop(m, None)
    r.set('se_metric_id', pickle.dumps(_se_metric_id))
    #---- define tenant list
    _tenant_dict = pickle.loads(r.get('se_tenant'))
    for t in tenant_list:
        _tenant_dict[t] = time.time()
    _removal = []
    for t in _tenant_dict:
        if (time.time() - _tenant_dict[t]) > (metric_refresh_interval*2):
            _removal.append(t)
    for t in _removal:      
        _tenant_dict.pop(t, None)
    r.set('se_tenant', pickle.dumps(_tenant_dict))
    #---- define se runtime for tenant
    _se_runtime = pickle.loads(r.get('se_runtime'))
    if 'runtime' in d:
        if request.args.get('runtime').lower() == 'true':
            for t in _tenant_dict:
                _se_runtime[t] = time.time()
    _removal = []
    for t in _se_runtime:
        if (time.time() - _se_runtime[t]) > (metric_refresh_interval*2):
            _removal.append(t)
    for t in _removal:
        _se_runtime.pop(t, None)
    r.set('se_runtime', pickle.dumps(_se_runtime))
    #---- define cloud list
    _cloud_dict = pickle.loads(r.get('se_cloud'))
    for c in cloud_list:
        _cloud_dict[c] = time.time()
    _removal = []
    for c in _cloud_dict:
        if (time.time() - _cloud_dict[c]) > (metric_refresh_interval*2):
            _removal.append(c)
    for c in _removal:
        _cloud_dict.pop(c, None)
    r.set('se_cloud', pickle.dumps(_cloud_dict))
   #---- define uuid list
    _uuid_dict = pickle.loads(r.get('se_entity_uuid'))
    for u in uuid_list:
        _uuid_dict[u] = time.time()
    _removal = []
    for u in _uuid_dict:
        if (time.time() - _uuid_dict[u]) > (metric_refresh_interval*2):
            _removal.append(u)
    for u in _removal:
        _uuid_dict.pop(u, None)
    r.set('se_entity_uuid', pickle.dumps(_uuid_dict))



    




#---- filters metrics from cache to return only what's requested in the Prometheus requests
def serviceengine_filter_metrics(request):
    d=request.args.to_dict()
    se_metrics = pickle.loads(r.get('se_metrics'))
    se_metrics_runtime = pickle.loads(r.get('se_metrics_runtime'))
    tenant_list,cloud_list,uuid_list = generate_params_list(request)
    if 'metric_id' in d:
        se_metric_list = request.args.get('metric_id').lower()
    else:
        se_metric_list = default_se_metric_list
    se_metric_list = remove_version_specific_metrics('serviceengine',se_metric_list)
    _metric_list = se_metric_list.replace('.','_').split(',')
    if 'runtime' in d:
        if request.args.get('runtime').lower() == 'true':
            _metric_list = _metric_list + se_metrics_runtime
    #----- filter results based upon request params
    list_to_remove = []
    #----- filter metrics
    for l in se_metrics:
        if '# HELP ' in l or '# TYPE ' in l:
            if l.split(' ')[2] not in _metric_list:
                list_to_remove.append(l)
        else:
            if l.split(' ')[0] not in _metric_list:
                list_to_remove.append(l)
    for e in list_to_remove:
        se_metrics.remove(e)
    #----- filter by UUID
    if uuid_list !='*':
        list_to_remove = []
        for l in se_metrics:
            if "# " not in l:
                if l.split('uuid="')[1].split('"',1)[0] not in uuid_list:
                    list_to_remove.append(l)
        for e in list_to_remove:
            se_metrics.remove(e)
    #----- filter by tenant
    else:
        list_to_remove = []
        for l in se_metrics:
            if "# " not in l:
                if l.split('tenant="')[1].split('"',1)[0] not in tenant_list:
                    list_to_remove.append(l)
        for e in list_to_remove:
            se_metrics.remove(e)
    #----- filter by cloud
    if '*' not in cloud_list:
        list_to_remove = []
        for l in se_metrics:
            if "# " not in l:
                if l.split('cloud="')[1].split('"',1)[0] not in cloud_list:
                    list_to_remove.append(l)
        for e in list_to_remove:
            se_metrics.remove(e)
    #----- remove emtpy comment lines
    list_to_remove = []
    _mlist = []
    for l in se_metrics:    
        if "# " not in l:
            _mlist.append(l.split(' ')[0])
    for l in se_metrics:
        if "# " in l:
            if l.split(' ')[2] not in _mlist:
                list_to_remove.append(l)
    if len(list_to_remove) > 0:
        for e in list_to_remove:
            se_metrics.remove(e)
    #-----
    se_metrics.append('\n')
    se_metrics = '\n'.join(se_metrics)
    return se_metrics



def serviceengine_metrics(request):
    try:
        if r.get('se_last_poll_time') == None:
            r.set('se_last_poll_time', (time.time()-(metric_refresh_interval+10)))
        if r.get('se_last_poll_start_time') == None:
            r.set('se_last_poll_start_time', (time.time()-(metric_refresh_interval+20)))
        if r.get('se_metrics') == None:
            r.set('se_metrics',pickle.dumps([]))
        if r.get('se_metrics_runtime') == None:
            r.set('se_metrics_runtime',pickle.dumps([]))  
        if r.get('se_polling') == None:
            r.set('se_polling', 'False')
        if time.time() - float(r.get('se_last_poll_start_time')) > metric_refresh_interval and r.get('se_polling') == 'False':
            r.set('se_polling','True')   
            serviceengine_metrics_params(request)
            if wait_for_cache == False:
                se_metrics = serviceengine_filter_metrics(request)
                p = Process(target = serviceengine_static.refresh_serviceengine_metrics, args = (r,login,avi_controller,))
                p.start()
            else:
                serviceengine_static.refresh_serviceengine_metrics(r,login,avi_controller)
                se_metrics = serviceengine_filter_metrics(request)
            return se_metrics
        else:
            print(str(datetime.now())+' =====> Using cached Serviceengine metrics')
            serviceengine_metrics_params(request)
            se_metrics = serviceengine_filter_metrics(request)
            if time.time() - float(r.get('se_last_poll_time')) > (metric_refresh_interval * 2):
                r.set('se_metrics',pickle.dumps([]))
                if r.get('se_polling') == 'True':
                    r.set('se_polling', 'False')
            return se_metrics
    except:
        print(str(datetime.now())+' '+avi_controller+': func serviceengine_metrics encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return False

#---------------------------------------------------------------------------------------------------------




#---------------------------------------------------------------------------------------------------------


#-----------------------------------
#----- Virtual service statistics - STATIC prometheus setup

#----- build lists for requested params, allows for multiple jobs servers to scrape different metrics
def virtualservice_metrics_params(request):
    if r.get('vs_entity_uuid') == None:
        r.set('vs_entity_uuid',pickle.dumps({}))
    if r.get('vs_metric_id') == None:
        r.set('vs_metric_id',pickle.dumps({}))
    if r.get('vs_tenant') == None:
        r.set('vs_tenant',pickle.dumps({}))
    if r.get('vs_cloud') == None:
        r.set('vs_cloud',pickle.dumps({}))
    d=request.args.to_dict()
    tenant_list,cloud_list,uuid_list = generate_params_list(request)
    if 'metric_id' in d:
        metric_id = request.args.get('metric_id').lower()
    else:
        metric_id = default_vs_metric_list
    vs_metric_list = remove_version_specific_metrics('virtualservice',metric_id)
    _metric_list = vs_metric_list.split(',')
    #---- define metric id list
    _vs_metric_id = pickle.loads(r.get('vs_metric_id'))
    for m in _metric_list:
        _vs_metric_id[m] = time.time()
    _removal = []
    for m in _vs_metric_id:
        if (time.time() - _vs_metric_id[m]) > (metric_refresh_interval*2):
            _removal.append(m)
    for m in _removal:
        _vs_metric_id.pop(m, None)
    r.set('vs_metric_id', pickle.dumps(_vs_metric_id))
    #---- define tenant list
    _tenant_dict = pickle.loads(r.get('vs_tenant'))
    for t in tenant_list:
        _tenant_dict[t] = time.time()
    _removal = []
    for t in _tenant_dict:
        if (time.time() - _tenant_dict[t]) > (metric_refresh_interval*2):
            _removal.append(t)
    for t in _removal:      
        _tenant_dict.pop(t, None)
    r.set('vs_tenant', pickle.dumps(_tenant_dict))
    #---- define cloud list
    _cloud_dict = pickle.loads(r.get('vs_cloud'))
    for c in cloud_list:
        _cloud_dict[c] = time.time()
    _removal = []
    for c in _cloud_dict:
        if (time.time() - _cloud_dict[c]) > (metric_refresh_interval*2):
            _removal.append(c)
    for c in _removal:
        _cloud_dict.pop(c, None)
    r.set('vs_cloud', pickle.dumps(_cloud_dict))
   #---- define uuid list
    _uuid_dict = pickle.loads(r.get('vs_entity_uuid'))
    for u in uuid_list:
        _uuid_dict[u] = time.time()
    _removal = []
    for u in _uuid_dict:
        if (time.time() - _uuid_dict[u]) > (metric_refresh_interval*2):
            _removal.append(u)
    for u in _removal:
        _uuid_dict.pop(u, None)
    r.set('vs_entity_uuid', pickle.dumps(_uuid_dict))


    




#---- filters metrics from cache to return only what's requested in the Prometheus requests
def virtualservice_filter_metrics(request):
    d=request.args.to_dict()
    vs_metrics = pickle.loads(r.get('vs_metrics'))
    tenant_list,cloud_list,uuid_list = generate_params_list(request)
    if 'metric_id' in d:
        vs_metric_list = request.args.get('metric_id').lower()
    else:
        vs_metric_list = default_vs_metric_list
    vs_metric_list = remove_version_specific_metrics('virtualservice',vs_metric_list)
    _metric_list = vs_metric_list.replace('.','_').split(',')
    #----- filter results based upon request params
    list_to_remove = []
    #----- filter metrics
    for l in vs_metrics:
        if '# HELP ' in l or '# TYPE ' in l:
            if l.split(' ')[2] not in _metric_list:
                list_to_remove.append(l)
        else:
            if l.split(' ')[0] not in _metric_list:
                list_to_remove.append(l)
    for e in list_to_remove:
        vs_metrics.remove(e)
    #----- filter by UUID
    if uuid_list !='*':
        list_to_remove = []
        for l in vs_metrics:
            if "# " not in l:
                if l.split('uuid="')[1].split('"',1)[0] not in uuid_list:
                    list_to_remove.append(l)
        for e in list_to_remove:
            vs_metrics.remove(e)
    #----- filter by tenant
    else:
        list_to_remove = []
        for l in vs_metrics:
            if "# " not in l:
                if l.split('tenant="')[1].split('"',1)[0] not in tenant_list:
                    list_to_remove.append(l)
        for e in list_to_remove:
            vs_metrics.remove(e)
    #----- filter by cloud
    if '*' not in cloud_list:
        list_to_remove = []
        for l in vs_metrics:
            if "# " not in l:
                if l.split('cloud="')[1].split('"',1)[0] not in cloud_list:
                    list_to_remove.append(l)
        for e in list_to_remove:
            vs_metrics.remove(e)
    #----- remove emtpy comment lines
    list_to_remove = []
    _mlist = []
    for l in vs_metrics:    
        if "# " not in l:
            _mlist.append(l.split(' ')[0])
    for l in vs_metrics:
        if "# " in l:
            if l.split(' ')[2] not in _mlist:
                list_to_remove.append(l)
    if len(list_to_remove) > 0:
        for e in list_to_remove:
            vs_metrics.remove(e)
    #-----
    vs_metrics.append('\n')
    vs_metrics = '\n'.join(vs_metrics)
    return vs_metrics

                  
#----------

def virtualservice_metrics(request):
    try:
        if r.get('vs_last_poll_time') == None:
            r.set('vs_last_poll_time', (time.time()-(metric_refresh_interval+10)))
        if r.get('vs_last_poll_start_time') == None:
            r.set('vs_last_poll_start_time', (time.time()-(metric_refresh_interval+20)))            
        if r.get('vs_metrics') == None:
            r.set('vs_metrics',pickle.dumps([]))
        if r.get('vs_polling') == None:
            r.set('vs_polling', 'False')
        if time.time() - float(r.get('vs_last_poll_start_time')) > metric_refresh_interval and r.get('vs_polling') == 'False':
            r.set('vs_polling','True')   
            virtualservice_metrics_params(request)
            if wait_for_cache == False:
                vs_metrics = virtualservice_filter_metrics(request)
                p = Process(target = virtualservice_static.refresh_vs_metrics, args = (r,login,avi_controller,))
                p.start()
            else:
                virtualservice_static.refresh_vs_metrics(r,login,avi_controller)
                vs_metrics = virtualservice_filter_metrics(request)
            return vs_metrics
        else:
            print(str(datetime.now())+' =====> Using cached Virtualservice metrics')
            virtualservice_metrics_params(request)
            vs_metrics = virtualservice_filter_metrics(request)
            if time.time() - float(r.get('vs_last_poll_time')) > (metric_refresh_interval * 2):
                r.set('vs_metrics',pickle.dumps([]))
                if r.get('vs_polling') == 'True':
                    r.set('vs_polling', 'False')
            return vs_metrics
    except:
        print(str(datetime.now())+' '+avi_controller+': func virtualservice_metrics encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return False

#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------

#-----------------------------------
#----- Virtual service statistics -  Prometheus service discovery


def update_servicediscovery_targets(request):
    try:
        if r.get('sd_targets') == None:
            r.set('sd_targets',pickle.dumps({}))
        if r.get('sd_names') == None:
            r.set('sd_names', pickle.dumps({}))        
        sd_names = pickle.loads(r.get('sd_names'))
        sd_targets = pickle.loads(r.get('sd_targets'))
        d=request.args.to_dict()
        tenant = request.args.get('kubernetes_namespace')
        vs_name = request.args.get('virtualservice')
        if 'metric_id' in d:
            sd_metric_list = request.args.get('metric_id').lower()
        else:
            sd_metric_list = default_vs_metric_list
        if tenant not in sd_names:
            sd_names[tenant] = {}
        if 'extra_metrics' in d:
            extra_metrics = request.args.get('extra_metrics')
            sd_metric_list = (sd_metric_list+','+extra_metrics).replace(' ','')
        sd_metric_list = remove_version_specific_metrics('virtualservice',sd_metric_list)
        sd_metric_list = sd_metric_list.split(',')
        #---- remove unneccesary metrics
        if vs_name in sd_names[tenant]:
            uuid = sd_names[tenant][vs_name]
            sd_targets[uuid]['vs_metric_list'] = sd_metric_list
            r.set('sd_targets',pickle.dumps(sd_targets))
        else:
            print(str(datetime.now())+' =====> New VS discovered: %s' %vs_name)
            resp = avi_request('virtualservice?name=%s&fields=cloud_ref,tenant_ref&include_name=true' %vs_name, tenant)
            if resp.status_code == 200:
                if resp.json()['count'] == 1:
                    cloud = resp.json()['results'][0]['cloud_ref'].split('#')[1]
                    entity_uuid = resp.json()['results'][0]['uuid']
                    temp_name = resp.json()['results'][0]['name']
                    sd_names[tenant][temp_name] = entity_uuid
                    r.set('sd_names', pickle.dumps(sd_names))  
                    sd_targets[entity_uuid] = {'vs_metric_list': sd_metric_list, 'cloud': cloud, 'lastquery': time.time(), 'lastresponse': time.time()}
                    r.set('sd_targets', pickle.dumps(sd_targets))                
            else:
                print(str(datetime.now())+' =====> ERROR update_servicediscovery_targets: %s' %resp.text) 
                return ['ERROR',resp.status_code,resp.text]
        return ['SUCCESS']
    except: 
        print(str(datetime.now())+' '+avi_controller+': func update_servicediscovery_targets encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return False

#----------


#----------    

def virtualservice_servicediscovery_metrics(request):
    try:
        if r.get('sd_polling') == None:
            r.set('sd_polling','False')
        if r.get('sd_last_poll_time') == None:
            r.set('sd_last_poll_time',(time.time()-(metric_refresh_interval+10))) 
        if r.get('sd_last_poll_start_time') == None:
            r.set('sd_last_poll_start_time',(time.time()-(metric_refresh_interval+20))) 
        if r.get('sd_metrics') == None:
            r.set('sd_metrics', pickle.dumps([]))   
        status = update_servicediscovery_targets(request)
        if status[0] != 'SUCCESS':
            return status[0]+'|'+str(status[1])+'|'+status[2]
        else:
            if time.time() - float(r.get('sd_last_poll_start_time')) > metric_refresh_interval and r.get('sd_polling') == 'False':
                r.set('sd_polling','True')
                if wait_for_cache == False:
                    p = Process(target = servicediscovery.update_servicediscovery_metric_cache_multiprocess, args = (r,login,avi_controller,metric_refresh_interval,))
                    p.start()
                else:
                    servicediscovery.update_servicediscovery_metric_cache_multiprocess(r,login,avi_controller,metric_refresh_interval)
            else:
                print(str(datetime.now())+' =====> Using cached Servicediscovery metrics')
            sd_names = pickle.loads(r.get('sd_names'))
            sd_targets = pickle.loads(r.get('sd_targets'))
            sd_metrics = pickle.loads(r.get('sd_metrics'))
            tenant = request.args.get('kubernetes_namespace')
            vs_name = request.args.get('virtualservice')
            uuid = sd_names[tenant][vs_name]
            #prom_metrics = ''
            prom_metrics = ['\n']
            for s in sd_metrics:
                for v in s:
                    if v == uuid:
                        for m in s[v]:
                            if 'data' in m:
                                temp_tags = ''
                                #----- check is metric is desired for the vs
                                if m['header']['name'] in sd_targets[uuid]['vs_metric_list']:
                                    metric_name = m['header']['name'].replace('.','_').replace('-','_')
                                    metric_description = m['header']['metric_description']
                                    metric_value = m['data'][0]['value']
                                    temp_payload = {}
                                    temp_payload['name'] = vs_name
                                    temp_payload['uuid'] = uuid
                                    temp_payload['cloud'] = sd_targets[uuid]['cloud']
                                    temp_payload['tenant'] = tenant
                                    temp_payload['entity_type'] = 'virtualservice'
                                    for e in temp_payload:
                                        temp_tags=temp_tags+(str(e+'="'+temp_payload[e]+'",'))
                                    temp_tags = '{'+temp_tags.rstrip(',')+'}'
                                    #prom_metrics = prom_metrics+'\n'+'# HELP '+metric_name+' '+metric_description
                                    #prom_metrics = prom_metrics+'\n'+'# TYPE '+metric_name+' gauge'
                                    #prom_metrics = prom_metrics+'\n'+metric_name+''+temp_tags+' '+str(metric_value)
                                    prom_metrics.append('%s 01# HELP %s %s' %(metric_name,metric_name, metric_description))
                                    prom_metrics.append('%s 02# TYPE %s gauge' %(metric_name,metric_name))                                                
                                    prom_metrics.append('%s %s %s' %(metric_name,temp_tags,str(metric_value)))                                         
                                    sd_targets[uuid]['lastquery'] = time.time()
                                    sd_targets[uuid]['lastresponse'] = time.time()
            r.set('sd_targets',pickle.dumps(sd_targets))
            #prom_metrics = prom_metrics+'\n'
            prom_metrics = list(set(prom_metrics))
            prom_metrics = sorted(prom_metrics)
            for idx, item in enumerate(prom_metrics):
                if '01#' in item:
                   item = item.split('01',1)[1]
                   prom_metrics[idx] = item
                elif '02#' in item:
                   item = item.split('02',1)[1]
                   prom_metrics[idx] = item                
            prom_metrics.append('\n')
            prom_metrics = '\n'.join(prom_metrics)
            if time.time() - float(r.get('sd_last_poll_time')) > (metric_refresh_interval * 2):
                r.set('sd_metrics',pickle.dumps(''))
                if r.get('sd_polling') == 'True':
                    r.set('sd_polling', 'False')
            return prom_metrics
    except:
        r.set('sd_polling','False')
        print(str(datetime.now())+' '+avi_controller+': func virtualservice_servicediscovery_metrics encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return False
    

#---------------------------------------------------------------------------------------------------------    
    
    
#---------------------------------------------------------------------------------------------------------

#-----------------------------------
#----- Pool statistics

#----- build lists for requested params, allows for multiple jobs servers to scrape different metrics
def pool_metrics_params(request):
    if r.get('pool_entity_uuid') == None:
        r.set('pool_entity_uuid',pickle.dumps({}))
    if r.get('pool_metric_id') == None:
        r.set('pool_metric_id',pickle.dumps({}))
    if r.get('pool_tenant') == None:
        r.set('pool_tenant',pickle.dumps({}))
    if r.get('pool_cloud') == None:
        r.set('pool_cloud',pickle.dumps({}))
    d=request.args.to_dict()
    tenant_list,cloud_list,uuid_list = generate_params_list(request)
    if 'metric_id' in d:
        metric_id = request.args.get('metric_id').lower()
    else:
        metric_id = default_pool_metric_list
    pool_metric_list = remove_version_specific_metrics('pool',metric_id)
    _metric_list = pool_metric_list.split(',')
    #---- define metric id list
    _pool_metric_id = pickle.loads(r.get('pool_metric_id'))
    for m in _metric_list:
        _pool_metric_id[m] = time.time()
    _removal = []
    for m in _pool_metric_id:
        if (time.time() - _pool_metric_id[m]) > (metric_refresh_interval*2):
            _removal.append(m)
    for m in _removal:
        _pool_metric_id.pop(m, None)
    r.set('pool_metric_id', pickle.dumps(_pool_metric_id))
    #---- define tenant list
    _tenant_dict = pickle.loads(r.get('pool_tenant'))
    for t in tenant_list:
        _tenant_dict[t] = time.time()
    _removal = []
    for t in _tenant_dict:
        if (time.time() - _tenant_dict[t]) > (metric_refresh_interval*2):
            _removal.append(t)
    for t in _removal:      
        _tenant_dict.pop(t, None)
    r.set('pool_tenant', pickle.dumps(_tenant_dict))
    #---- define cloud list
    _cloud_dict = pickle.loads(r.get('pool_cloud'))
    for c in cloud_list:
        _cloud_dict[c] = time.time()
    _removal = []
    for c in _cloud_dict:
        if (time.time() - _cloud_dict[c]) > (metric_refresh_interval*2):
            _removal.append(c)
    for c in _removal:
        _cloud_dict.pop(c, None)
    r.set('pool_cloud', pickle.dumps(_cloud_dict))
   #---- define uuid list
    _uuid_dict = pickle.loads(r.get('pool_entity_uuid'))
    for u in uuid_list:
        _uuid_dict[u] = time.time()
    _removal = []
    for u in _uuid_dict:
        if (time.time() - _uuid_dict[u]) > (metric_refresh_interval*2):
            _removal.append(u)
    for u in _removal:
        _uuid_dict.pop(u, None)
    r.set('pool_entity_uuid', pickle.dumps(_uuid_dict))


    




#---- filters metrics from cache to return only what's requested in the Prometheus requests
def pool_filter_metrics(request):
    d=request.args.to_dict()
    pool_metrics = pickle.loads(r.get('pool_metrics'))
    tenant_list,cloud_list,uuid_list = generate_params_list(request)
    if 'metric_id' in d:
        pool_metric_list = request.args.get('metric_id').lower()
    else:
        pool_metric_list = default_pool_metric_list
    pool_metric_list = remove_version_specific_metrics('pool',pool_metric_list)
    _metric_list = pool_metric_list.replace('.','_').split(',')
    #----- filter results based upon request params
    list_to_remove = []
    #----- filter metrics
    for l in pool_metrics:
        if '# HELP ' in l or '# TYPE ' in l:
            if l.split(' ')[2] not in _metric_list:
                list_to_remove.append(l)
        else:
            if l.split(' ')[0] not in _metric_list:
                list_to_remove.append(l)
    for e in list_to_remove:
        pool_metrics.remove(e)
    #----- filter by UUID
    if uuid_list !='*':
        list_to_remove = []
        for l in pool_metrics:
            if "# " not in l:
                if l.split('uuid="')[1].split('"',1)[0] not in uuid_list:
                    list_to_remove.append(l)
        for e in list_to_remove:
            pool_metrics.remove(e)
    #----- filter by tenant
    else:
        list_to_remove = []
        for l in pool_metrics:
            if "# " not in l:
                if l.split('tenant="')[1].split('"',1)[0] not in tenant_list:
                    list_to_remove.append(l)
        for e in list_to_remove:
            pool_metrics.remove(e)
    #----- filter by cloud
    if '*' not in cloud_list:
        list_to_remove = []
        for l in pool_metrics:
            if "# " not in l:
                if l.split('cloud="')[1].split('"',1)[0] not in cloud_list:
                    list_to_remove.append(l)
        for e in list_to_remove:
            pool_metrics.remove(e)
    #----- remove emtpy comment lines
    list_to_remove = []
    _mlist = []
    for l in pool_metrics:    
        if "# " not in l:
            _mlist.append(l.split(' ')[0])
    for l in pool_metrics:
        if "# " in l:
            if l.split(' ')[2] not in _mlist:
                list_to_remove.append(l)
    if len(list_to_remove) > 0:
        for e in list_to_remove:
            pool_metrics.remove(e)
    #-----
    pool_metrics.append('\n')
    pool_metrics = '\n'.join(pool_metrics)
    return pool_metrics





def pool_metrics(request):
    try:
        if r.get('pool_last_poll_time') == None:
            r.set('pool_last_poll_time', (time.time()-(metric_refresh_interval+10)))
        if r.get('pool_last_poll_start_time') == None:
            r.set('pool_last_poll_start_time', (time.time()-(metric_refresh_interval+20)))            
        if r.get('pool_metrics') == None:
            r.set('pool_metrics',pickle.dumps([]))
        if r.get('pool_polling') == None:
            r.set('pool_polling', 'False')
        if time.time() - float(r.get('pool_last_poll_start_time')) > metric_refresh_interval and r.get('pool_polling') == 'False':
            pool_metrics_params(request)
            if wait_for_cache == False:
                pool_metrics = pool_filter_metrics(request)
                p = Process(target = pool_static.refresh_pool_metrics, args = (r,login,avi_controller,))
                p.start()
            else:
                pool_static.refresh_pool_metrics(r,login,avi_controller)
                pool_metrics = pool_filter_metrics(request)
            return pool_metrics
        else:
            print(str(datetime.now())+' =====> Using cached Pool metrics')
            pool_metrics_params(request)
            pool_metrics = pool_filter_metrics(request)            
            #pool_metrics = pickle.loads(r.get('pool_metrics'))
            if time.time() - float(r.get('pool_last_poll_time')) > (metric_refresh_interval * 2):
                r.set('pool_metrics',pickle.dumps([]))
                if r.get('pool_polling') == 'True':
                    r.set('pool_polling', 'False')
            return pool_metrics
    except:
        r.set('pool_polling','False')      
        print(str(datetime.now())+' '+avi_controller+': func pool_metrics encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return False


#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------
#-----------------------------------
#----- GET controller Member specific statistics


#----- build lists for requested params, allows for multiple jobs servers to scrape different metrics
def controller_metrics_params(request):
    if r.get('ctl_metric_id') == None:
        r.set('ctl_metric_id',pickle.dumps({}))
    if r.get('ctl_runtime') == None:
        r.set('ctl_runtime',pickle.dumps({}))  
    d=request.args.to_dict()
    if 'metric_id' in d:
        metric_id = request.args.get('metric_id').lower()
    else:
        metric_id = default_controller_metric_list
    controller_metric_list = remove_version_specific_metrics('controller',metric_id)
    _metric_list = controller_metric_list.split(',')
    #---- define metric id list
    _controller_metric_id = pickle.loads(r.get('ctl_metric_id'))
    for m in _metric_list:
        _controller_metric_id[m] = time.time()
    _removal = []
    for m in _controller_metric_id:
        if (time.time() - _controller_metric_id[m]) > (metric_refresh_interval*2):
            _removal.append(m)
    for m in _removal:
        _controller_metric_id.pop(m, None)
    r.set('ctl_metric_id', pickle.dumps(_controller_metric_id))
    #---- define ctl runtime
    _ctl_runtime = pickle.loads(r.get('ctl_runtime'))
    if 'runtime' in d:
        if request.args.get('runtime').lower() == 'true':
            _ctl_runtime['true'] = time.time()
    _removal = []
    for t in _ctl_runtime:
        if (time.time() - _ctl_runtime[t]) > (metric_refresh_interval*2):
            _removal.append(t)
    for t in _removal:
        _ctl_runtime.pop(t, None)
    r.set('ctl_runtime', pickle.dumps(_ctl_runtime))



    




#---- filters metrics from cache to return only what's requested in the Prometheus requests
def controller_filter_metrics(request):
    ctl_metrics = pickle.loads(r.get('ctl_metrics'))
    ctl_metrics_runtime = pickle.loads(r.get('ctl_metrics_runtime'))
    d=request.args.to_dict()
    if 'metric_id' in d:
        ctl_metric_list = request.args.get('metric_id').lower()
    else:
        ctl_metric_list = default_controller_metric_list
    ctl_metric_list = remove_version_specific_metrics('controller',ctl_metric_list)
    _metric_list = ctl_metric_list.replace('.','_').split(',')
    if 'runtime' in d:
        if request.args.get('runtime').lower() == 'true':
            _metric_list = _metric_list + ctl_metrics_runtime
    #----- filter results based upon request params
    list_to_remove = []
    #----- filter metrics
    for l in ctl_metrics:
        if '# HELP ' in l or '# TYPE ' in l:
            if l.split(' ')[2] not in _metric_list:
                list_to_remove.append(l)
        else:
            if l.split(' ')[0] not in _metric_list:
                list_to_remove.append(l)
    for e in list_to_remove:
        ctl_metrics.remove(e)
    ctl_metrics.append('\n')
    ctl_metrics = '\n'.join(ctl_metrics)
    return ctl_metrics






def controller_metrics(request):
    try:
        if r.get('ctl_last_poll_time') == None:
            r.set('ctl_last_poll_time', (time.time()-(metric_refresh_interval+10)))
        if r.get('ctl_last_poll_start_time') == None:
            r.set('ctl_last_poll_start_time', (time.time()-(metric_refresh_interval+20)))            
        if r.get('ctl_metrics') == None:
            r.set('ctl_metrics',pickle.dumps([]))
        if r.get('ctl_polling') == None:
            r.set('ctl_polling', 'False')
        if r.get('ctl_metrics_runtime') == None:
            r.set('ctl_metrics_runtime',pickle.dumps([]))              
        if time.time() - float(r.get('ctl_last_poll_start_time')) > metric_refresh_interval and r.get('ctl_polling') == 'False': 
            r.set('ctl_polling','True')
            controller_metrics_params(request)
            if wait_for_cache == False:
                ctl_metrics = controller_filter_metrics(request)
                p = Process(target = controller_static.refresh_ctl_metrics, args = (r,login,avi_controller,))
                p.start()
            else:
                controller_static.refresh_ctl_metrics(r,login,avi_controller)
                ctl_metrics = controller_filter_metrics(request)
            return ctl_metrics
        else:
            print(str(datetime.now())+' =====> Using cached Controller metrics')
            controller_metrics_params(request)
            ctl_metrics = controller_filter_metrics(request)
            if time.time() - float(r.get('ctl_last_poll_time')) > (metric_refresh_interval * 2):
                r.set('ctl_metrics',pickle.dumps([]))
                if r.get('ctl_polling') == 'True':
                    r.set('ctl_polling', 'False')
            return ctl_metrics
    except:
        r.set('ctl_polling', 'False')
        print(str(datetime.now())+' '+avi_controller+': func controller_cluster_metrics encountered an error encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return False





#---------------------------------------------------------------------------------------------------------
#-----------------------------------
#------------------------- 

app = Flask(__name__)


@app.route('/metrics', methods=['GET'])
def add_message():
    try:
        req_start_time = time.time()
        d=request.args.to_dict()
        avi_login()
        if request.args.get('entity_type').lower() == 'virtualservice':
            if 'kubernetes_namespace' in d:
                metrics = virtualservice_servicediscovery_metrics(request)
            else:
                metrics = virtualservice_metrics(request)
            #print metrics
        elif request.args.get('entity_type').lower() == 'serviceengine':
            metrics = serviceengine_metrics(request)
            #print metrics
        elif request.args.get('entity_type').lower() == 'controller':
            metrics = controller_metrics(request) 
            #print metrics
        elif request.args.get('entity_type').lower() == 'pool':
            metrics = pool_metrics(request)
            #print metrics
        else:
            return '', 500
        req_total_time = str(time.time()-req_start_time)
        print(str(datetime.now())+' =====> request took '+req_total_time+' seconds\n')
        if metrics == False:
            return '', 500
        elif metrics.split('|')[0] == 'ERROR':
            return metrics.split('|')[2], int(metrics.split('|')[1])
        else:
            return metrics, 200
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)



@app.route('/virtualservice_debug', methods=['GET'])
def vs_debug():
    try:
        _1 = '\n<p>=====> Last Polling Time %s</p>\n' %time.ctime(float(r.get('vs_last_poll_time')))
        _2 = '\n<p>=====></p>\n'
        _3 = '\n<p>'+str(pickle.loads(r.get('vs_results')))+'</p>\n'
        _4 = '\n<p>'+str(pickle.loads(r.get('vs_metrics')))+'</p>\n'
        _5 = '\n<p>=====> VS without METRICS %s</p>\n' %str(pickle.loads(r.get('vs_missing_metrics')))
        response = _1+_3+_4+_5
        return response, 200
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return "=====> Virtualservice metrics polling hasn't run yet\n", 200



@app.route('/servicediscovery_debug', methods=['GET'])
def sd_debug():
    try:
        _1 = '\n<p>=====> Last Polling Time %s</p>\n' %time.ctime(float(r.get('sd_last_poll_time')))
        _2 = '\n<p>=====></p>\n'
        _3 = '\n<p>'+str(pickle.loads(r.get('sd_names')))+'</p>\n'
        _4 = '\n<p>'+str(pickle.loads(r.get('sd_targets')))+'</p>\n'
        _5 = '\n<p>'+str(pickle.loads(r.get('sd_metrics')))+'</p>\n'
        response = _1+_3+_4+_5
        return response, 200
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return "=====> Servicediscovery metrics polling hasn't run yet\n", 200
    




@app.route('/serviceengine_debug', methods=['GET'])
def se_debug():
    try:
        _1 = '\n<p>=====> Last Polling Time %s</p>\n' %time.ctime(float(r.get('se_last_poll_time')))
        _2 = '=====>'
        _3 = '\n<p>'+str(pickle.loads(r.get('se_results')))+'</p>\n'
        _4 = '\n</p>'+str(pickle.loads(r.get('se_metrics')))+'</p>\n'
        _5 = '\n<p>=====> Serviceengine without METRICS %s</p>\n' %str(pickle.loads(r.get('se_missing_metrics')))
        response = _1+_3+_4+_5
        return response, 200
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return "=====> Serviceengine metrics polling hasn't run yet\n", 200
    
    

@app.route('/pool_debug', methods=['GET'])
def pool_debug():
    try:
        _1 = '\n<p>=====> Last Polling Time %s</p>\n' %time.ctime(float(r.get('pool_last_poll_time')))
        _2 = '=====>'
        _3 = '\n<p>'+str(pickle.loads(r.get('pool_results')))+'</p>\n'
        _4 = '\n</p>'+str(pickle.loads(r.get('pool_metrics')))+'</p>\n'
        _5 = '\n<p>=====> Pools without METRICS %s</p>\n' %str(pickle.loads(r.get('pool_missing_metrics')))
        response = _1+_3+_4+_5
        return response, 200
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return "=====> Pool metrics polling hasn't run yet\n", 200
    


@app.route('/redis_debug', methods=['GET'])
def redis_debug():
    try:
        d=request.args.to_dict()
        if 'key' in d:
            key = request.args.get('key').lower()
            try:
                value = str(pickle.loads(r.get(key)))
            except:
                value = str(r.get(key))
            _1 = '\n<p>=====> Redis Key %s</p>\n' %key
            _2 = value+'</p>\n'
            response = _1+_2
            return response, 200
        else:
            _1 = '\n<p>=====> All Redis Keys </p>\n'
            response = []
            for key in r.scan_iter("*"):
                response.append(key)
            response = sorted(response)
            response.remove('avi_login')
            response = ('\n'.join(response))+'\n'
            response = _1+response
            return response, 200
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return "=====> Redis Debug has an error\n", 500
    


@app.route('/redis_delete', methods=['GET'])
def redis_delete():
    try:
        d=request.args.to_dict()
        if 'key' in d:
            key = request.args.get('key').lower()
            r.delete(key)
            _1 = '\n<p>=====> Deleted Redis Key %s</p>\n' %key
            _2 = value+'</p>\n'
            response = _1+_2
            return response, 200
        else:
            _1 = '\n<p>=====> Deleted All Redis Keys </p>\n'
            response = []
            for key in r.scan_iter("*"):
                response.append(key)
                r.delete(key)
            response = sorted(response)
            if 'avi_login' in response:
                response.remove('avi_login')
            response = ('\n'.join(response))+'\n'
            response = _1+response
            return response, 200
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return "=====> Redis Flush has an error\n", 500



try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    if __name__ == '__main__':
        app.run(host="0.0.0.0", port=8080, threaded=True)
except:
    exception_text = traceback.format_exc()
    print(str(datetime.now())+' '+avi_controller+': '+exception_text)