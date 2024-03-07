#!/usr/bin/env python
import os
import sys
import json
from time import gmtime, strftime
from api_endpoint import APIEndpoint
from sample_lib import (          #pylint: disable=import-error
    import_ssl_certificate, update_ssl_certificate, create_pki_profile, create_application_profile,
)


#----- There are 4 actions that will be receiving from Cloud Center
#----- 1.  START - create new VS, POOL, CERT/KEY
#----- 2.  STOP - delete VS, POOL, CERT/KEY
#----- 3.  UPDATE - update pool servers only
#----- 4.  MODIFY - apply configuration changes - NOT USED TODAY



def aci_app_name(parentJobName):
    split_list = parentJobName.split('run')
    if len(split_list) == 1:
        return None
    return (parentJobName.split('run')[0])



def validate_avi_params():
    try:
        global params
        with open('params.json', 'r') as p:
            params = json.loads(p.read())
    except Exception:
        print ('failed to load parmaters json!')
        sys.exit(0)
    print ('Avi Controller IP        : ' + params.get('aviControllerIp', ''))
    print ('Avi Controller User      : ' + params.get('aviControllerUserName', ''))
    print ('Avi Controller Password  : ' + params.get('aviPassword', ''))
    print ('Avi Tenant               : ' + params.get('aviTenantName', ''))
    print ('Avi App Name             : ' + params.get('vipName', ''))
    print ('Cliqr Launch User Id     : ' + params.get('launchUserId', ''))
    print ('Avi VIP                  : ' + params.get('vipIp', ''))
    print ('Avi VIP Port             : ' + params.get('vipPort', ''))
    print ('Avi SSL Enable           : ' + params.get('sslEnable', ''))
    if ('aviControllerIp' not in params or \
        'aviControllerUserName' not in params or \
        'aviPassword' not in params or \
        'aviTenantName' not in params or \
        'aviEcosystem' not in params or \
        'launchUserId' not in params or \
        'vipName' not in params or \
        'vipIp' not in params or \
        'vipPort' not in params or \
        'sslEnable' not in params):
        return False
    return True



def create_avi_endpoint():
    controller_ip = params.get('aviControllerIp', '')
    username = params.get('aviControllerUserName','')
    password = params.get('aviPassword', '')
    tenant = params.get('aviTenantName','')
    print ('Connecting to Avi Controller %s...'%(controller_ip))
    print ('User : %s Tenant : %s' %(username,tenant))
    return APIEndpoint(controller_ip,
                       username,
                       password, tenant=tenant)



def create_avi_pool(session, action):
    app_name = params['vipName']
    poolName = app_name + '-pool'
    poolServers = []
    for s in params['poolMembers']:
        for e in s:
            poolServers.append(e)
    hm_list = []
    if params['poolMonitor'] != '':
        hm_ref = session.get_object_uri('healthmonitor', params['poolMonitor'])
        hm_list.append(hm_ref)
    else:
        hm_ref = session.get_object_uri('healthmonitor', 'System-Ping')
        hm_list.append(hm_ref)
    listenPort = int(params['listenPort']) if params['listenPort'] != '' else int(params['vipPort'])
    if params['persistence'] == '' or params['persistence'].upper() == 'NONE':
        persistence_ref = ''
    else:
        persistence_ref = session.get_object_uri('applicationpersistenceprofile', params['persistence'])

    print 'Pool Name ' + poolName + ' Pool Servers : ' + ' '.join(poolServers) + ' Pool Port : ' + str(listenPort)
    servers_obj = []
    for server in poolServers:
        servers_obj.append({
            'ip' : {
                'addr' : server,
                'type' : 'V4'
            },
            'port' : listenPort
        })
    if action == 'MODIFY':
        pool_obj = session.get_object('pool', poolName)
        pool_obj.update({
            'name' : poolName,
            'servers' : servers_obj,
            'health_monitor_refs' : hm_list,
            'lb_algorithm' : 'LB_ALGORITHM_'+params['lbMethod'].upper().replace(' ','_'),
            'application_persistence_profile_ref' : persistence_ref
        })
    elif action == 'UPDATE':
        pool_obj = session.get_object('pool', poolName)
        pool_obj.update({
            'servers' : servers_obj
        })
    else:
        pool_obj = {
            'name' : poolName,
            'servers' : servers_obj,
            'health_monitor_refs' : hm_list,
            'lb_algorithm' : 'LB_ALGORITHM_'+params['lbMethod'].upper().replace(' ','_'),
            'application_persistence_profile_ref' : persistence_ref
        }
    session.create_or_update(obj='pool', obj_name=poolName,
                             data=pool_obj)



def print_external_service_result(contentObj):
    print 'CLIQR_EXTERNAL_SERVICE_RESULT_START'
    print json.dumps(contentObj)
    print 'CLIQR_EXTERNAL_SERVICE_RESULT_END'



def create_avi_virtualservice(session, app_profile_name, action):
    app_name = params['vipName']
    poolName = app_name + '-pool'
    vsName = params['vipName']
    vsVip = params['vipIp']
    vsPort = int(params['vipPort'])
    sslEnable = True if params['sslEnable'] == 'Yes' else False
    if app_profile_name != '':
        app_profile_ref = session.get_object_uri(
                            'applicationprofile',
                            app_profile_name)
    else:
        app_profile_ref = session.get_object_uri(
                            'applicationprofile',
                            'System-Http')
    print ('Creating VirtualService : %s...' %(vsName))
    pool_ref = session.get_object_uri('pool', poolName)
    service_objs = []
    service_objs.append({
        'port' : vsPort,
        'enable_ssl' : sslEnable
    })
    if action == 'MODIFY':
        vs_obj = session.get_object('virtualservice', vsName)
        vs_obj.update({
            'name' : vsName,
            'type' : 'VS_TYPE_NORMAL',
            'ip_address' : {
                'addr' : vsVip,
                'type' : 'V4'
            },
            'enabled' : True,
            'services' : service_objs,
            'pool_ref' : pool_ref,
            'application_profile_ref' : app_profile_ref,
            'description' : '%s - Virtual Service Modified by %s' \
                             %(strftime("%Y-%m-%d %H:%M:%S", gmtime()),\
                              params['launchUserId'])+'\n'+vs_obj['description']
        })
        if params['aviEcosystem'].upper() == 'AMAZON':
            vs_obj.pop('ip_address', None)
    else:
        vs_obj = None
        vs_obj = {
            'name' : vsName,
            'type' : 'VS_TYPE_NORMAL',
            'ip_address' : {
                'addr' : vsVip,
                'type' : 'V4'
            },
            'enabled' : True,
            'services' : service_objs,
            'pool_ref' : pool_ref,
            'application_profile_ref' : app_profile_ref,
            'description' : '%s - Virtual Service Created by %s' %(strftime("%Y-%m-%d %H:%M:%S", gmtime()), params['launchUserId'])
        }
        if params['aviEcosystem'].upper() == 'AMAZON':
            vs_obj.pop('ip_address', None)
            subnet_obj = session.get_object('cloud', 'Default-Cloud')['aws_configuration']['zones']
            for s in subnet_obj:
                if s['mgmt_network_name'] == params['vipIp']:
                    vs_obj['subnet_uuid'] = s['mgmt_network_uuid']
            vs_obj['auto_allocate_ip'] = True
            vs_obj['auto_allocate_floating_ip'] = True if params['aviAllocateFloatingIp'].upper() == 'YES' else False
            #vs_obj['auto_allocate_floating_ip'] = True
            vsVip = vs_obj['subnet_uuid']
    print_external_service_result({
        'ipAddress': vsVip,
        'hostName' : vsName,
        'environment': {
            'instanceType': 'VS_TYPE_NORMAL'
        }
    })
    if sslEnable == True:
        vs_obj['ssl_key_and_certificate_refs']  = [session.get_object_uri('sslkeyandcertificate', vsName)]
    session.create_or_update(obj='virtualservice',
                             obj_name=vsName,
                             data=vs_obj)




def delete_avi_virtualservice_pool(session):
    vsName = params['vipName']
    poolName = vsName + '-pool'
    print 'Deleting VS ' + vsName
    session.delete('virtualservice', vsName)
    print 'Deleting Pool ' + poolName
    session.delete('pool', poolName)
    if params['sslEnable'] == "Yes":
        print 'Deleting Cert/Key ' + vsName
        session.delete('sslkeyandcertificate', vsName)





#def execute_avi(action='START'):
def execute_avi(action):
    print 'in Avi Python Client'
    action_list = ['START','UPDATE', 'MODIFY', 'STOP']
    if action not in action_list:
        print 'Invalid Action Type "%s"; \r\nAvailable Options:  START, STOP, UPDATE, MODIFY' %action
        sys.exit(0)
    #---- DELETE print os.environ
    if (validate_avi_params() == False):
        print ('All Valid Parameters not present for Avi operation')
        sys.exit(0)

    # Establish session with the Avi Controller in 'admin' tenant for
    # configuration
    try :
        session = create_avi_endpoint()
    except Exception:
        print ('login failed to Avi Controller!')
        f = open('FAILURE', 'w')
        f.write('login failed to Avi Controller!')
        f.close()
        sys.exit(0)

    pathname = os.path.dirname(os.path.realpath(__file__))
    if action == 'START' or action == 'MODIFY':
        if params['sslEnable'] == "Yes":
            with open(pathname + '/server.crt') as f:
                server_crt = f.read()
            with open(pathname + '/server.key') as f:
                server_key = f.read()
            #with open(pathname + '/cakey.pem') as f:
            #    ca_key = f.read()
            #with open(pathname + '/cacert.pem') as f:
            #    ca_cert = f.read()
            #----- FIX THIS WITH A CLEANUP FUNCTION
            if action == 'START':
                try:
                    import_ssl_certificate(session, params['vipName'], server_key, server_crt)
                except:
                    ssl_obj = session.get_object('sslkeyandcertificate', params['vipName'])
                    update_ssl_certificate(session, params['vipName'], server_key, server_crt, ssl_obj['uuid'])
            else:
                try:
                    ssl_obj = session.get_object('sslkeyandcertificate', params['vipName'])
                    update_ssl_certificate(session, params['vipName'], server_key, server_crt, ssl_obj['uuid'])
                except:
                    import_ssl_certificate(session, params['vipName'], server_key, server_crt)
            #create_pki_profile(session, 'MyPKIProfile', certs=[ ca_cert ])
            #create_application_profile(session, 'MyAppProfile', 'MyPKIProfile')
        #else:
        #    create_application_profile(session, 'MyAppProfile', 'MyPKIProfile')
        # Vs/Pool are created in the context of the Tenant
        create_avi_pool(session,action)
        create_avi_virtualservice(session, params['appProfile'],action)
    elif action == 'UPDATE':
        create_avi_pool(session,action)
    elif action == 'STOP':
        delete_avi_virtualservice_pool(session)
    return
