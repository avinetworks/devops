import json
import requests
requests.packages.urllib3.disable_warnings()
import logging
import os
import sys

logger = logging.getLogger('avisession')
#logger.setLevel(logging.DEBUG)
#ch = logging.StreamHandler(sys.stdout)
#ch.setLevel(logging.DEBUG)
#logger.addHandler(ch)

class ObjectNotFound(Exception):
    pass

class APIError(Exception):
    pass

class APIEndpoint(object):
    def __init__(self, controller_ip, username, password=None, token=None, tenant=None, batch=False):
        self.sess = requests.Session()
        self.controller_ip = controller_ip
        self.username = username
        self.password = password
        self.keystone_token = token
        self.tenant = tenant
        self.batch = batch

        if not controller_ip.startswith('http'):
            self.prefix = "https://%s" % controller_ip
        else:
            self.prefix = controller_ip
        self.authenticate_session()
        return

    def authenticate_session(self):
        body = {"username": self.username}
        if not self.keystone_token:
            body["password"] = self.password
        else:
            body["token"] = self.keystone_token
        rsp = self.sess.post(os.path.join(self.prefix, "login"), body,
                             timeout=5, verify=False)
        if rsp.status_code != 200:
            raise Exception("Authentication failed: %s", rsp.text)
        logger.debug("rsp cookies: %s", dict(rsp.cookies))
        self.sess.headers.update({
            "X-CSRFToken": dict(rsp.cookies)['csrftoken'],
            "Referer": self.prefix,
            "Content-Type" : "application/json"
        })
        # switch to a different tenant if needed
        if self.tenant:
            self.sess.headers.update({"X-Avi-Tenant": "%s" % self.tenant})
        logger.debug("sess headers: %s", self.sess.headers)
        return

    def _api(self, method, uri, params=None, data=None, headers=None,
             timeout=20):
        '''
        Internal routine to perform the API given the controller IP address,
        HTTP method, query parameters and REST API URI
        Returns the response.
        '''
        params = {} if not params else params
        headers = {} if not headers else headers
        data = {} if not data else data
        if uri.startswith('http') or uri.startswith('https'):
            full_uri = uri
        else:
            full_uri = os.path.join(self.prefix, uri)
        if headers:
            self.sess.headers.update(headers)
        logger.debug('%s %s data=%s', method, full_uri, data)
        acceptable_status_codes = []
        try:
            if method == 'GET':
                rsp = self.sess.get(full_uri, params=params,
                                    timeout=timeout, verify=False)
                acceptable_status_codes = [200]
            elif method == 'PUT':
                rsp = self.sess.put(full_uri, params=params,
                                    data=json.dumps(data),
                                    timeout=timeout, verify=False)
                acceptable_status_codes = [200, 201]
            elif method == 'POST':
                rsp = self.sess.post(full_uri, params=params,
                                     data=json.dumps(data),
                                     timeout=timeout, verify=False)
                acceptable_status_codes = [200, 201]
            elif method == 'DELETE':
                rsp = self.sess.delete(full_uri, params=params,
                                       data=json.dumps(data),
                                       timeout=timeout, verify=False)
                acceptable_status_codes = [200, 204]
            else:
                raise Exception('Unknown http request %s' % method)
        except requests.exceptions.Timeout:
            print 'Timeout in handling the request %s %s' % (method, full_uri)
            raise
        except requests.exceptions.ConnectionError as err:
            print 'Error in contacting the controller %s' % err
            raise

        if rsp.status_code not in acceptable_status_codes:
            raise APIError("Error in issuing API %s URI=%s DATA=%s Error:%s" %
                (method, uri, data, rsp.text))

        rsp_dict = json.loads(rsp.text) if rsp.text else {}
        return rsp_dict

    def get_object(self, obj, obj_name):
        '''
        Returns the contents of the object given the object and its name
        This performs a query for /api/<obj>?name=<obj_name> to get the contents
        Returns ObjectNotFound if there are no objects
        '''
        rsp = self._api('GET', 'api/%s?name=%s' % (obj, obj_name))
        if rsp['count'] == 0:
            if self.batch:
                # This is allowed as we are forward referencing the object in the
                # scope of execution
                return 'api/%s?name=%s' % (obj, obj_name)
            raise ObjectNotFound("No object for %s %s exists" % (obj, obj_name))
        elif rsp['count'] > 1:
            raise Exception("Multiple objects with the same name cannot exist in a given tenant")
        return rsp['results'][0]

    def get_object_uri(self, obj, obj_name):
        '''
        Returns the URI of the object given the object and its name
        This performs a query for /api/<obj>?name=<obj_name> to get the resource URI
        Returns ObjectNotFound if there are no objects
        '''
        rsp = self._api('GET', 'api/%s?name=%s' % (obj, obj_name))
        if rsp['count'] == 0:
            if self.batch:
                # This is allowed as we are forward referencing the object in the
                # scope of execution
                return 'api/%s?name=%s' % (obj, obj_name)
            raise ObjectNotFound("No object for %s %s exists" % (obj, obj_name))
        elif rsp['count'] > 1:
            raise Exception("Multiple objects with the same name cannot exist in a given tenant")
        return rsp['results'][0]['url']

    def get(self, obj, obj_name='', obj_uuid=''):
        '''
        Returns the object given the object and its name
        This performs a query for /api/<obj>?name=<obj_name> to get the resource
        Returns ObjectNotFound if there are no objects
        '''
        if obj_name:
            rsp = self._api('GET', 'api/%s?name=%s' % (obj, obj_name))
            if rsp['count'] == 0:
                return ObjectNotFound("No object for %s %s exists" % (obj, obj_name))
            elif rsp['count'] > 1:
                return Exception("Multiple objects with the same name cannot exist in a given tenant")
            return rsp['results'][0]
        elif obj_uuid:
            rsp = self._api('GET', 'api/%s/%s' % (obj, obj_uuid))
            return rsp
        return None

    def post(self, obj, obj_name='', obj_uuid='', action='', headers=None,
             data=None):
        headers = {} if not headers else headers
        data = {} if not data else data
        '''
        Returns the object given the object and its name
        This performs a query for /api/<obj>?name=<obj_name> to get the resource
        Returns ObjectNotFound if there are no objects
        '''
        if obj_name:
            rsp = self._api('POST', 'api/%s?name=%s' % (obj, obj_name),
                            headers=headers, data=data)
            if rsp['count'] == 0:
                return ObjectNotFound("No object for %s %s exists" % (obj,
                                                                      obj_name))
            elif rsp['count'] > 1:
                return Exception("Multiple objects with the same name cannot exist in a given tenant")
            return rsp['results'][0]
        elif obj_uuid:
            path = 'api/%s/%s' % (obj, obj_uuid)
            if action:
                path = path + '/' + action
            rsp = self._api('POST', path)
            return rsp
        return None

    def put(self, obj, obj_uuid='', action='', headers=None, data=None):
        '''
        Returns the object given the object and its name
        This performs a query for /api/<obj>?name=<obj_name> to get the resource
        Returns ObjectNotFound if there are no objects
        '''
        headers = {} if not headers else headers
        data = {} if not data else data
        rsp = self._api('PUT', 'api/%s/%s' % (obj, obj_uuid),
                        headers=headers, data=data)
        return rsp

    def get_collection(self, obj, **kwargs):
        path = 'api/%s?' % obj
        for k, v in kwargs.iteritems():
            path = path + '&' + k + '=' + v
        rsp = self._api('GET', path)
        return rsp

    def create_or_update(self, obj, obj_name, data):
        '''
        Create the object if it doesn't exist. Otherwise, update the object
        Assumes that we update the object with the given "data" dictionary.
        If you need to set specific parameters, you have to do a get, update the
        relevant parameters and then issue a create_or_update
        '''
        try:
            uri = self.get_object_uri(obj, obj_name)
            data['uuid'] = os.path.basename(uri)
            data['url'] = '/api/%s/%s' % (obj, data['uuid'])
            method = 'PUT'
        except ObjectNotFound:
            uri = 'api/%s' % obj
            method = 'POST'
        if not self.batch:
            return self._api(method=method, uri=uri, data=data)
        else:
            return data

    def delete(self, obj, obj_name):
        '''
        Delete the object if it exists. Not an error if it is already deleted
        '''
        try:
            uri = self.get_object_uri(obj, obj_name)
        except ObjectNotFound:
            return
        if not self.batch:
            self._api(method='DELETE', uri=uri)

    def create_or_update_batch(self, data):
        print json.dumps(data, indent=4)
        return self._api(method='PUT', uri='api/macro', data=data)

    def delete_batch(self, data):
        return self._api(method='DELETE', uri='api/macro', data=data)

    def execute_api(self, method, uri, params=None, data=None, headers=None):
        '''
        Execute the API directly.
        Allowed methods are ('POST', 'PUT', 'GET', 'DELETE')
        Primarily for cases like generate self-signed ssl certificate which is
        implemented as a POST of a specific action URI
        '''
        params = {} if not params else params
        headers = {} if not headers else headers
        data = {} if not data else data
        return self._api(method=method, uri=uri, params=params, data=data,
                         headers=headers)

    def generate_query_params(self, qdict):
        '''
        Converts the key value args dictionary into http query parameters.
        '''
        query_params = ''
        for k, v in qdict.items():
            query_params += '%s=%s&' % (k, v)
            # strip the last &
        query_params = query_params[:-1]
        return query_params

    def get_metrics(self, obj_type, obj_uuid, **kwargs):
        '''
        @param sess: APIEndpoint object
        @param obj_type: Type of object - virtualservice, serviceengine, pool,
                virtualmachine, host
        @param obj_uuid: uuid of the object.
        API perfoms GET on the metrics
        using options passed as kwargs.
        '''
        if obj_uuid:
            metrics_uri = 'api/analytics/metrics/%s/%s' % (obj_type, obj_uuid)
        else:
            # this is a collection API
            metrics_uri = 'api/analytics/metrics/%s' % (obj_type)
        metrics_params = self.generate_query_params(kwargs)
        return self.execute_api('GET', metrics_uri, params=metrics_params)

    def get_anomalies(self, obj_type, obj_uuid, **kwargs):
        '''
        @param self: APIEndpoint object
        @param obj_type: Type of object - virtualservice, serviceengine, pool,
                virtualmachine, host
        @param obj_uuid: uuid of the object.
        API perfoms GET on the metrics
        using options passed as kwargs.
        '''
        if obj_uuid:
            metrics_uri = 'api/analytics/anomaly/%s/%s' % (obj_type, obj_uuid)
        else:
            # this is a collection API
            metrics_uri = 'api/analytics/anomaly/%s' % (obj_type)
        metrics_params = self.generate_query_params(kwargs)
        return self.execute_api('GET', metrics_uri, params=metrics_params)

    def get_healthscore(self, obj_type, obj_uuid, **kwargs):
        '''
        @param self: APIEndpoint object
        @param obj_type: Type of object - virtualservice, serviceengine, pool,
                virtualmachine, host
        @param obj_uuid: uuid of the object.
        API perfoms GET on the metrics
        using options passed as kwargs.
        '''
        if obj_uuid:
            metrics_uri = 'api/analytics/healthscore/%s/%s' % (obj_type, obj_uuid)
        else:
            # this is a collection API
            metrics_uri = 'api/analytics/healthscore/%s' % (obj_type)
        metrics_params = self.generate_query_params(kwargs)
        return self.execute_api('GET', metrics_uri, params=metrics_params)
