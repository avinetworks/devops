'''
This script is to disable all VSs placed on SEs with no availability zones.
Prerequists:
1. Populate variables - AVI_CONTROLLER_IP, AVI_CONTROLLER_USER, AVI_CONTROLLER_PASSWORD, SE_CLOUD_NAME, SE_CLOUD_TENANT
2. Install avisdk using "pip install avisdk"

usage: python vs_disable.py
'''

try:
    from avi.sdk.avi_api import ApiSession
    import urllib3
    import requests
    import traceback
except ImportError as e:
    print 'Modules are missing %s'%str(e)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

AVI_CONTROLLER_IP       = '10.145.130.214' # ip:port
AVI_CONTROLLER_USER     = ''
AVI_CONTROLLER_PASSWORD = ''
SE_CLOUD_NAME           = 'Default-Cloud'
SE_CLOUD_TENANT         = 'admin'


class AviAzure(object):


    def __init__(self):

        self.controller_ip  = AVI_CONTROLLER_IP
        self.username       = AVI_CONTROLLER_USER
        self.password       = AVI_CONTROLLER_PASSWORD
        self.se_cloud_name  = SE_CLOUD_NAME
        self.se_cloud_tenant= SE_CLOUD_TENANT
        self.api            = None

        if not (self.controller_ip and self.username and self.username and self.password and
                self.se_cloud_name and self.se_cloud_tenant):
            print('One of the field is missing - AVI_CONTROLLER_IP, AVI_CONTROLLER_USER, '
                  'AVI_CONTROLLER_PASSWORD, SE_CLOUD_NAME, SE_CLOUD_TENANT')
            exit(1)
        self.is_connected()

    def is_connected(self):
        '''
        To check for successful authentication
        :return: True: Success or False: Failed
        '''
        self.api = ApiSession.get_session(self.controller_ip, self.username,
                                          self.password, tenant="*", api_version=self.get_version())

    def get(self, url, tenant=None):
        '''
        Request api call with GET method
        :param url: controller url
        :return:
        '''
        header_tenant = '*'
        if tenant:
            header_tenant = tenant

        rsp = self.api.get(url, tenant=header_tenant)
        if rsp.status_code!=200:
            raise Exception(rsp.text)
        return rsp.status_code, rsp.json()

    def put(self, url, data):
        '''
        Request api call with PUT method
        :param url: controller url
        :param data: API data to be posted
        :return:
        '''
        rsp = self.api.put(url, data=data, tenant='*')
        if rsp.status_code!=200:
            raise Exception(rsp.text)
        return rsp.status_code, rsp.json()

    def get_version(self):
        '''
        Get Controller Version
        :return:
        '''
        resp = requests.get('https://%s/api/initial-data' % self.controller_ip,
                            headers={
                                'Content-Type': 'application/json'
                            },
                            verify=False)
        if resp.status_code == 200:
            version = resp.json()['version']['Version']
            api_version = str(version)
            return api_version
        else:
            print resp.text
            print 'Error while getting controller version'

    def get_se_with_no_az(self, se_cloud_uuid):
        '''
        Get the list of SEs uuid with no Availability Zone
        :return:
        '''
        se_list = {}
        status, result = self.get('serviceengine?page_size=200')
        print 'SEs with no AZ:'
        for se in result['results']:
            cloud_ref = se['cloud_ref'].split('/')[-1]
            if cloud_ref == se_cloud_uuid and (not se.has_key('availability_zone') or not se['availability_zone']):
                se_list[se['uuid']] = se['name']
                print se['name']
        print '\n'
        return se_list

    def get_vs_placed_on_se(self, se_list, oshift_clouds_dict):
        '''
        Get Dict with vs_uuid as key and se_name as value
        :param se_list:
        :return:
        '''
        vs_list = {}
        status, result = self.get('virtualservice?page_size=200')
        result = result['results']
        for vs in result:
            cloud_ref = vs['cloud_ref'].split('/')[-1]
            if oshift_clouds_dict.has_key(cloud_ref) and vs['enabled']:
                for vip_runtime in vs['vip_runtime']:
                    if vip_runtime.has_key('se_list'):
                        for se in vip_runtime['se_list']:
                            se_uuid = se['se_ref'].split('/')[-1]
                            if se_list.has_key(se_uuid):
                                vs_key = "%s:%s"%(vs['name'], vs['uuid'])
                                if vs_list.has_key(vs_key):
                                    vs_list[vs_key].append(se_list['se_uuid'])
                                else:
                                    vs_list[vs_key] = [se_list[se_uuid]]
        return vs_list

    def disable_vs(self, vs):
        '''
        Disable VS.
        :param vs: vs uuid
        :param vs_list: dict with vs_uuid-se_names
        :return:
        '''
        try:
            vs_uuid = vs.split(':')[1]
            status, result = self.get('virtualservice/%s' % vs_uuid)
            result['enabled'] = False
            status, result = self.put('virtualservice/%s' % vs_uuid, result)
            print 'VS: %s got disabled'%(result['name'])
        except Exception as e:
            print 'Error while disabling VS %s: %s'%(vs_uuid, str(e))

    def get_all_OShift_clouds_with_azure_ipam(self):
        '''
        Get all cloud uuid:name dict, across all tenants
        :return:
        '''
        cloud_list = {}
        # returns clouds from across all tenants
        status, result = self.get('cloud')
        for cloud in result['results']:
            if cloud['vtype'] == 'CLOUD_OSHIFT_K8S' and cloud.has_key('ipam_provider_ref'):
                ipam_ref = cloud['ipam_provider_ref'].split('/')[-1]
                status, ipam_config = self.get('ipamdnsproviderprofile/%s'%ipam_ref)
                if ipam_config['type'] == 'IPAMDNS_TYPE_AZURE':
                    cloud_list[cloud['uuid']] = cloud['name']
        return cloud_list

    def get_se_cloud_uuid(self, se_cloud_name):
        '''
        Get SE uuid from Given Cloud Name where SEs belongs
        :param se_cloud_name:
        :return:
        '''
        # se_cloud_tenant is needed because, there can be multiple clouds names in different tenants
        status, result = self.get('cloud', tenant=self.se_cloud_tenant)
        for cloud in result['results']:
            if cloud['name'] == se_cloud_name:
                return cloud['uuid']
        raise Exception('Cloud %s does not exists'%se_cloud_name)

    def disable_all_vs(self):
        '''
        Disable all VSs placed on SEs with no availability zone
        :return:
        '''
        try:
            # get all openshift clouds with azure ipam configured
            oshift_clouds_dict = self.get_all_OShift_clouds_with_azure_ipam()
            se_cloud_uuid = self.get_se_cloud_uuid(self.se_cloud_name)
            # get all SEs belongs to given cloud name
            se_with_no_az_dict = self.get_se_with_no_az(se_cloud_uuid)
            # get all VSs placed on above SEs
            vs_list = self.get_vs_placed_on_se(se_with_no_az_dict, oshift_clouds_dict)
            for vs, se_name in vs_list.iteritems():
                vs_name = vs.split(':')[0]
                print "VS %s is placed on SE %s"%(vs_name, se_name)

            status = str(raw_input("Do you want to Disable all VSs, yes/no?\n"))
            if status.lower() == 'yes':
                # Disable all VSs
                for vs, se_name in vs_list.iteritems():
                    self.disable_vs(vs)
            print 'Script Completed.'
        except Exception as e:
            print 'Script Failed with Error %s'%str(e)
            traceback.print_exc()


if __name__ == '__main__':
    obj = AviAzure()
    obj.disable_all_vs()
