import socket
import requests
import json
import traceback
from datetime import datetime
import sys


#----- Send value to graphite
def send_value_graphite(endpoint_info, graphite_payload):
    try:
        message_list = []
        name_space_prefix = 'network-script||'
        for entry in graphite_payload:
            name_space = (name_space_prefix+entry['name_space']).replace('.','_').replace('||','.').replace(' ','_')
            message_list.append('%s %f %d' %(name_space, entry['metric_value'], entry['timestamp']))
            #----- I believe there is a message list limit on graphite for plain text
            if sys.getsizeof(message_list) > 4915:
                message = '\n'.join(message_list) + '\n'
                socket.setdefaulttimeout(10)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((endpoint_info['server'], endpoint_info['server_port']))
                sock.send(message)
                sock.close()
                message_list = []
        message = '\n'.join(message_list) + '\n'
        socket.setdefaulttimeout(10)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((endpoint_info['server'], endpoint_info['server_port']))
        sock.send(message)
        sock.close()

    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+'   '+exception_text)
        print message





#----- Send value to splunk HEC - destination a metric index
def send_value_splunk(endpoint_info, splunk_payload):
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
            resp = requests.post('%s://%s:%s/services/collector/event' %(endpoint_info['hec_protocol'], endpoint_info['server'], str(endpoint_info['hec_port'])) , verify=False, headers = headers, data=json.dumps(payload))
            if resp.status_code == 400:
                print payload
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+'   '+exception_text)
        print entry




#----- Send value to appdynamics
def send_value_appdynamics_machine(endpoint_info, appd_payload):
    try:
        for entry in appd_payload:
            name_space = entry['name_space'].replace('||','|')
            print('name=Custom Metrics|%s,value=%d,aggregator=OBSERVATION,time-rollup=CURRENT,cluster-rollup=INDIVIDUAL' % (name_space, long(entry['metric_value'])))
    except:
        exception_text = traceback.format_exc()
        print(str(datetime.now())+'   '+exception_text)




#----- this is to send to appdynamics machine agent http listener
def send_value_appdynamics_http(endpoint_info, appd_payload):
    try:
        payload = []
        for entry in appd_payload:
            name_space = entry['name_space'].replace('||','|')
            temp_payload = {}
            temp_payload['metricName'] = 'Custom Metrics|'+name_space
            temp_payload['aggregatorType'] = 'OBSERVATION'
            temp_payload['value'] = long(entry['metric_value'])
            payload.append(temp_payload)
        headers = ({'content-type': 'application/json'})
        resp = requests.post('http://%s:%s/api/v1/metrics' %(endpoint_info['server'],endpoint_info['server_port']),headers = headers, data=json.dumps(payload))
        if resp.status_code != 204:
            print resp
        #if resp.status_code != 202:
        #    print resp
    except:
        exception_text = traceback.format_exc()
        print exception_text




def send_value_influxdb(endpoint_info, influx_payload):
    try:
        tag_to_ignore = ['metric_name', 'timestamp', 'metric_value','name_space']
        metric_prefix = endpoint_info['metric_prefix']
        message_list = []
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
                resp = requests.post('%s://%s:%s/write?db=%s' %(endpoint_info['protocol'],endpoint_info['server'],endpoint_info['server_port'],endpoint_info['db']),verify=False,headers = headers, data=message)
                message_list = []
        message = '\n'.join(message_list) + '\n'
        headers = ({'content-type': 'octet-stream'})
        resp = requests.post('%s://%s:%s/write?db=%s' %(endpoint_info['protocol'],endpoint_info['server'],endpoint_info['server_port'],endpoint_info['db']),verify=False,headers = headers, data=message)
    except:
        exception_text = traceback.format_exc()
        print exception_text
            








def send_value_opentsdb(payload):
    pass





def send_value_prometheus(payload):
    pass





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
        resp = requests.post('https://%s%s' %(endpoint_info['api_url'],endpoint_info['api_key']), verify=False, headers = headers, data=json.dumps(payload))
        if resp.status_code != 202:
            print resp
    except:
        exception_text = traceback.format_exc()
        print exception_text






def send_value_elastic_stack(payload):
    pass





def send_metriclist_to_endpoint(endpoint_list, payload):
    try:
        for endpoint_info in endpoint_list:
            if endpoint_info['type'] == 'graphite':
                send_value_graphite(endpoint_info, payload)
            elif endpoint_info['type'] == 'splunk':
                send_value_splunk(endpoint_info, payload)
            elif endpoint_info['type'] == 'appdynamics_http':
                send_value_appdynamics_http(endpoint_info, payload)
            elif endpoint_info['type'] == 'appdynamics_machine':
                send_value_appdynamics_machine(endpoint_info, payload)
            elif endpoint_info['type'] == 'datadog':
                send_value_datadog(endpoint_info, payload)
            elif endpoint_info['type'] == 'influxdb':
                send_value_influxdb(endpoint_info, payload)
    except:
        exception_text = traceback.format_exc()
        print exception_text
