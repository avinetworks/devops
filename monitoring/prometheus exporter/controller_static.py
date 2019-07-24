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











def controller_metrics_multiprocess(r,controller_metric_list):
    try:        
        print(str(datetime.now())+' =====> Refreshing Controller Static Metrics Cache')
        ctl_static_metric_cache_start = time.time()
        cluster = avi_request('cluster','admin')
        if cluster.status_code == 403:
            print(str(datetime.now())+' =====> ERROR controller_metrics_multiprocess: %s' %cluster.text)
        else:
            cluster = cluster.json()
            cluster_nodes = {}
            proc = []
            for c in cluster['nodes']:
                cluster_nodes[c['vm_uuid']]=c['name']
                p = Process(target = controller_metrics_child, args = (r,controller_metric_list,c['vm_uuid'],))
                p.start()
                proc.append(p)
            for p in proc:
                p.join()
            _runtime = pickle.loads(r.get('ctl_runtime'))
            if 'true' in _runtime:
                runtime_metrics = controller_runtime_metrics()
            metric_keys = r.keys('temp_ctl_stat_*')
            metric_resp = []
            for k in metric_keys:
                try:
                    _1 = pickle.loads(r.get(k))
                    metric_resp.append(_1)
                    r.delete(k)        
                except:
                    print _1
            #prom_metrics = ''
            prom_metrics = ['\n']
            ctl_metrics_runtime = pickle.loads(r.get('ctl_metrics_runtime'))
            for n in metric_resp:
                node = cluster_nodes[n['entity_uuid']]
                for m in n['series']:
                    temp_tags = ''
                    metric_name = m['header']['name'].replace('.','_').replace('-','_')
                    metric_description = m['header']['metric_description']
                    metric_value = m['data'][0]['value']
                    temp_payload = {}
                    temp_payload['name'] = node
                    temp_payload['vm_uuid'] = n['entity_uuid']       
                    temp_payload['entity_type'] = 'controller'        
                    for e in temp_payload:
                        temp_tags=temp_tags+(str(e+'="'+temp_payload[e]+'",'))
                    temp_tags = '{'+temp_tags.rstrip(',')+'}'
                    #prom_metrics = prom_metrics+'\n'+'# HELP '+metric_name+' '+metric_description
                    #prom_metrics = prom_metrics+'\n'+'# TYPE '+metric_name+' gauge'
                    #prom_metrics = prom_metrics+'\n'+metric_name+''+temp_tags+' '+str(metric_value)
                    prom_metrics.append('%s 01# HELP %s %s' %(metric_name,metric_name, metric_description))
                    prom_metrics.append('%s 02# TYPE %s gauge' %(metric_name,metric_name))                         
                    prom_metrics.append('%s %s %s' %(metric_name,temp_tags,str(metric_value)))
            if 'true' in _runtime:
                for c in runtime_metrics:
                    if c == 'cloud_runtime':
                        for m in runtime_metrics[c]:
                            temp_tags = ''
                            metric_name = 'cloud_status'
                            metric_description = 'cloud_status'
                            metric_value = 1
                            temp_payload = {}
                            temp_payload['name'] = m
                            temp_payload['uuid'] = runtime_metrics[c][m]['config']['uuid'] 
                            temp_payload['vtype'] = runtime_metrics[c][m]['config']['vtype']
                            temp_payload['tenant'] = runtime_metrics[c][m]['config']['tenant'] 
                            temp_payload['entity_type'] = 'cloud'
                            temp_payload['cloud_status'] = runtime_metrics[c][m]['cloud_status']
                            ctl_metrics_runtime.append(metric_name)
                            for e in temp_payload:
                                temp_tags=temp_tags+(str(e+'="'+temp_payload[e]+'",'))
                            temp_tags = '{'+temp_tags.rstrip(',')+'}'                         
                            prom_metrics.append('%s 01# HELP %s' %(metric_name,metric_description))
                            prom_metrics.append('%s 02# TYPE %s gauge' %(metric_name,metric_description))
                            prom_metrics.append('%s %s %s' %(metric_name,temp_tags,str(1)))
                    else:
                        for _1 in cluster_nodes:
                            if cluster_nodes[_1] == c:
                                entity_uuid = _1
                        for m in runtime_metrics[c]:
                            temp_tags = ''
                            metric_name = m
                            metric_description = m
                            metric_value = 1
                            temp_payload = {}
                            temp_payload['name'] = c
                            temp_payload['vm_uuid'] = entity_uuid 
                            temp_payload['entity_type'] = 'controller'
                            ctl_metrics_runtime.append(m)
                            if type(runtime_metrics[c][m]) != int:
                                temp_payload[m] = (str(runtime_metrics[c][m])).lower()
                            for e in temp_payload:
                                temp_tags=temp_tags+(str(e+'="'+temp_payload[e]+'",'))
                            temp_tags = '{'+temp_tags.rstrip(',')+'}'                         
                            prom_metrics.append('%s 01# HELP %s' %(m,m))
                            prom_metrics.append('%s 02# TYPE %s gauge' %(m,m))
                            prom_metrics.append('%s %s %s' %(m,temp_tags,str(1)))
            ctl_metrics_runtime = list(set(ctl_metrics_runtime))                   
            r.set('ctl_metrics_runtime',pickle.dumps(ctl_metrics_runtime))
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
            #_ctl_metrics = '\n'.join(prom_metrics)
            r.set('ctl_polling', 'False')
            r.set('ctl_metrics',pickle.dumps(prom_metrics))
            temp_total_time = str(time.time()-ctl_static_metric_cache_start)
            print(str(datetime.now())+' =====> Refresh of Controller Metrics Cache took %s seconds' %temp_total_time)
    except:
        r.set('ctl_polling', 'False')
        print(str(datetime.now())+' : func controller_metrics encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)





def controller_metrics_child(r,controller_metric_list,vm_uuid):
    try:
        ctl_static_metric_cache_start = time.time()
        ctl_stat = avi_request('analytics/metrics/controller/%s/?metric_id=%s&limit=1&step=300&?aggregate_entity=False' %(vm_uuid,controller_metric_list),'admin').json()
        r.set('temp_ctl_stat_'+vm_uuid,pickle.dumps(ctl_stat))
        temp_total_time = str(time.time()-ctl_static_metric_cache_start)
        print(str(datetime.now())+' =====> Refresh of Controller Metrics Cache took %s seconds for uuid %s' %(temp_total_time,vm_uuid))
    except:
        print(str(datetime.now())+' : func controller_metrics_child encountered an error for uuid: '+vm_uuid)
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)





def controller_runtime_metrics():
    try:
        runtime_stats = {}
        #----- get list of tenants
        tenant_list = []
        ten_inv = avi_request('tenant?fields=name&page_size=200','admin')
        resp = ten_inv.json()
        page_number = 1
        while 'next' in resp:
            page_number += 1
            resp = avi_request('tenant?fields=name&page_size=200&page='+str(page_number),'admin').json()
            for v in resp['results']:
                ten_inv.json()['results'].append(v)
        for t in ten_inv.json()['results']:
            tenant_list.append(t['name'])
        #----- cluster runtime
        resp = avi_request('cluster/runtime','admin')
        if resp.status_code == 403:
            print(str(datetime.now())+' =====> ERROR controller_runtime_metrics: %s' %resp.text)
        else:
            if 'node_info' in resp.json():
                version = resp.json()['node_info']['version'].split(' ',1)[0]
            if 'node_states' in resp.json():
                for n in resp.json()['node_states']:
                    if n['name'] not in runtime_stats:
                        runtime_stats[n['name']] = {}
                    runtime_stats[n['name']]['cluster_role'] = n['role']
                    runtime_stats[n['name']]['cluster_state'] = n['state']
                    runtime_stats[n['name']]['version'] = version
        #----- cloud runtime
        for t in tenant_list:
            resp = avi_request('cloud-inventory?fields=status,vtype&include_name=true&page_size=200',t).json()['results']
            cloud_runtime_stats= {}
            for r in resp:
                if r['config']['name'] not in cloud_runtime_stats:
                    cloud_runtime_stats[r['config']['name']] = {'cloud_status': r['status']['state']}
                    cloud_runtime_stats[r['config']['name']]['config'] = {}
                cloud_runtime_stats[r['config']['name']]['config']['uuid'] = r['uuid']
                cloud_runtime_stats[r['config']['name']]['config']['vtype'] = r['config']['vtype']
                cloud_runtime_stats[r['config']['name']]['config']['tenant'] = r['mvrf']['tenant_ref'].split('#',1)[1]
        runtime_stats['cloud_runtime'] = cloud_runtime_stats
        #resp = avi_request('licenseusage', 'admin')
        #if resp.status_code == 403:
        #    print(str(datetime.now())+' =====> ERROR controller_runtime_metrics: %s' %resp.text)
        #else:
        return runtime_stats
    except:
        print(str(datetime.now())+' : func controller_runtime_metrics encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)


                        









def refresh_ctl_metrics(r,avi_login,controller):
    try:
        global login
        login = avi_login
        global avi_controller
        avi_controller = controller
        r.set('ctl_last_poll_start_time', time.time())
        #---
        controller_metric_list = []
        _controller_metric_list = pickle.loads(r.get('ctl_metric_id'))
        for c in _controller_metric_list:
            controller_metric_list.append(c)
        controller_metric_list = ','.join(controller_metric_list)
        controller_metrics_multiprocess(r,controller_metric_list)
        r.set('ctl_last_poll_time', time.time())
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' : '+exception_text)

