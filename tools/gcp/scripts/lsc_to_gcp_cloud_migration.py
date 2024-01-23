#!/usr/bin/python
"""
This script clones the VirtualServices which are in LSC Cloud to GCP Cloud. 
This script currently clones the VirtualService one Cloud at a time.

Usage:
1) Export the full configuration from the old LSC Cloud Controller
2) If the config is of version < 18.2.5 then migrate the config to 18.2.5.
   Run these commands on a 18.2.5 controller to upgrade the config

    export DJANGO_SETTINGS_MODULE=portal.settings_full
    export PYTHONPATH=/opt/avi/python/lib:/opt/avi/python/bin/portal
    python /opt/avi/python/bin/upgrade/config_migrator.py --config-file old-config.json --output-file new-config.json

3) Create the GCP Cloud with the required configuration on the new 18.2.5 controller
4) Create Service Engine Groups for the GCP Cloud with the required configuration. 
   NOTE: The SE Group count and name should be same as that of the LSC Cloud SE Groups

5) Install the python requirements listed below on the machine where this script needs to run
6) Run the script passing the upgraded 18.2.5 config, the new controller details and the cloud names whose VS needs to be cloned.
    python lsc_to_gcp_cloud_migration.py --from-cloud old-lsc-cloud --to-cloud new-gcp-cloud --controller 10.152.134.15 \
        --password avi123$% --config-file new-config.json

pip-requirements:
networkx==2.2
avisdk==18.2.5
eventlet==0.25.1
ipaddress==1.0.22
urllib3==1.25.3
"""


import os
import sys
import copy
import json
import time
import urllib3
import logging
import networkx
import urlparse
import argparse
import eventlet
import threading
import ipaddress
from avi.sdk import avi_api


eventlet.monkey_patch()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)
lock = threading.Lock()
NEW_OBJECTS = {}
REF_MAP = {} # old ref - new ref
VIP_IPS = {} # network-id+subnet : set of vip ips


def setup_logging():
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('cloud_migration.log', 'w+')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    fh.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def resource_factory(rtype, config):
    cls_name = rtype.lower().title()
    if hasattr(sys.modules[__name__], cls_name):
        return getattr(sys.modules[__name__], cls_name)(config)
    return Resource(config)


def get_name_from_ref(ref):
    # /api/vsvip/?tenant=admin&name=vsvip-NOrudq&cloud=Default-Cloud
    parsed_ref = urlparse.urlparse(ref)
    if parsed_ref.query:  
        s = parsed_ref.path.split('/')
        params = dict(urlparse.parse_qsl(parsed_ref.query))
        return params['name']
    raise Exception("Failed to get name from ref %s" % ref)


class Resource(object):
    def __init__(self, config):
        self.priority = 100
        self.config = config
        self.failed = False
        self.scheduled = False

    def update_ref(self, ref, session, lsc_cloud_name, gcp_cloud_name):
        parsed_ref = urlparse.urlparse(ref)
        if not parsed_ref.query:
            # the ref is a uuid of old object . Get this from the cache
            if not parsed_ref.path in NEW_OBJECTS:
                raise Exception('Object %s not found in new created objects' % parsed_ref.path)
            return urlparse.urlparse(NEW_OBJECTS[parsed_ref.path]['url']).path

        # If ref is alredy resolved then return from cache
        if ref in REF_MAP:
            return REF_MAP[ref]

        # /api/vsvip/?tenant=admin&name=vsvip-NOrudq&cloud=Default-Cloud
        s = parsed_ref.path.split('/')
        params = dict(urlparse.parse_qsl(parsed_ref.query))
        # update the cloud ref
        if '/api/cloud/' in parsed_ref.path and params['name'] == lsc_cloud_name:
            params['name'] = gcp_cloud_name
            logger.debug("Updating cloud reference for %s", ref)
        if 'cloud' in params and params['cloud'] == lsc_cloud_name:
            params['cloud'] = gcp_cloud_name
            logger.debug("Updating cloud reference for %s", ref)

        headers = {"X-Avi-Version": "18.2.5"}
        if 'tenant' in params:
            headers["X-Avi-Tenant"] = params['tenant']
        if 'cloud' in params:
            headers["X-Avi-Cloud"] = params['cloud'] if params['cloud']!=lsc_cloud_name else gcp_cloud_name
 
        obj_type, obj_name = s[2], params['name']
        obj = session.get_object_by_name(obj_type, obj_name, headers=headers)
        if not obj:
            raise Exception("Cannot find %s %s " % (obj_type, obj_name))

        REF_MAP[ref] = obj['url']
        return obj['url']

    def _resolve_ref(self, key, value, session, lsc_cloud_name, gcp_cloud_name):
        if isinstance(value, dict):
            for k, v in copy.deepcopy(value).iteritems():
                value[k] = self._resolve_ref(k, v, session, lsc_cloud_name, gcp_cloud_name)
        elif isinstance(value, list):
            if key.endswith('_refs'):
                for i, v in enumerate(value):
                    value[i] = self._resolve_ref("_ref", v, session, lsc_cloud_name, gcp_cloud_name)
            for i, v in enumerate(value):
                value[i] = self._resolve_ref(key, v, session, lsc_cloud_name, gcp_cloud_name)
        elif isinstance(value, basestring):
            if key.endswith('_ref'):
                return self.update_ref(value, session, lsc_cloud_name, gcp_cloud_name)
        return value

    def _resolve_refs(self, session, config, lsc_cloud_name, gcp_cloud_name):
        new_config = copy.deepcopy(config)
        for key, value in config.iteritems():
            new_config[key] = self._resolve_ref(key, new_config[key], session, lsc_cloud_name, gcp_cloud_name)
        return new_config

    def pre_create_update_config(self, session):
        # update the config inplace
        pass

    def skip_create(self):
        # if this is set to true then the resource is not created
        return False

    def pre_resolve_update_config(self, session):
        # update the config inplace
        pass

    def create(self, session, lsc_cloud_name, gcp_cloud_name):
        if self.skip_create():
            logger.info("Skip creating resource %s", self._get_url())
            return

        cloud_name = None
        if 'cloud_ref' in self.config:
            cloud_name = get_name_from_ref(self.config.get('cloud_ref'))
            # change the cloud name to new cloud
            cloud_name = cloud_name if cloud_name != lsc_cloud_name else gcp_cloud_name

        tenant_name = None
        if 'tenant_ref' in self.config:
            tenant_name = get_name_from_ref(self.config.get('tenant_ref'))

        headers = {"X-Avi-Version": "18.2.5"}
        if tenant_name:
            headers["X-Avi-Tenant"] = tenant_name
        if cloud_name:
            headers["X-Avi-Cloud"] = cloud_name

        remove_fields = ["extension"]
        for field in remove_fields:
            if field in self.config:
                del self.config[field]
    
        obj_type = self._get_type()

        obj = session.get_object_by_name(obj_type, self.config['name'], headers=headers)
        if obj:
            logger.info("Resource %s already exits", self._get_url())
            # old config to new object
            parsed_ref = urlparse.urlparse(self._get_url())
            NEW_OBJECTS[parsed_ref.path] = obj
            return
        
        logger.info("Creating resource %s", self._get_url())

        # Update the config before resolving the references
        self.pre_resolve_update_config(session)
        # Resolve all the references to new objects created in controller
        self.config = self._resolve_refs(session, self.config, lsc_cloud_name, gcp_cloud_name)

        self.pre_create_update_config(session)

        resp = session.post(obj_type, data=self.config,  headers=headers)
        if resp.status_code not in [200, 201]:
            msg = "Failed to create %s : %s" % (self._get_url(), resp.text)
            raise Exception(msg)
        parsed_ref = urlparse.urlparse(self._get_url())
        NEW_OBJECTS[parsed_ref.path] = resp.json()

    def delete(self, session, lsc_cloud_name, gcp_cloud_name):
        cloud_name = None
        if 'cloud_ref' in self.config:
            cloud_name = get_name_from_ref(self.config.get('cloud_ref'))
            # change the cloud name to new cloud
            cloud_name = cloud_name if cloud_name != lsc_cloud_name else gcp_cloud_name

        tenant_name = None
        if 'tenant_ref' in self.config:
            tenant_name = get_name_from_ref(self.config.get('tenant_ref'))

        headers = {"X-Avi-Version": "18.2.5"}
        if tenant_name:
            headers["X-Avi-Tenant"] = tenant_name
        if cloud_name:
            headers["X-Avi-Cloud"] = cloud_name
        try:
            obj = session.get_object_by_name(self._get_type(), self.config['name'])
            if not obj:
                return
            path = obj['url'].split('/api/')[-1]

            logger.info("Deleting Resource %s", path)
            resp = session.delete(path)
        except avi_api.ObjectNotFound:
            logger.info("Resource %s not found", self._get_url())
            return
        except Exception as e:
            logger.error(e)
            raise

    def _get_url(self):
        if self.config.get('url'):
            return self.config['url']
        if self.config.get('uuid'):
            # There are some resource which does not have url in it. Create a url using the uuid.
            return '/api/%s/%s' % (self._get_type(), self.config['uuid'])
        raise Exception("Neither url nor uuid found for resource %s", self.config)

    def _get_type(self):
        if 'url' in self.config:
            # /api/virtualservice/virtualservice-19f62358-6986-41b4-af6a-ea4fca8ccced
            return self.config['url'].split('/')[2]
        if 'uuid' in self.config:
            # "virtualservice-19f62358-6986-41b4-af6a-ea4fca8ccced",
            return self.config['uuid'].split('-')[0]
        raise Exception("Cannot determine type of resource %s", self.config)

    def __hash__(self):
        return hash(self._get_url())

    def __eq__(self, other):
        return self._get_url() == other._get_url()

    def __str__(self):
        return self._get_url()

    def __repr__(self):
        return self._get_url()


class Ipamdnsproviderprofile(Resource):
    def __init__(self, config):
        super(Ipamdnsproviderprofile, self).__init__(config)

    def skip_create(self):
        return True


class Sslkeyandcertificate(Resource):
    def __init__(self, config):
        super(Sslkeyandcertificate, self).__init__(config)

    def skip_create(self):
        return True


class Cloudconnectoruser(Resource):
    def __init__(self, config):
        super(Cloudconnectoruser, self).__init__(config)

    def skip_create(self):
        return True


class Cloud(Resource):
    def __init__(self, config):
        super(Cloud, self).__init__(config)

    def skip_create(self):
        return True


class Virtualservice(Resource):
    def __init__(self, config):
        super(Virtualservice, self).__init__(config)

    def pre_resolve_update_config(self, session):
        # ISSUE: how to decryt a ssl certificate key?
        # config/4500398218428663088
        # Failed to create /api/sslkeyandcertificate/sslkeyandcertificate-60e26fdf-25e2-4d89-b2e9-2a814d3a250e
        # {"error": "Fail to decrypt string, wrong key"}
        if 'ssl_key_and_certificate_refs' in self.config:
            del self.config['ssl_key_and_certificate_refs']

        
        # ISSUE: enable_rhi is enabled in the Paypal setup in 17.2.11, but the must check if failing in 18.2.5
        # config/5697950030656498597
        # Failed to create /api/virtualservice/virtualservice-368802b2-378f-4818-bf17-fe86aa01aaa1
        # {"error": "Virtual Service advertisement is not allowed on public clouds."}
        if self.config.get('enable_rhi'):
            self.config['enable_rhi'] = False


class Pool(Resource):
    def __init__(self, config):
        super(Pool, self).__init__(config)

    def pre_resolve_update_config(self, session):
        # ISSUE: how to decryt a ssl certificate key?
        # config/4500398218428663088
        # Failed to create /api/sslkeyandcertificate/sslkeyandcertificate-60e26fdf-25e2-4d89-b2e9-2a814d3a250e
        # {"error": "Fail to decrypt string, wrong key"}
        if 'ssl_key_and_certificate_ref' in self.config:
            del self.config['ssl_key_and_certificate_ref']


        # ISSUE: Failing in must check
        # config/5697950030656498597
        # Failed to create /api/virtualservice/virtualservice-368802b2-378f-4818-bf17-fe86aa01aaa1
        # {"error": "Cannot enable Request Queuing for L4 Service pool"}
        if self.config.get('request_queue_enabled'):
            self.config['request_queue_enabled'] = False


        # ISSUE: need to see how to fix this must check
        # config/5697950030656498597
        # Failed to create /api/pool/pool-af332752-28e0-46a1-9f31-ed0bee120877
        # {"error": "Disable port translation is set in pool_gcmsdukeserv-vip.qa.paypal.com-14683. Healthmonitor System-TCP must specify a monitor port."}
        if self.config.get("use_service_port"):
            self.config["use_service_port"] = False


class Network(Resource):
    def __init__(self, config):
        super(Network, self).__init__(config)

    def pre_create_update_config(self, session):
        # Remove the subnet_runtime
        if "subnet_runtime" in self.config:
            del self.config["subnet_runtime"]


class Vsvip(Resource):
    def __init__(self, config):
        super(Vsvip, self).__init__(config)

    def pre_create_update_config(self, session):
        # This is the preserve the IP of the VS if the IP is allocated from IPAM
        vips = self.config.get('vip', [])
        for vip in vips:
            if vip['auto_allocate_ip']:
                with lock:
                    vip_ip = vip["ip_address"]["addr"]
                    # update the subnet range to the VIP IP
                    net_ref = vip["ipam_network_subnet"]["network_ref"]
                    result = session.get('network/%s' % net_ref.split('/')[-1])
                    if result.status_code not in [200, 201]:
                        raise Exception("Failed to get network %s: %s" % (net_ref, result.json()))
                    net = result.json()
                    logger.debug("Network Config : %s", net)
                    # Get the subnet in the network
                    subnet_index = -1
                    subnet_cidr = ""
                    for index, subnet in enumerate(net['configured_subnets']):
                        vip_subnet_prefix = vip['ipam_network_subnet']['subnet']['ip_addr']['addr']
                        vip_subnet_mask = vip['ipam_network_subnet']['subnet']['mask']
                        subnet_cidr = "%s/%s" % (vip_subnet_prefix, vip_subnet_mask)
                        if (vip_subnet_prefix == subnet['prefix']['ip_addr']['addr']  and
                            vip_subnet_mask == subnet['prefix']['mask']):
                            subnet_index = index
                            break

                    if subnet_index == -1:
                        raise Exception("Cannot find subnet with cidr '%s' in network %s" % (subnet_cidr, net_ref))

                    net_key = "%s/%s" % (net['uuid'], subnet_cidr)
                    static_ranges =  net['configured_subnets'][subnet_index]["static_ranges"]

                    # Filter out only ranges that are current VIPs
                    new_ranges = []
                    for range in static_ranges:
                        start = ipaddress.IPv4Address(unicode(range["begin"]["addr"]))
                        end = ipaddress.IPv4Address(unicode(range["end"]["addr"]))
                        if int(end) - int(start) == 0 and str(start) in VIP_IPS.get(net_key, []):
                            new_ranges.append(range)
                    
                    # add the vip range to it
                    new_ranges.append({"begin": {
                                            "type": "V4",
                                            "addr": vip_ip
                                            },
                                        "end": {
                                            "type": "V4",
                                            "addr": vip_ip
                                    }})
                    logger.info("Updating network %s with VIP %s", net['uuid'], vip_ip)
                    logger.debug("Updated Range: %s", new_ranges)
                    net['configured_subnets'][subnet_index]["static_ranges"] = new_ranges
                    resp = session.put("network/%s" % net['uuid'], data=net)
                    if resp.status_code not in [200, 201]:
                        logger.error("Update Failed: %s", resp.text)
                        raise Exception("Failed to update network %s", net['uuid'])

                    if net_key not in VIP_IPS:
                        VIP_IPS[net_key] = set()
                    VIP_IPS[net_key].add(vip_ip)


class Migrate(object):
    class Action:
        CREATE = "create"
        DELETE = "delete"
        VERIFY = "verify"

    def __init__(self, config, lsc_cloud, gcp_cloud, controller, username, password, action):
        self.config = config
        self.lsc_cloud_name = lsc_cloud
        self.gcp_cloud_name = gcp_cloud
        self.action = action
        self.session = avi_api.ApiSession.get_session(controller, username, password, api_version='18.2.5')

    def _get_object_by_name(self, obj_type, name):
        for k, v in self.config.iteritems():
            if k.lower() == obj_type:
                for obj in v:
                    if obj['name'] == name:
                        return obj
        raise Exception("Object Name %s of Type %s not found" % (name, obj_type))    

    def _get_object_by_uuid(self, obj_type, uuid):
        for k, v in self.config.iteritems():
            if k.lower() == obj_type:
                for obj in v:
                    if obj['uuid'] == uuid:
                        return obj
        raise Exception("Object UUID %s of Type %s not found" % (uuid, obj_type))    

    def _get_object_from_ref(self, ref):
        parsed_ref = urlparse.urlparse(ref)
        if parsed_ref.query:
            # /api/vsvip/?tenant=admin&name=vsvip-NOrudq&cloud=Default-Cloud
            s = parsed_ref.path.split('/')
            params = dict(urlparse.parse_qsl(parsed_ref.query))
            obj_type, obj_name = s[2], params['name']
            return obj_type, self._get_object_by_name(obj_type, obj_name)
        else:
            # /api/networkprofile/networkprofile-1ac8f694-b550-4901-b194-b62c67305fa4
            s = parsed_ref.path.split('/')
            if len(s) < 4:
                return None, None
            obj_type, obj_uuid = s[2], s[3]
            return obj_type, self._get_object_by_uuid(obj_type, obj_uuid)

    def recurse(self, key, value, graph, base_obj):
        def _add_ref(ref, graph, base_obj):
            obj_type, ref_config = self._get_object_from_ref(ref)
            if not ref_config:
                logger.info("Cannot get object of ref: %s %s", key, ref)
                return
            
            # update the refs with new cloud
            ref_obj = resource_factory(obj_type, ref_config)
            # if edge already exists in graph then ignore it
            if graph.has_edge(ref_obj, base_obj):
                return
            # obj requires the referenced object
            graph.add_edge(ref_obj, base_obj)
            # recursively set the referenced object dependency
            self.add_dependency(graph, ref_obj)

        if isinstance(value, dict):
            for k, v in value.iteritems():
                # ignore the extensions as they are runtime info
                if key == "extension":
                    continue
                self.recurse(k, v, graph, base_obj)
        elif isinstance(value, list):
            if key.endswith('_refs'):
                for v in value:
                    _add_ref(v, graph, base_obj)
            else:
                for v in value:
                    self.recurse(key, v, graph, base_obj)
        elif isinstance(value, basestring):
            if key.endswith('_ref'):
                _add_ref(value, graph, base_obj)

    def add_dependency(self, graph, obj):
        config = obj.config
        for k, v in config.iteritems():
            self.recurse(k, v, graph, obj)

    def create_graph(self, config):
        graph = networkx.DiGraph()
        # Create only VirtualService and its references
        t = 'VirtualService'
        #t = 'VsVip'
        vss = config.get(t, [])
        if not vss:
            logger.info("No virtualservice found in config. Nothing to do.")
            return graph

        for vs in vss:
            vs_obj = resource_factory(t.lower(), vs)
            self.add_dependency(graph, vs_obj)
        return graph
    
    def _get_all_vsvips(self):
        vsvips = []
        path = 'vsvip'
        while path:
            result = self.session.get(path).json()
            for v in result['results']:
                vsvips.append(v)
            path = result.get('next')
            path = path[path.find('vsvip'):] if path else False
        return vsvips

    def _populate_initial_data(self):
        vsvips = self._get_all_vsvips()
        for vsvip in vsvips:
            vips = vsvip.get('vip', [])
            for vip in vips:
                if vip['auto_allocate_ip']:
                    vip_ip = vip["ip_address"]["addr"]
                    net_ref = vip["ipam_network_subnet"]["network_ref"]
                    net_uuid = net_ref.split('/')[-1]

                    vip_subnet_prefix = vip['ipam_network_subnet']['subnet']['ip_addr']['addr']
                    vip_subnet_mask = vip['ipam_network_subnet']['subnet']['mask']
                    subnet_cidr = "%s/%s" % (vip_subnet_prefix, vip_subnet_mask)
                    net_key = "%s/%s" % (net_uuid, subnet_cidr)

                    if net_key not in VIP_IPS:
                        VIP_IPS[net_key] = set()
                    VIP_IPS[net_key].add(vip_ip)
        logger.debug("Initial VIPS: %s", VIP_IPS)

    def verify(self):
        config_vips = self.config.get('VsVip', [])
        vsvips = self._get_all_vsvips()

        avi_vips = {}
        for v in vsvips:
            avi_vips[v['name']] = v

        success = True
        for config_vip in config_vips:
            if config_vip['name'] not in avi_vips:
                logger.error("ERROR: vsvip '%s' not in avi", config_vip['name'])
                success = False
                continue
            avi_vip = avi_vips[config_vip['name']]
            cip = config_vip['vip'][0]['ip_address']['addr']
            aip = avi_vip['vip'][0]['ip_address']['addr']
            if cip != aip:
                logger.error("ERROR: vsvip '%s' IP Mismatch. Config has '%s' and Avi has '%s'", config_vip['name'], cip, aip)
                success = False
        
        if success:
            logger.info("All VIPs successfully verified!")
        else:
            logger.error("There were errors while verifying the VIPs")

    def migrate(self):
        if self.action == self.Action.VERIFY:
            self.verify()
            return

        # Create Graph of all the objects that are referenced by the virtualservices 
        # in the config
        graph = self.create_graph(self.config)
        # Remove the cycles
        remove_edges = [(Network, Ipamdnsproviderprofile)]
        while True:
            cycles = []
            try:
                cycles = networkx.find_cycle(graph, orientation='reverse')
            except networkx.exception.NetworkXNoCycle:
                break

            for edge in cycles:
                u, v = edge[0], edge[1]
                if (type(u), type(v)) in remove_edges:
                    graph.remove_edge(u, v)

        self._populate_initial_data()

        def create(node, lsc_cloud_name, gcp_cloud_name):
            try:
                node.create(self.session, lsc_cloud_name, gcp_cloud_name)
                return node
            except Exception as e:
                logger.error("Failed to create resource %s", node.config)
                raise
    
        def delete(node, lsc_cloud_name, gcp_cloud_name):
            node.delete(self.session, lsc_cloud_name, gcp_cloud_name)
            return node

        count = 0
        while True:
            nodes = networkx.topological_sort(graph)
            ready_nodes = []
            for node in nodes:
                if self.action == self.Action.CREATE:
                    if not graph.in_degree(node):
                        ready_nodes.append(node)
                else:
                    if not graph.out_degree(node):
                        ready_nodes.append(node)
            if not ready_nodes:
                break

            threads = []
            for i, node in enumerate(ready_nodes):
                count += 1
                if self.action == self.Action.CREATE:
                    NUM_THREADS = 50
                    t = eventlet.spawn(create, node, self.lsc_cloud_name, self.gcp_cloud_name)
                else:
                    NUM_THREADS = 100
                    t = eventlet.spawn(delete, node, self.lsc_cloud_name, self.gcp_cloud_name)
                threads.append(t)
                if len(threads) >= NUM_THREADS or i == len(ready_nodes) - 1:
                    # wait for all to complete
                    for t in threads:
                        node = t.wait()
                        graph.remove_node(node)
                    threads = []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-file', help="AVI Config file path", required=True)
    parser.add_argument('--from-cloud', help="LSC Cloud with GCP IPAM from which VS needs to be cloned", required=True)
    parser.add_argument('--to-cloud', help="New GCP Cloud Name", required=True)
    parser.add_argument('--controller', help="Hostname/IP-Address of the New Avi Controller", required=True)
    parser.add_argument('--username', help="Avi username", default="admin")
    parser.add_argument('--password', help="Avi user password", required=True)
    parser.add_argument('--action', help="Create/Delete/Verify Configuration", default=Migrate.Action.CREATE,
                        choices=(Migrate.Action.CREATE, Migrate.Action.DELETE, Migrate.Action.VERIFY))

    args = parser.parse_args()

    if not os.path.exists(args.config_file):
        raise Exception("Config file %s not found" % args.config_file)

    with open(args.config_file, 'r') as f:
        config = json.load(f)

    setup_logging()
    m = Migrate(config, args.from_cloud, args.to_cloud, args.controller, args.username, args.password, args.action)
    m.migrate()

if __name__ == '__main__':
    main()
