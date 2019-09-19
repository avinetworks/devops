import json, requests, urllib3
from flask import Flask, request, jsonify
from datetime import datetime
import time
import traceback
import os
import redis
import cPickle as pickle
from multiprocessing import Process




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





def serviceengine_inventory_multiprocess(r,cloud_list,uuid_list,tenant_list,runtime):
    try:
        se_inventory_cache_start = time.time()
        proc = []
        for t in tenant_list:
            p = Process(target = serviceengine_inventory_child, args = (r,cloud_list,uuid_list,tenant_list,t,runtime,))
            p.start()
            proc.append(p)
            if len(proc) > 10:
                for p in proc:
                    p.join()
                proc = []
        for p in proc:
            p.join()
        #----- get keys, consolidate then delete
        inv_keys = r.keys('temp_se_dict_*')
        se_dict = {}
        for k in inv_keys:
            _1 = pickle.loads(r.get(k))
            se_dict.update(_1)
            r.delete(k)
        se_results = {}
        se_results['TOTAL_SERVICEENGINES'] = len(se_dict)
        for v in se_dict:
            if se_dict[v]['tenant'] not in se_results:
                se_results[se_dict[v]['tenant']] = 1
            else:
                se_results[se_dict[v]['tenant']] += 1
        r.set('se_results', pickle.dumps(se_results))
        r.set('se_dict', pickle.dumps(se_dict))
        temp_total_time = str(time.time()-se_inventory_cache_start)
        print(str(datetime.now())+' =====> Refresh of SE Inventory Cache took %s seconds' %temp_total_time)
    except:
        print(str(datetime.now())+' '+avi_controller+': func serviceengine_inventory_multiprocess encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)





def serviceengine_inventory_child(r,cloud_list,uuid_list,tenant_list,t,runtime):
    try:
        se_inventory_cache_start = time.time()
        #if runtime == True:
        if t in runtime:
            _runtime = True
            _rt = ',vs_refs,mgmt_vnic&join_subresources=runtime'
        else:
            _runtime = False
            _rt = ''
        se_inv = avi_request('serviceengine?fields=cloud_ref,tenant_ref,se_group_ref%s&page_size=200&include_name=true' %_rt,t)
        if se_inv.status_code == 403:
            print(str(datetime.now())+' =====> ERROR serviceengine_inventory_child: %s' %se_inv.text)
        else:
            se_inv = se_inv.json()
            resp = se_inv
            page_number = 1
            se_dict = {}
            while 'next' in resp:
                page_number += 1
                resp = avi_request('serviceengine?fields=cloud_ref,tenant_ref,se_group_ref%s&page_size=200&include_name=true&page='+str(page_number) %_rt,t).json()
                for v in resp['results']:
                    se_inv['results'].append(v)
            if se_inv['count'] > 0:
                for v in se_inv['results']:
                    if v['tenant_ref'].rsplit('#')[1] in tenant_list:
                        if v['cloud_ref'].rsplit('#')[1].lower() in cloud_list or '*' in cloud_list:
                            if v['uuid'] in uuid_list or '*' in uuid_list:
                                if v['uuid'] not in se_dict:
                                    se_dict[v['uuid']] = {}
                                    se_dict[v['uuid']]['name'] = v['name']
                                    se_dict[v['uuid']]['tenant'] = v['tenant_ref'].rsplit('#')[1]
                                    se_dict[v['uuid']]['cloud'] = v['cloud_ref'].rsplit('#')[1]
                                    se_dict[v['uuid']]['se_group'] = v['se_group_ref'].rsplit('#')[1]
                                    if _runtime == True:
                                        se_dict[v['uuid']]['runtime']={}
                                        if 'vs_refs' in v:
                                            se_dict[v['uuid']]['runtime']['virtualservice_count'] = len(v['vs_refs'])
                                        else:
                                            se_dict[v['uuid']]['runtime']['virtualservice_count'] = 0                                        
                                        if 'version' in v['runtime']:
                                            se_dict[v['uuid']]['runtime']['version'] = v['runtime']['version'].split(' ',1)[0]
                                        if 'se_connected' in v['runtime']:
                                            se_dict[v['uuid']]['runtime']['se_connected'] = v['runtime']['se_connected']
                                        if 'power_state' in v['runtime']:
                                            se_dict[v['uuid']]['runtime']['power_state'] = v['runtime']['power_state']
                                        if 'migrate_state' in v['runtime']:
                                            se_dict[v['uuid']]['runtime']['migrate_state'] = v['runtime']['migrate_state']
                                        if 'oper_status' in v['runtime']:
                                            se_dict[v['uuid']]['runtime']['oper_status'] = v['runtime']['oper_status']['state']
                                        if 'mgmt_vnic' in v:
                                            se_dict[v['uuid']]['runtime']['mgmt_ip'] = v['mgmt_vnic']['vnic_networks'][0]['ip']['ip_addr']['addr']
                                else:
                                    if v['tenant_ref'].rsplit('#')[1] == 'admin':
                                        se_dict[v['uuid']]['tenant'] = 'admin'
            r.set('temp_se_dict_'+t,pickle.dumps(se_dict))
            temp_total_time = str(time.time()-se_inventory_cache_start)
            print(str(datetime.now())+' =====> Refresh of SE Inventory Cache took %s seconds for tenant %s' %(temp_total_time,t))
    except:
        print(str(datetime.now())+' '+avi_controller+': func serviceengine_inventory_child encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)






def serviceengine_metrics_multiprocess(r,uuid_list,se_metric_list,tenant_list,runtime):
    try:        
        discovered_se = []
        metric_resp = []
        print(str(datetime.now())+' =====> Refreshing SE Static Metrics Cache')
        se_static_metric_cache_start = time.time()
        se_dict = pickle.loads(r.get('se_dict'))
        proc = []
        for t in tenant_list:
            p = Process(target = serviceengine_metrics_child, args = (r,uuid_list,se_metric_list,se_dict,t,))
            p.start()
            proc.append(p)
            if len(proc) > 10:
                for p in proc:
                    p.join()
                proc = []
        for p in proc:
            p.join()
        metric_keys = r.keys('temp_se_stat_*')
        for k in metric_keys:
            _1 = pickle.loads(r.get(k))
            metric_resp.append(_1['series']['collItemRequest:AllSEs'])
            r.delete(k)        
        #prom_metrics = ''
        prom_metrics = ['\n']
        se_metrics_runtime = pickle.loads(r.get('se_metrics_runtime'))
        for _resp in metric_resp:
            for s in _resp:
                if s in se_dict:
                    if s not in discovered_se:
                        discovered_se.append(s)
                        for m in _resp[s]:
                            if 'data' in m:
                                temp_tags = ''
                                metric_name = m['header']['name'].replace('.','_').replace('-','_')
                                metric_description = m['header']['metric_description']
                                metric_value = m['data'][0]['value']
                                temp_payload = {}
                                temp_payload['name'] = se_dict[s]['name']
                                temp_payload['uuid'] = s
                                temp_payload['cloud'] = se_dict[s]['cloud']
                                temp_payload['se_group'] = se_dict[s]['se_group']
                                temp_payload['tenant'] = m['header']['tenant_ref'].rsplit('#')[1]
                                temp_payload['entity_type'] = 'serviceengine'
                                for e in temp_payload:
                                    temp_tags=temp_tags+(str(e+'="'+temp_payload[e]+'",'))
                                temp_tags = '{'+temp_tags.rstrip(',')+'}'
                                #prom_metrics = prom_metrics+'\n'+'# HELP '+metric_name+' '+metric_description
                                #prom_metrics = prom_metrics+'\n'+'# TYPE '+metric_name+' gauge'
                                #prom_metrics = prom_metrics+'\n'+metric_name+''+temp_tags+' '+str(metric_value)
                                prom_metrics.append('%s 01# HELP %s %s' %(metric_name,metric_name, metric_description))
                                prom_metrics.append('%s 02# TYPE %s gauge' %(metric_name,metric_name))                                
                                prom_metrics.append('%s %s %s' %(metric_name,temp_tags,str(metric_value)))  
                        if 'runtime' in se_dict[s]:
                            for m in se_dict[s]['runtime']:
                                temp_payload = {}
                                temp_payload['name'] = se_dict[s]['name']
                                temp_payload['uuid'] = s
                                temp_payload['cloud'] = se_dict[s]['cloud']
                                temp_payload['se_group'] = se_dict[s]['se_group']
                                temp_payload['tenant'] = se_dict[s]['tenant']
                                temp_payload['entity_type'] = 'serviceengine'
                                se_metrics_runtime.append(m)
                                temp_tags = ''
                                if type(se_dict[s]['runtime'][m]) != int:
                                    temp_payload[m] = str(se_dict[s]['runtime'][m])
                                    int_value = False
                                else:
                                    int_value = True
                                for e in temp_payload:
                                    temp_tags=temp_tags+(str(e+'="'+temp_payload[e]+'",'))
                                temp_tags = '{'+temp_tags.rstrip(',')+'}'                            
                                prom_metrics.append('%s 01# HELP %s' %(m,m))
                                prom_metrics.append('%s 02# TYPE %s gauge' %(m,m))
                                if int_value == False:
                                    prom_metrics.append('%s %s %s' %(m,temp_tags,str(1)))
                                else:
                                    prom_metrics.append('%s %s %s' %(m,temp_tags,str(se_dict[s]['runtime'][m])))
                            ##----- return vscount for SE
                            #metric_name = 'vscount'
                            #metric_value = se_dict[s]['vscount']
                            #temp_payload = {}
                            #temp_payload['name'] = se_dict[s]['name']
                            #temp_payload['uuid'] = s
                            #temp_payload['cloud'] = se_dict[s]['cloud']
                            #temp_payload['se_group'] = se_dict[s]['se_group']
                            #temp_payload['tenant'] = se_dict[s]['tenant']
                            #temp_payload['entity_type'] = 'serviceengine'
                            #temp_tags = ''
                            #for e in temp_payload:
                            #    temp_tags=temp_tags+(str(e+'="'+temp_payload[e]+'",'))
                            #temp_tags = '{'+temp_tags.rstrip(',')+'}'                            
                            #prom_metrics.append('%s 01# HELP %s' %(m,m))
                            #prom_metrics.append('%s 02# TYPE %s gauge' %(m,m))                                
                            #prom_metrics.append('%s %s %s' %(metric_name,temp_tags,str(metric_value)))  
        se_metrics_runtime = list(set(se_metrics_runtime))                   
        r.set('se_metrics_runtime',pickle.dumps(se_metrics_runtime))
        #prom_metrics = prom_metrics+'\n'
        #se_metrics = prom_metrics
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
        _se_metrics = '\n'.join(prom_metrics)        
        r.set('se_polling', 'False')
        missing_metrics = []
        for _s in se_dict:
            if se_dict[_s]['name'] not in _se_metrics:
                _a = se_dict[_s]['tenant']+' : '+se_dict[_s]['name']
                missing_metrics.append(_s)
        r.set('se_missing_metrics', pickle.dumps(missing_metrics))
        r.set('se_metrics', pickle.dumps(prom_metrics))
        temp_total_time = str(time.time()-se_static_metric_cache_start)
        print(str(datetime.now())+' =====> Refresh of SE Metrics Cache took %s seconds' %temp_total_time)
    except:
        r.set('se_polling', 'False')
        print(str(datetime.now())+' : func serviceengine_metrics encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)





def serviceengine_metrics_child(r,uuid_list,se_metric_list,se_dict,t):
    try:
        se_static_metric_cache_start = time.time()
        if '*' in uuid_list:
            entity_uuid = '*'
        else:
            _temp_uuid_list = []
            for e in uuid_list:
                if se_dict[e]['tenant'] == t:
                    _temp_uuid_list.append(e)
            entity_uuid = ','.join(_temp_uuid_list)
        payload = {
            "metric_requests": [
                {
                    "step": 300,
                    "limit": 1,
                    "aggregate_entity": False,
                    "entity_uuid": entity_uuid,
                    "id": "collItemRequest:AllSEs",
                    "metric_id": se_metric_list
                }
                ]}
        se_stat = avi_post('analytics/metrics/collection?pad_missing_data=false&include_refs=true&include_name=true', t, payload).json()
        r.set('temp_se_stat_'+t,pickle.dumps(se_stat))
        temp_total_time = str(time.time()-se_static_metric_cache_start)
        print(str(datetime.now())+' =====> Refresh of SE Metrics Cache took %s seconds for tenant %s' %(temp_total_time,t))
    except:
        print(str(datetime.now())+' : func servicengine_metrics_child encountered an error for tenant: '+t)
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)








def refresh_serviceengine_metrics(r,avi_login,controller):
    try:
        global login
        login = avi_login
        global avi_controller
        avi_controller = controller
        r.set('se_last_poll_start_time', time.time())
        cloud_list = []
        _cloud_list = pickle.loads(r.get('se_cloud'))
        for c in _cloud_list:
            cloud_list.append(c)
        #---
        uuid_list = []
        _uuid_list = pickle.loads(r.get('se_entity_uuid'))
        if '*' in _uuid_list:
            uuid_list = '*'
        else:
            for u in _uuid_list:
                uuid_list.append(u)
        #---
        tenant_list = []
        _tenant_list = pickle.loads(r.get('se_tenant'))
        for t in _tenant_list:
            tenant_list.append(t)
        #---
        se_metric_list = []
        _se_metric_list = pickle.loads(r.get('se_metric_id'))
        for s in _se_metric_list:
            se_metric_list.append(s)
        se_metric_list = ','.join(se_metric_list)
        #---
        runtime = pickle.loads(r.get('se_runtime'))
        #---
        serviceengine_inventory_multiprocess(r,cloud_list,uuid_list,tenant_list,runtime)
        serviceengine_metrics_multiprocess(r,uuid_list,se_metric_list,tenant_list,runtime)        
        r.set('se_last_poll_time', time.time())
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)

