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











def pool_inventory_multiprocess(r,cloud_list,uuid_list,tenant_list):
    try:
        pool_inventory_cache_start = time.time()
        pool_dict={}
        proc = []
        for t in tenant_list:
            p = Process(target = pool_inventory_child, args = (r,cloud_list,uuid_list,tenant_list,t,))
            p.start()
            proc.append(p)
            if len(proc) > 10:
                for p in proc:
                    p.join()
                proc = []
        for p in proc:
            p.join()
        #----- get keys, consolidate then delete
        inv_keys = r.keys('temp_pool_dict_*')
        pool_dict = {}
        for k in inv_keys:
            _1 = pickle.loads(r.get(k))
            pool_dict.update(_1)
            r.delete(k)
        pool_results = {}
        pool_results['TOTAL_POOLS'] = len(pool_dict)
        for p in pool_dict:
            if pool_dict[p]['tenant'] not in pool_results:
                pool_results[pool_dict[p]['tenant']] = 1
            else:
                pool_results[pool_dict[p]['tenant']] += 1
        r.set('pool_results', pickle.dumps(pool_results))
        r.set('pool_dict', pickle.dumps(pool_dict))
        temp_total_time = str(time.time()-pool_inventory_cache_start)
        print(str(datetime.now())+' =====> Refresh of Pool Inventory Cache took %s seconds' %temp_total_time)
    except:
        print(str(datetime.now())+' '+avi_controller+': func pool_inventory_multiprocess encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)





def pool_inventory_child(r,cloud_list,uuid_list,tenant_list,t):
    try:
        pool_inventory_cache_start = time.time()
        pool_inv = avi_request('pool?fields=cloud_ref,tenant_ref&page_size=200&include_name=true',t)
        if pool_inv.status_code == 403:
            print(str(datetime.now())+' =====> ERROR pool_inventory_child: %s' %pool_inv.text)
        else:
            pool_inv = pool_inv.json()
            resp = pool_inv
            page_number = 1
            pool_dict = {}
            while 'next' in resp:
                page_number += 1
                resp = avi_request('pool?fields=cloud_ref,tenant_ref&page_size=200&include_name=true&page='+str(page_number),t).json()
                for p in resp['results']:
                    pool_inv['results'].append(p)
            if pool_inv['count'] > 0:
                for p in pool_inv['results']:
                    if p['tenant_ref'].rsplit('#')[1] in tenant_list:
                        if p['cloud_ref'].rsplit('#')[1].lower() in cloud_list or '*' in cloud_list:
                            if p['uuid'] in uuid_list or '*' in uuid_list:
                                if p['uuid'] not in pool_dict:
                                    pool_dict[p['uuid']] = {}
                                    pool_dict[p['uuid']]['name'] = p['name']
                                    pool_dict[p['uuid']]['tenant'] = p['tenant_ref'].rsplit('#')[1]
                                    pool_dict[p['uuid']]['cloud'] = p['cloud_ref'].rsplit('#')[1]
                                else:
                                    if p['tenant_ref'].rsplit('#')[1] == 'admin':
                                        pool_dict[p['uuid']]['tenant'] = 'admin'
            r.set('temp_pool_dict_'+t,pickle.dumps(pool_dict))
            temp_total_time = str(time.time()-pool_inventory_cache_start)
            print(str(datetime.now())+' =====> Refresh of Pool Inventory Cache took %s seconds for tenant %s' %(temp_total_time,t))
    except:
        print(str(datetime.now())+' '+avi_controller+': func pool_inventory_child encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)




def pool_metrics_multiprocess(r,uuid_list,pool_metric_list,tenant_list):
    try:        
        discovered_servers = []
        metric_resp = []
        print(str(datetime.now())+' =====> Refreshing Pool Static Metrics Cache')
        pool_static_metric_cache_start = time.time()
        pool_dict = pickle.loads(r.get('pool_dict'))
        proc = []
        for t in tenant_list:
            p = Process(target = pool_metrics_child, args = (r,uuid_list,pool_metric_list,pool_dict,t,))
            p.start()
            proc.append(p)
            if len(proc) > 10:
                for p in proc:
                    p.join()
                proc = []
        for p in proc:
            p.join()
        metric_keys = r.keys('temp_pool_stat_*')
        for k in metric_keys:
            _1 = pickle.loads(r.get(k))
            metric_resp.append(_1['series']['collItemRequest:AllServers'])
            r.delete(k)
        #prom_metrics = ''
        prom_metrics = ['\n']
        for _resp in metric_resp:
            for p in _resp:
                if p.split(',')[1] in pool_dict:
                    if p not in discovered_servers:
                        discovered_servers.append(p)
                        for m in _resp[p]:
                            if 'data' in m:
                                temp_tags = ''
                                metric_name = m['header']['name'].replace('.','_').replace('-','_')
                                metric_description = m['header']['metric_description']
                                metric_value = m['data'][0]['value']
                                temp_payload = {}
                                temp_payload['name'] = pool_dict[p.split(',')[1]]['name']
                                temp_payload['uuid'] = p.split(',')[1]
                                temp_payload['server'] = p.split(',')[2]
                                temp_payload['cloud'] = pool_dict[p.split(',')[1]]['cloud']
                                temp_payload['tenant'] = m['header']['tenant_ref'].rsplit('#')[1]
                                temp_payload['entity_type'] = 'pool'
                                for e in temp_payload:
                                    temp_tags=temp_tags+(str(e+'="'+temp_payload[e]+'",'))
                                temp_tags = '{'+temp_tags.rstrip(',')+'}'
                                #prom_metrics = prom_metrics+'\n'+metric_name+''+temp_tags+' '+str(metric_value)
                                prom_metrics.append('%s 01# HELP %s %s' %(metric_name,metric_name, metric_description))
                                prom_metrics.append('%s 02# TYPE %s gauge' %(metric_name,metric_name))                                                
                                prom_metrics.append('%s %s %s' %(metric_name,temp_tags,str(metric_value)))                                       
        #prom_metrics = prom_metrics+'\n'
        #pool_metrics = prom_metrics
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
        _pool_metrics = '\n'.join(prom_metrics)        
        r.set('pool_polling', 'False')
        missing_metrics = []
        for _p in pool_dict:
            if pool_dict[_p]['name'] not in _pool_metrics:
                _a = pool_dict[_p]['tenant']+' : '+pool_dict[_p]['name']
                missing_metrics.append(_a)
        r.set('pool_missing_metrics', pickle.dumps(missing_metrics))
        #r.set('pool_metrics', pickle.dumps(pool_metrics))
        r.set('pool_metrics', pickle.dumps(prom_metrics))
        temp_total_time = str(time.time()-pool_static_metric_cache_start)
        print(str(datetime.now())+' =====> Refresh of Pool Metrics Cache took %s seconds' %temp_total_time)
    except:
        r.set('pool_polling', 'False')
        print(str(datetime.now())+' '+avi_controller+': func pool_metrics_multiprocess encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)
        return False





def pool_metrics_child(r,uuid_list,pool_metric_list,pool_dict,t):
    try:
        pool_static_metric_cache_start = time.time()
        if '*' in uuid_list:
            entity_uuid = '*'
        else:
            _temp_uuid_list = []
            for e in uuid_list:
                if pool_dict[e]['tenant'] == t:
                    _temp_uuid_list.append(e)
            entity_uuid = ','.join(_temp_uuid_list)
        payload = {
            "metric_requests": [
                {
                    "step": 300,
                    "limit": 1,
                    "aggregate_entity": False,
                    "entity_uuid": "*",
                    "obj_id": "*",
                    "pool_uuid": entity_uuid,
                    "id": "collItemRequest:AllServers",
                    "metric_id": pool_metric_list
                }
                ]}
        pool_stat = avi_post('analytics/metrics/collection?pad_missing_data=false&dimension_limit=1000&include_name=true&include_refs=true', t, payload).json()
        r.set('temp_pool_stat_'+t,pickle.dumps(pool_stat))
        temp_total_time = str(time.time()-pool_static_metric_cache_start)
        print(str(datetime.now())+' =====> Refresh of Pool Metrics Cache took %s seconds for tenant %s' %(temp_total_time,t))
    except:
        print(str(datetime.now())+' : func pool_metrics_child encountered an error for tenant: '+t)
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)






def refresh_pool_metrics(r,avi_login,controller):
    try:
        global login
        login = avi_login
        global avi_controller
        avi_controller = controller
        r.set('pool_last_poll_start_time', time.time())
        #---
        cloud_list = []
        _cloud_list = pickle.loads(r.get('pool_cloud'))
        for c in _cloud_list:
            cloud_list.append(c)
        #---
        uuid_list = []
        _uuid_list = pickle.loads(r.get('pool_entity_uuid'))
        if '*' in _uuid_list:
            uuid_list = '*'
        else:
            for u in _uuid_list:
                uuid_list.append(u)
        #---
        tenant_list = []
        _tenant_list = pickle.loads(r.get('pool_tenant'))
        for t in _tenant_list:
            tenant_list.append(t)
        #---
        pool_metric_list = []
        _pool_metric_list = pickle.loads(r.get('pool_metric_id'))
        for p in _pool_metric_list:
            pool_metric_list.append(p)
        pool_metric_list = ','.join(pool_metric_list)
        #---
        pool_inventory_multiprocess(r,cloud_list,uuid_list,tenant_list)
        pool_metrics_multiprocess(r,uuid_list,pool_metric_list,tenant_list)
        r.set('pool_last_poll_time', time.time())
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)

