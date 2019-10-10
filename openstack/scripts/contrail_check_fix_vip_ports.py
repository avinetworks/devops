#!/usr/bin/env python

import argparse
import traceback
import sys
#sys.path.append('/opt/avi/python/bin/cloud_connector')

import logging
import avi.util.openstack_utils as osutils
import lib.cloud_connector_constants as const
import lib.cloud_connector_utils as cc_utils
import neutronclient.neutron.client as nnclient
import novaclient.client as nvclient
from novaclient import extension
from novaclient.v2.contrib import list_extensions

from avi.infrastructure import datastore
from avi.util.net_util import verify_connectivity
from avi.util.openstack_utils import ks_ip_port
from avi.util.os_utils2 import ks_clients
from openstack import jvnc_client as contrailc


root = logging.getLogger()
root.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh = logging.FileHandler('contrail_check_fix_vip_ports.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
root.addHandler(fh)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.ERROR)
ch.setFormatter(formatter)
root.addHandler(ch)

log = logging.getLogger()
ds = datastore.Datastore()

ENDPOINTS = ['compute', 'network', 'image', 'identity']

VNCJ_DEFAULT_HEADERS = {
    'Content-type': 'application/json; charset="UTF-8"',
    'X-Contrail-Useragent': 'avi-controller',
}

secache = {}

def get_endpoints(tksc, service=None, eptype=None, region=None):
    aref = tksc.session.auth.auth_ref
    eps = aref.service_catalog.get_endpoints(service_type=service,
                                             region_name=region,
                                             endpoint_type=eptype)
    return eps


def os_try_access(username, password, tenant, ip, timeout=5,
                  region=None, auth_url=None, log=None):
    (kip, kport, auth_url) = ks_ip_port(ip, auth_url=auth_url)
    rc, msg = verify_connectivity(kip, kport)
    if not rc:
        return (None, msg)

    skwopts = {'timeout': 60, 'verify': False}
    ckwopts = {'connect_retries': const.CONNECT_RETRIES,
               'region_name': region}
    try:
        rc, uksc, tksc = ks_clients(auth_url, username, password,
                                    pd_name=tenant, skwopts=skwopts,
                                    ckwopts=ckwopts, logger=log)
        eps = get_endpoints(tksc, eptype='public', region=region)
        for ep in ENDPOINTS:
            if not eps.get(ep):
                msg = ('Endpoint for %s not found in region %s (possibly bad region)' % (ep, region))
                return (None, msg)
    except Exception as e:
        msg = str(e)
        return (None, msg)

    return (tksc, 'Success')


def fetch_oscfg(cloud_uuid=None, cloud_name=None):
    if cloud_uuid:
        cloud = ds.get('cloud', cloud_uuid)
        return cloud_uuid, cloud['config'].openstack_configuration
    elif cloud_name:
        clouds = ds.get_all('cloud')
        for c in clouds:
            if c.get('config') and c['config'].name == cloud_name:
                return c['uuid'], c['config'].openstack_configuration
    else:
        clouds = ds.get_all('cloud')
        for c in clouds:
            if c.get('config') and c['config'].HasField('openstack_configuration'):
                return c['uuid'], c['config'].openstack_configuration


def get_cls(tname, auth_url, oscfg):
    ksc, err = os_try_access(oscfg.username, oscfg.password,
                             tname, oscfg.keystone_host,
                             const.REQUEST_TIMEOUT, oscfg.region,
                             auth_url=auth_url, log=log)
    if not ksc:
        log.error("Cloudn't establish connection to OpenStack, error: %s", err)
        sys.exit(1)
    eptype = 'internal' if oscfg.use_internal_endpoints else 'public'
    ckwopts = {'connect_retries': const.CONNECT_RETRIES,
               'region_name': oscfg.region, 'interface': eptype}
    neuc = nnclient.Client('2', session=ksc.session,
                            retries=const.API_RETRIES, **ckwopts)
    extns = [extension.Extension('list_extensions', list_extensions)]
    novc = nvclient.Client('2.15', session=ksc.session, extensions=extns, **ckwopts)
    return ksc, neuc, novc


def get_clients(oscfg):
    (_, _, auth_url) = osutils.ks_ip_port(oscfg.keystone_host,
                                          auth_url=oscfg.auth_url)
    return get_cls(oscfg.admin_tenant, auth_url, oscfg)


def fix_vip_ports(selist, novc, neuc, jnc, vscfg, ip, pid, nwid):
    error = False
    dportid = None
    f = False
    for se in selist:
        if se.is_standby:
            continue
        if se.is_primary or vscfg.scaleout_ecmp:
            sevmid = cc_utils.cc_uuid(se.se_uuid)
        if secache.get(sevmid):
            for port_id, aaps in secache[sevmid]['aaps'].iteritems():
                if ip in aaps:
                    log.error('IP %s found as primary for port %s', ip, port_id)
                    error = True
                    break
            if error:
                break
            for port_id, fixips in secache[sevmid]['fixips'].iteritems():
                if ip in fixips:
                    f = True
                    dportid = port_id
                    break
            if f:
                break
        else:
            try:
                vm = novc.servers.get(sevmid)
            except:
                log.error('No server present with id: %s', sevmid)
                vm = None
            if vm:
                for j in vm.interface_list():
                    try:
                        sport = neuc.show_port(j.port_id)['port']
                        if sevmid not in secache:
                            secache[sevmid] = {'fixips': {}, 'aaps': {}}
                        secache[sevmid]['fixips'].update({sport['id']: [a['ip_address'] for a in sport.get('fixed_ips', [])]})
                        secache[sevmid]['aaps'].update({sport['id']: [a['ip_address'] for a in sport.get('allowed_address_pairs', [])]})
                        for ips in sport.get('allowed_address_pairs', []):
                            if ips['ip_address'] == ip:
                                log.error('IP %s found as primary for port %s', ip, sport['id'])
                                error = True
                                break
                        if error:
                            break
                        for  k in sport.get('fixed_ips', []):
                            if ip == k['ip_address']:
                                f = True
                                dportid = sport['id']
                                break
                        if f:
                            break
                    except:
                        log.error('No data port with port id %s is present', j.port_id)
            if error or f:
                break
    if dportid and f:
        try:
            spvmi, piip, _ = jnc._vnc_get_vmi_iip(dportid, ip)
            vpvmi, _, _ = jnc._vnc_get_vmi_iip(pid)
            if piip:
                jnc._update_vmi_ref(piip, [spvmi], None, dvmis=[spvmi,vpvmi])
                jnc._vnc_put_iip(piip, None)
                print 'Fixed vip port for VS {}'.format(vscfg.name)
        except Exception as e:
            log.error('Error during fix: %s', traceback.format_exc())
            print 'Failed to fix the vip port for VS {}: {}'.format(vscfg.name, e)
            print 'Failure in detail: {}'.format(traceback.format_exc())
    elif not error:
        print 'No SE found with data port having ip {} for VS {}. Creating dummy port'.format(ip, vscfg.name)
        log.info('Creating dummy port with ip %s as fixedip', ip)
        try:
            pdata = {'name': 'dummy-vip-{}-port'.format(ip), 'network_id': nwid, 'fixed_ips': [{'ip_address' : ip}]}
            dummy_port = neuc.create_port({'port': pdata})['port']
        except Exception as e:
            log.error('Failed to create dummy port with ip %s: %s', ip, traceback.format_exc())
            print 'Failed to create dummy port with ip {}: {}'.format(ip, e)
            print 'Failure in detail: {}'.format(traceback.format_exc())
            print 'Failed to fix the vip port for VS {}'.format(vscfg.name)
        else:
            try:
                spvmi, piip, _ = jnc._vnc_get_vmi_iip(dummy_port['id'], ip)
                vpvmi, _, _ = jnc._vnc_get_vmi_iip(pid)
                if piip:
                    jnc._update_vmi_ref(piip, [spvmi], None, dvmis=[spvmi,vpvmi])
                    jnc._vnc_put_iip(piip, None)
                    print 'Fixed vip port for VS {}. Please disable and enable the VS'.format(vscfg.name)
            except Exception as e:
                log.error('Error during fix: %s', traceback.format_exc())
                print 'Failed to fix the vip port for VS {}: {}'.format(vscfg.name, e)
                print 'Failure in detail: {}'.format(traceback.format_exc())
            else:
                log.info('Deleting dummy port with id %s', dummy_port['id'])
                try:
                    neuc.delete_port(dummy_port['id'])
                except:
                    log.error('Error during dummy port delete: %s', traceback.format_exc())
                    print 'Error during dummy port delete, please check the log for more info and delete the port manually'

def check_vip_ports(args):
    def check(ip, neuc, novc, jnc, vs, pid, nwid):
        try:
            port = neuc.show_port(pid)['port']
        except:
            log.error('Error in getting port: %s', traceback.format_exc())
            port = None
        if port:
            found = False
            for i in port.get('fixed_ips', []):
                if ip == i['ip_address']:
                    found = True
                    break
            if not found:
                print 'VS {} IP {} not found on port {}'.format(vs['config'].name, ip, pid)
                if args.fix:
                    se_list = vs['runtime'].vip_runtime[0].se_list
                    fix_vip_ports(se_list, novc, neuc, jnc, vs['config'], ip, pid, nwid)
            else:
                print 'found VS {} IP {} on port {}'.format(vs['config'].name, ip, pid)

            existing_pairs = [pair['ip_address'][:pair['ip_address'].rfind('/')] if '/' in pair['ip_address'] else pair['ip_address'] for pair in port.get('allowed_address_pairs', [])]
            if ip not in existing_pairs:
                print 'VS {} IP {} not found in allowed address pairs of port {}'.format(vs['config'].name, ip, pid)
                if args.fix:
                    pairs = port.get('allowed_address_pairs', [])
                    pairs.append({'ip_address' : ip})
                    body = {'port': {'allowed_address_pairs': pairs}}
                    try:
                        neuc.update_port(port=pid, body=body)
                        print 'Fixed allowed address pairs entry for port {} wrt VS {} IP {}'.format(pid, vs['config'].name, ip)
                    except:
                        log.error('Error during ip %s updation to aap: %s', ip, traceback.format_exc())
            else:
                print 'found VS {} IP {} in allowed address pairs of port {}'.format(vs['config'].name, ip, pid)
        else:
            print 'VS {} IP {} port not found'.format(vs['config'].name, ip)

    cloud_uuid, oscfg = fetch_oscfg(cloud_uuid=args.cloud_uuid, cloud_name=args.cloud_name)
    if not oscfg:
        log.error("OpenStack Configuration not found!")
        sys.exit(1)
    try:
        ksc, neuc, novc = get_clients(oscfg)
        jnc = contrailc.JVncConf(ksc, oscfg.contrail_endpoint, log=log)
        jnc.session.headers.update(VNCJ_DEFAULT_HEADERS)
    except:
        log.error('Clients not initialised : %s', traceback.format_exc())
        sys.exit(1)

    if args.vs_uuid:
        vs_list = [ds.get('virtualservice', args.vs_uuid)]
    else:
        vs_list = ds.get_all('virtualservice')
    for vs in vs_list:
        if vs.get('config') and vs['config'].cloud_uuid == cloud_uuid and vs['config'].vip:
            for vip in vs['config'].vip:
                if not (vip.ip_address and vip.ip_address.addr) and not (vip.ip6_address and vip.ip6_address.addr):
                    continue
                if vip.ip_address and vip.ip_address.addr:
                    check(vip.ip_address.addr, neuc, novc, jnc, vs, vip.port_uuid, vip.network_uuid)
                if vip.ip6_address and vip.ip6_address.addr:
                    check(vip.ip6_address.addr, neuc, novc, jnc, vs, vip.port_uuid, vip.network_uuid)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check VIP Ports',
                formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--cloud-uuid', help='Provide cloud uuid')
    parser.add_argument('--cloud-name', help='Provide cloud name')
    parser.add_argument('--vs-uuid', help='Provide vs uuid for which port has to be fixed')
    parser.add_argument('--fix', help='Fix the port issue for particular vs if vs-uuid is provided, else for all vs', action="store_true")
    args = parser.parse_args()
    check_vip_ports(args)

