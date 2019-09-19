import json, requests, urllib3
from flask import Flask, request, jsonify
from datetime import datetime
import time
import traceback
import os
import redis
import cPickle as pickle
from multiprocessing import Process



if 'EN_WILDCARD_LIMIT' in os.environ:
    wildcard_limit = int(os.environ['EN_WILDCARD_LIMIT'])  
else:
    wilcard_limit = 10000



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



def update_servicediscovery_metric_cache_multiprocess(r,avi_login,controller,refresh_interval):
    try:
        sd_static_metric_cache_start = time.time()
        global login
        global avi_controller
        global metric_refresh_interval
        login = avi_login
        avi_controller= controller
        r.set('sd_last_poll_start_time', time.time())    
        metric_refresh_interval = refresh_interval
        r.set('targets_to_remove', pickle.dumps({}))               
        sd_names = pickle.loads(r.get('sd_names'))
        sd_targets = pickle.loads(r.get('sd_targets'))
        print(str(datetime.now())+' =====> Refreshing SD VS Metrics Cache')
        sd_metrics = []
        proc = []
        for tenant in sd_names:
            p = Process(target = update_servicediscovery_metric_cache_child, args = (r,tenant,sd_names,sd_targets,))
            p.start()
            proc.append(p)
        for p in proc:
            p.join()
        metric_keys = r.keys('temp_sd_stat_*')
        for k in metric_keys:
            _1 = pickle.loads(r.get(k))
            sd_metrics.append(_1['series']['allvs'])
            r.delete(k)  
        r.set('sd_metrics', pickle.dumps(sd_metrics),ex=(metric_refresh_interval*2))
        r.set('sd_polling', 'False')
        r.set('sd_last_poll_time', time.time())
        #----- remove stale targets from target lists
        targets_to_remove = pickle.loads(r.get('targets_to_remove'))
        if len(targets_to_remove) > 0:
            for t in targets_to_remove:
                for v in targets_to_remove[t]:
                    print(str(datetime.now())+' =====> Removing vs %s from target list' %v)
                    temp_uuid = sd_names[t][v]
                    sd_targets.pop(temp_uuid,None)
                    sd_names[t].pop(v,None)
            r.set('sd_names', pickle.dumps(sd_names))
            r.set('sd_targets', pickle.dumps(sd_targets))  
        temp_total_time = str(time.time()-sd_static_metric_cache_start)
        print(str(datetime.now())+' =====> Refresh of SD Metrics Cache took %s seconds' %temp_total_time)                    
    except:
        print(str(datetime.now())+' '+avi_controller+': func update_servicediscovery_metric_cache encountered an error')
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)





def update_servicediscovery_metric_cache_child(r,tenant,sd_names,sd_targets):
    try:
        sd_static_metric_cache_start = time.time()
        entity_uuid = []
        vs_metric_list = []
        targets_to_remove = pickle.loads(r.get('targets_to_remove'))
        for v in sd_names[tenant]:
            uuid = sd_names[tenant][v]
            #----- check to see if metrics for the service have been scraped in the 2 intervals
            #----- OR if no response for the UUID in last 2 intervals
            #----- add target to removal if not
            if time.time() - sd_targets[uuid]['lastquery'] > (metric_refresh_interval * 2) or time.time() - sd_targets[uuid]['lastresponse'] > (metric_refresh_interval * 2):
                if tenant not in targets_to_remove:
                    targets_to_remove[tenant] = {}
                targets_to_remove[tenant][v]=uuid
            else:
                entity_uuid.append(uuid)
                for m in sd_targets[uuid]['vs_metric_list']:
                    vs_metric_list.append(m)
        r.set('targets_to_remove',pickle.dumps(targets_to_remove))
        if len(entity_uuid) > wilcard_limit:
            entity_uuid = '*'
        else:
            entity_uuid = ','.join(entity_uuid)
        vs_metric_list = list(set(vs_metric_list))
        vs_metric_list = ','.join(vs_metric_list)
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
        vs_stat = avi_post('analytics/metrics/collection?pad_missing_data=false&include_refs=true&include_name=true', tenant, payload)
        if vs_stat.status_code == 403:
            print(str(datetime.now())+' =====> ERROR update_servicediscovery_metric_cache_child: %s' %vs_stat.text) 
        else:       
            #--- save to tenant object then combine
            r.set('temp_sd_stat_'+tenant,pickle.dumps(vs_stat.json()),ex=(metric_refresh_interval *2))
            #temp_metrics.append(vs_stat['series']['allvs'])
            temp_total_time = str(time.time()-sd_static_metric_cache_start)
            print(str(datetime.now())+' =====> Refresh of SD Metrics Cache took %s seconds for tenant %s' %(temp_total_time,tenant))
    except:
        print(str(datetime.now())+' '+avi_controller+': func update_servicediscovery_metric_cache_child for tenant %s encountered an error' %tenant)
        exception_text = traceback.format_exc()
        print(str(datetime.now())+' '+avi_controller+': '+exception_text)





#def refresh_servicediscovery_metrics(r,request,avi_login,controller):
#    try:
#        global login
#        login = avi_login
#        global avi_controller
#
#        avi_controller = controller
#        r.set('sd_last_poll_start_time', time.time())
#        update_servicediscovery_metric_cache_multiprocess(r,login,avi_controller)
#        r.set('sd_last_poll_time', time.time())
#    except:
#        exception_text = traceback.format_exc()
#        print(str(datetime.now())+' : '+exception_text)

