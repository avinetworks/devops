from api_endpoint import APIEndpoint, ObjectNotFound
import os

def import_ssl_certificate(sess, name, key, cert, key_passphrase=''):
    ssl_kc_obj = {
        'name' : name,
        'key' : key,
        'certificate' : cert,
        'key_passphrase' : key_passphrase,
        'self_signed' : False
    }
    return sess.execute_api(method='POST',
                            uri='api/sslkeyandcertificate/importkeyandcertificate',
                            data=ssl_kc_obj)



def update_ssl_certificate(sess, name, key, cert, uuid, key_passphrase=''):
    ssl_kc_obj = None
    ssl_kc_obj={
        'name' : name,
        'certificate' : {'certificate' : cert},
        'key' : key
    }
    return sess.execute_api(method='PUT',
                            uri='api/sslkeyandcertificate/%s/' %uuid,
                            data=ssl_kc_obj)



def create_pki_profile(sess, name, certs=[], crls=[]):
    cert_objs = []
    for cert in certs:
        cert_objs.append({
            'certificate' : cert
        })
    crl_objs = []
    for crl in crls:
        crl_objs.append({
            'body' : crl
        })
    pki_profile_obj = {
        'name' : name,
        'ca_certs' : cert_objs,
        'crls' : crl_objs
    }
    return sess.create_or_update(obj='pkiprofile', obj_name=name,
                                 data=pki_profile_obj)


def create_application_profile(sess, name, pki_profile_obj_name):
    '''
    Create a L7 application profile with caching, compression and
    websockets enabled.
    '''
    pki_profile_ref = sess.get_object_uri('pkiprofile', pki_profile_obj_name)
    application_profile_obj = {
        'name' : name,
        'type' : 'APPLICATION_PROFILE_TYPE_HTTP',
        'http_profile' : {
            'connection_multiplexing_enabled' : True,
            'compression_profile' : {
                'compression' : True,
                'remove_accept_encoding_header' : False,
                'type' : 'AUTO_COMPRESSION'
            },
            'cache_config': {
                'enabled' : True,
            },
            'websockets_enabled' : True,
            'ssl_client_certificate_mode': 'SSL_CLIENT_CERTIFICATE_REQUEST',
            'ssl_client_certificate_action' : {
                'headers': [
                     {
                         'request_header' : 'X-Cert',
                         'request_header_value' : 'HTTP_POLICY_VAR_SSL_CLIENT_SUBJECT'
                     }
                ],
                'close_connection' : True
            },
            'pki_profile_ref' : pki_profile_ref
        }
    }
    return sess.create_or_update(obj='applicationprofile', obj_name=name,
                                 data=application_profile_obj)

def create_or_update_content_switching_policy(sess, name, uris, pool_name,
                                              pool_data=''):
    '''
    Create a HTTP Request policy with a content switching rule to a pool
    '''
    pool_ref = sess.get_object_uri('pool', pool_name)
    match_str = []
    for uri in uris:
        match_str.append({'str' : '%s' % uri})
    switching_action = {
        'action' : 'HTTP_SWITCHING_SELECT_POOL'
    }
    http_policy_set_obj = {
        'name' : name,
        'http_request_policy' : {
            'rules': [
                {
                    'name'  : 'rule-1',
                    'index' : 1,
                    'enable' : True,
                    'match' : {
                        'path': {
                            'match_criteria' : 'BEGINS_WITH',
                            'match_str' : match_str
                        }
                    },
                    'switching_action' : {
                        'action' : 'HTTP_SWITCHING_SELECT_POOL',
                        'pool_ref' : pool_ref,
                        'pool_ref_data' : pool_data
                    }
                }
            ]
        }
    }
    return sess.create_or_update(obj='httppolicyset', obj_name=name,
                                 data=http_policy_set_obj)

def create_or_update_pool(sess, name, servers=[]):
    '''
    Create or Update a Pool with the given servers. Servers are assumed to be
    of the type <ip_address>:<port>. If port is not present, it is assumed to
    be a default of 80.
    '''
    servers_obj = []
    for server in servers:
        parts = server.split(':')
        ip_addr = parts[0]
        port = parts[1] if len(parts) == 2 else 80
        servers_obj.append({
            'ip' : {
                'addr' : ip_addr,
                'type' : 'V4'
            },
            'port' : port
        })
    pool_obj = {
        'name' : name,
        'servers' : servers_obj
    }
    return sess.create_or_update(obj='pool', obj_name=name,
                                 data=pool_obj)

def create_vs(sess, name, ip_addr, services=[],
              application_profile_name='System-HTTP'):
    application_profile_ref = sess.get_object_uri('applicationprofile', application_profile_name)
    service_objs = []
    for service in services:
        service_objs.append({
            'port' : service,
            'enable_ssl' : True
        })
    vs_obj = {
        'name' : name,
        'type' : 'VS_TYPE_NORMAL',
        'ip_address' : {
            'addr' : ip_addr,
            'type' : 'V4'
        },
        'enabled' : True,
        'services' : service_objs,
        'application_profile_ref' : application_profile_ref
    }
    return sess.create_or_update(obj='virtualservice', obj_name=name,
                                 data=vs_obj)

def create_vh_endpoint_vs(sess, name, ip_addr, services=[],
                          application_profile_name='System-HTTP'):
    application_profile_ref = sess.get_object_uri('applicationprofile', application_profile_name)
    service_objs = []
    for service in services:
        service_objs.append({
            'port' : service,
            'enable_ssl' : True
        })
    vs_obj = {
        'name' : name,
        'type' : 'VS_TYPE_VH_PARENT',
        'ip_address' : {
            'addr' : ip_addr,
            'type' : 'V4'
        },
        'enabled' : True,
        'services' : service_objs,
        'application_profile_ref' : application_profile_ref
    }
    return sess.create_or_update(obj='virtualservice', obj_name=name,
                                 data=vs_obj)


def create_vh_app_vs(sess, name, pool_name, vh_domain_name, vh_endpoint_name,
                     application_profile_name='System-HTTP'):
    application_profile_ref = sess.get_object_uri('applicationprofile', application_profile_name)
    pool_ref = sess.get_object_uri('pool', pool_name)
    vh_parent_vs_ref = sess.get_object_uri('virtualservice', vh_endpoint_name)
    vs_obj = {
        'name' : name,
        'type' : 'VS_TYPE_VH_CHILD',
        'vh_parent_vs_ref' : vh_parent_vs_ref,
        'vh_domain_name' : [
            vh_domain_name
        ],
        'pool_ref' : pool_ref,
        'application_profile_ref' : application_profile_ref
    }
    return sess.create_or_update(obj='virtualservice', obj_name=name,
                                 data=vs_obj)


def get_vs_metrics(sess, vs_name, **kwargs):
    '''
    @param sess: APIEndpoint object
    @param vs_name: Name of the VirtualService
    API gets the UUID of the virtualservice and perfoms GET on the metrics
    using options passed as kwargs.
    '''
    vs_ref = sess.get_object_uri('virtualservice', vs_name)
    print ' virtual service', vs_ref
    vs_uuid = vs_ref.split('/')[-1]
    return sess.get_metrics('virtualservice', vs_uuid, **kwargs)

def get_se_metrics(sess, se_name, **kwargs):
    '''
    @param sess: APIEndpoint object
    @param vs_name: Name of the VirtualService
    API gets the UUID of the virtualservice and perfoms GET on the metrics
    using options passed as kwargs.
    '''
    obj_uuid = ''
    if se_name:
        obj_ref = sess.get_object_uri('serviceengine', se_name)
        print ' service_engine ', obj_ref
        obj_uuid = obj_ref.split('/')[-1]
    return sess.get_metrics('serviceengine', obj_uuid, **kwargs)


def get_vs_anomalies(sess, vs_name, **kwargs):
    '''
    @param sess: APIEndpoint object
    @param vs_name: Name of the VirtualService
    API gets the UUID of the virtualservice and perfoms GET on the metrics
    using options passed as kwargs.
    '''
    vs_ref = sess.get_object_uri('virtualservice', vs_name)
    print ' virtual service', vs_ref
    vs_uuid = vs_ref.split('/')[-1]
    return sess.get_anomalies('virtualservice', vs_uuid, **kwargs)


def get_vs_healthscore(sess, vs_name, **kwargs):
    '''
    @param sess: APIEndpoint object
    @param vs_name: Name of the VirtualService
    API gets the UUID of the virtualservice and perfoms GET on the metrics
    using options passed as kwargs.
    '''
    vs_ref = sess.get_object_uri('virtualservice', vs_name)
    print ' virtual service', vs_ref
    vs_uuid = vs_ref.split('/')[-1]
    return sess.get_healthscore('virtualservice', vs_uuid, **kwargs)


def get_sample_ssl_params(path=''):
    '''
    returns the sample ssl params
    '''
    with open(path + 'certs/server.crt') as f:
        server_crt = f.read()
    with open(path + 'certs/server.key') as f:
        server_key = f.read()
    with open(path + 'certs/cakey.pem') as f:
        ca_key = f.read()
    with open(path + 'certs/cacert.pem') as f:
        ca_cert = f.read()
    return server_crt, server_key, ca_key, ca_cert
