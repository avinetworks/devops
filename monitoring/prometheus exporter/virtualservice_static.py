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





def virtualservice_inventory_multiprocess(r,cloud_list,uuid_list,tenant_list):
    try:
        vs_inventory_cache_start = time.time()
        proc = []
        for t in tenant_list:
            p = Process(target = virtualservice_inventory_child, args = (r,cloud_list,uuid_list,tenant_list,t,))
            p.start()
            proc.append(p)
            if len(proc) > 10:
                for p in proc:
                    p.join()
                proc = []
        for p in proc:
            p.join()
        #----- get keys, consolidate then delete
        inv_keys = r.keys('temp_vs_dict_*')
        vs_dict = {}
        for k in inv_keys:
            _1 = pickle.loads(r.get(k))
            vs_dict.update(_1)
            r.delete(k)
        vs_results = {}
        vs_results['TOTAL_VIRTUALSERVICES'] = len(vs_dict)
        for v in vs_dict:
            if vs_dict[v]['tenant'] not in vs_results:
                vs_results[vs_dict[v]['tenant']] = 1
            else:
                vs_results[vs_dict[v]['tenant']] += 1
        r.set('vs_results', pickle.dumps(vs_results))
        r.set('vs_dict', pickle.dumps(vs_dict))
        temp_total_time = str(time.time()-vs_inventory_cache_start)
        print(str(datetime.now())+' =====> Refresh of VS Inventory Cache took %s seconds' %temp_total_time)
    except:
        print(str(datetime.now())+' : func virtualservice_inventory_multiprocess encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)





def virtualservice_inventory_child(r,cloud_list,uuid_list,tenant_list,t):
    try:
        vs_inventory_cache_start = time.time()
        vs_inv = avi_request('virtualservice?fields=cloud_ref,tenant_ref&page_size=200&include_name=true',t)
        if vs_inv.status_code == 403:
            print(str(datetime.now())+' =====> ERROR virtualservice_inventory_child: %s' %vs_inv.text)
        else:
            vs_inv = vs_inv.json()
            resp = vs_inv
            page_number = 1
            vs_dict = {}
            while 'next' in resp:
                page_number += 1
                resp = avi_request('virtualservice?fields=cloud_ref,tenant_ref&page_size=200&include_name=true&page='+str(page_number),t).json()
                for v in resp['results']:
                    vs_inv['results'].append(v)
            if vs_inv['count'] > 0:
                for v in vs_inv['results']:
                    if v['tenant_ref'].rsplit('#')[1] in tenant_list:
                        if v['cloud_ref'].rsplit('#')[1].lower() in cloud_list or '*' in cloud_list:
                            if v['uuid'] in uuid_list or '*' in uuid_list:
                                if v['uuid'] not in vs_dict:
                                    vs_dict[v['uuid']] = {}
                                    vs_dict[v['uuid']]['name'] = v['name']
                                    vs_dict[v['uuid']]['tenant'] = v['tenant_ref'].rsplit('#')[1]
                                    vs_dict[v['uuid']]['cloud'] = v['cloud_ref'].rsplit('#')[1]
                                else:
                                    if v['tenant_ref'].rsplit('#')[1] == 'admin':
                                        vs_dict[v['uuid']]['tenant'] = 'admin'
            r.set('temp_vs_dict_'+t,pickle.dumps(vs_dict))
            temp_total_time = str(time.time()-vs_inventory_cache_start)
            print(str(datetime.now())+' =====> Refresh of VS Inventory Cache took %s seconds for tenant %s' %(temp_total_time,t))
    except:
        print(str(datetime.now())+' : func virtualservice_inventory_child encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)






def virtualservice_metrics_multiprocess(r,uuid_list,vs_metric_list,tenant_list):
    try:        
        discovered_vs = []
        metric_resp = []
        print(str(datetime.now())+' =====> Refreshing Virtualservice Static Metrics Cache')
        vs_static_metric_cache_start = time.time()
        vs_dict = pickle.loads(r.get('vs_dict'))
        proc = []
        for t in tenant_list:
            p = Process(target = virtualservice_metrics_child, args = (r,uuid_list,vs_metric_list,vs_dict,t,))
            p.start()
            proc.append(p)
            if len(proc) > 9:
                for _p in proc:
                    _p.join()
                proc = []
        for p in proc:
            p.join()
        metric_keys = r.keys('temp_vs_stat_*')
        for k in metric_keys:
            try:
                _1 = pickle.loads(r.get(k))
                metric_resp.append(_1['series']['allvs'])
                r.delete(k)        
            except:
                print _1
        #prom_metrics = ''
        prom_metrics = ['\n']
        for _resp in metric_resp:
            for v in _resp:
                if v in vs_dict:
                    if v not in discovered_vs:
                        discovered_vs.append(v)
                        for m in _resp[v]:
                            if 'data' in m:
                                temp_tags = ''
                                metric_name = m['header']['name'].replace('.','_').replace('-','_')
                                metric_description = m['header']['metric_description']
                                metric_value = m['data'][0]['value']
                                temp_payload = {}
                                temp_payload['name'] = vs_dict[v]['name']
                                temp_payload['uuid'] = v
                                temp_payload['cloud'] = vs_dict[v]['cloud']
                                temp_payload['tenant'] = m['header']['tenant_ref'].rsplit('#')[1]
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
        #prom_metrics = prom_metrics+'\n'
        #vs_metrics = prom_metrics
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
        _vs_metrics = '\n'.join(prom_metrics)
        r.set('vs_polling', 'False')
        missing_metrics = []
        for _v in vs_dict:
            if vs_dict[_v]['name'] not in _vs_metrics:
                _a = vs_dict[_v]['tenant']+' : '+vs_dict[_v]['name']
                missing_metrics.append(_a)
        r.set('vs_missing_metrics', pickle.dumps(missing_metrics))
        #r.set('vs_metrics', pickle.dumps(vs_metrics))
        r.set('vs_metrics', pickle.dumps(prom_metrics))
        temp_total_time = str(time.time()-vs_static_metric_cache_start)
        print(str(datetime.now())+' =====> Refresh of VS Metrics Cache took %s seconds' %temp_total_time)
    except:
        r.set('vs_polling', 'False')
        print(str(datetime.now())+' : func virtualservice_metrics encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)





def virtualservice_metrics_child(r,uuid_list,vs_metric_list,vs_dict,t):
    try:
        vs_static_metric_cache_start = time.time()
        if '*' in uuid_list:
            entity_uuid = '*'
        else:
            _temp_uuid_list = []
            for e in uuid_list:
                if vs_dict[e]['tenant'] == t:
                    _temp_uuid_list.append(e)
            entity_uuid = ','.join(_temp_uuid_list)
        payload =  {
            'metric_requests': [
                {
                    'step' : 300, 
                    'limit': 1, 
                    'id': 'allvs', 
                    'entity_uuid' : entity_uuid, 
                    'metric_id': vs_metric_list
                }
                ]}
        vs_stat = avi_post('analytics/metrics/collection?pad_missing_data=false&include_refs=true&include_name=true', t, payload).json()
        r.set('temp_vs_stat_'+t,pickle.dumps(vs_stat))
        temp_total_time = str(time.time()-vs_static_metric_cache_start)
        print(str(datetime.now())+' =====> Refresh of VS Metrics Cache took %s seconds for tenant %s' %(temp_total_time,t))
    except:
        print(str(datetime.now())+' : func virtualservice_metrics_child encountered an error for tenant: '+t)
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)








def refresh_vs_metrics(r,avi_login,controller):
    try:
        global login
        login = avi_login
        global avi_controller
        avi_controller = controller
        r.set('vs_last_poll_start_time', time.time())
        #---
        cloud_list = []
        _cloud_list = pickle.loads(r.get('vs_cloud'))
        for c in _cloud_list:
            cloud_list.append(c)
        #---
        uuid_list = []
        _uuid_list = pickle.loads(r.get('vs_entity_uuid'))
        if '*' in _uuid_list:
            uuid_list = '*'
        else:
            for u in _uuid_list:
                uuid_list.append(u)
        #---
        tenant_list = []
        _tenant_list = pickle.loads(r.get('vs_tenant'))
        for t in _tenant_list:
            tenant_list.append(t)
        #---
        vs_metric_list = []
        _vs_metric_list = pickle.loads(r.get('vs_metric_id'))
        for v in _vs_metric_list:
            vs_metric_list.append(v)
        vs_metric_list = ','.join(vs_metric_list)
        #---
        virtualservice_inventory_multiprocess(r,cloud_list,uuid_list,tenant_list)
        virtualservice_metrics_multiprocess(r,uuid_list,vs_metric_list,tenant_list)
        r.set('vs_last_poll_time', time.time())
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)

