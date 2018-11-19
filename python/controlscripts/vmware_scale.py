from __future__ import print_function
from pyVmomi import vim
import vmutils
from avi.sdk.samples.autoscale.samplescaleout import scaleout_params
import uuid
from avi.sdk.avi_api import ApiSession
import json
import os

"""
This library contains functions needed to handle Server Autoscale
in VMWare.

The pyVmomi library is packaged with the Avi Vantage Contoller
from version 18.1.5 onwards.
"""
 
def getAviApiSession(tenant='admin', api_version=None):
    """
    Create local session to avi controller
    """
    token = os.environ.get('API_TOKEN')
    user = os.environ.get('USER')
    tenant = os.environ.get('TENANT')
    api = ApiSession.get_session("localhost", user, token=token,
                                 tenant=tenant, api_version=api_version)
    return api, tenant
 
def do_scale_in(vmware_settings, instance_names):
    """
    Perform scale in of pool.
    vmware_settings:
        vcenter: IP address or hostname of vCenter
        user: Username for vCenter access
        password: Password for vCenter access
        vm_folder_name: Folder containing VMs (or None for same as
            template)
    instance_names: Names of VMs to destroy
    """
 
    with vmutils.vcenter_session(host=vmware_settings['vcenter'],
                                 user=vmware_settings['user'],
                                 pwd=vmware_settings['password']) as session:
 
        vm_folder_name = vmware_settings.get('vm_folder_name', None)
 
        if vm_folder_name:
            vm_folder = vmutils.get_folder(session, vm_folder_name)
        else:
            vm_folder = None
 
        for instance_name in instance_names:
            vm = vmutils.get_vm_by_name(session, instance_name, vm_folder)
            if vm:
                print('Powering off VM %s...' % instance_name)
                power_off_task = vm.PowerOffVM_Task()
                (power_off_task_status,
                 power_off_task_result) = vmutils.wait_for_task(
                     power_off_task)
                if power_off_task_status:
                    print('Deleting VM %s...' % instance_name)
                    destroy_task = vm.Destroy_Task()
                    (destroy_task_status,
                     destroy_task_result) = vmutils.wait_for_task(
                         destroy_task)
                    if destroy_task_status:
                        print('VM %s deleted!' % instance_name)
                    else:
                        print('VM %s deletion failed!' % instance_name)
                else:
                    print('Unable to power off VM %s!' % instance_name)
            else:
                print('Unable to find VM %s!' % instance_name)
 
def do_scale_out(vmware_settings, pool_name, num_scaleout):
    """
    Perform scale out of pool.
    vmware_settings:
        vcenter: IP address or hostname of vCenter
        user: Username for vCenter access
        password: Password for vCenter access
        cluster_name: vCenter cluster name
        template_folder_name: Folder containing template VM, e.g.
            'Datacenter1/Folder1/Subfolder1' or None to search all
        template_name: Name of template VM
        vm_folder_name: Folder to place new VM (or None for same as
            template)
        customization_spec_name: Name of a customization spec to use
        resource_pool_name: Name of VMWare Resource Pool or None for default
        port_group: Name of port group containing pool member IP
    pool_name: Name of the pool
    num_scaleout: Number of new instances
    """
 
    new_instances = []
 
    with vmutils.vcenter_session(host=vmware_settings['vcenter'],
                                 user=vmware_settings['user'],
                                 pwd=vmware_settings['password']) as session:
 
        template_folder_name = vmware_settings.get('template_folder_name',
                                                   None)
        template_name = vmware_settings['template_name']
        if template_folder_name:
            template_folder = vmutils.get_folder(session,
                                                 template_folder_name)
            template_vm = vmutils.get_vm_by_name(
                session, template_name,
                template_folder)
        else:
            template_vm = vmutils.get_vm_by_name(
                session, template_name)
 
        vm_folder_name = vmware_settings.get('vm_folder_name', None)
        if vm_folder_name:
            vm_folder = vmutils.get_folder(session, vm_folder_name)
        else:
            vm_folder = template_vm.parent
 
        csm = session.RetrieveContent().customizationSpecManager
        customization_spec = csm.GetCustomizationSpec(
            name=vmware_settings['customization_spec_name'])
 
        cluster = vmutils.get_cluster(session,
                                      vmware_settings['cluster_name'])
 
        resource_pool_name = vmware_settings.get('resource_pool_name', None)
 
        if resource_pool_name:
            resource_pool = vmutils.get_resource_pool(session,
                                                      resource_pool_name)
        else:
            resource_pool = cluster.resourcePool
        relocate_spec = vim.vm.RelocateSpec(pool=resource_pool)
 
        clone_spec = vim.vm.CloneSpec(powerOn=True, template=False,
                                      location=relocate_spec,
                                      customization=customization_spec.spec)
 
        port_group = vmware_settings.get('port_group', None)
 
        clone_tasks = []
 
        for instance in range(num_scaleout):
            new_vm_name = '%s-%s' % (pool_name, str(uuid.uuid4()))
 
            print('Initiating clone of %s to %s' % (template_name,
                                                    new_vm_name))
 
            clone_task = template_vm.Clone(name=new_vm_name,
                                           folder=vm_folder,
                                           spec=clone_spec)
            print('Task %s created.' % clone_task.info.key)
            clone_tasks.append(clone_task)
 
        for clone_task in clone_tasks:
            print('Waiting for %s...' % clone_task.info.key)
 
            clone_task_status, clone_vm = vmutils.wait_for_task(clone_task,
                                                                timeout=600)
 
            ip_address = None
 
            if clone_vm:
                print('Waiting for VM %s to be ready...' % clone_vm.name)
                if vmutils.wait_for_vm_status(clone_vm,
                                condition=vmutils.net_info_available,
                                timeout=600):
                    print('Getting IP address from VM %s' % clone_vm.name)
                    for nic in clone_vm.guest.net:
                        if port_group is None or nic.network == port_group:
                            for ip in nic.ipAddress:
                                if '.' in ip:
                                    ip_address = ip
                                    break
                        if ip_address:
                            break
                else:
                    print('Timed out waiting for VM %s!' % clone_vm.name)
 
                if not ip_address:
                    print('Could not get IP for VM %s!' % clone_vm.name)
                    power_off_task = clone_vm.PowerOffVM_Task()
                    (power_off_task_status,
                     power_off_task_result) = vmutils.wait_for_task(
                         power_off_task)
                    if power_off_task_status:
                        destroy_task = clone_vm.Destroy_Task()
                else:
                    print('New VM %s with IP %s' % (clone_vm.name,
                                                    ip_address))
                    new_instances.append((clone_vm.name, ip_address))
            elif clone_task_status is None:
                print('Clone task %s timed out!' % clone_task.info.key)
 
    return new_instances
 
def scale_out(vmware_settings, *args):
    alert_info = json.loads(args[1])
    api, tenant = getAviApiSession()
    (pool_name, pool_uuid,
     pool_obj, num_scaleout) = scaleout_params('scaleout',
                                               alert_info,
                                               api=api,
                                               tenant=tenant)
    print('Scaling out pool %s by %d...' % (pool_name, num_scaleout))
 
    new_instances = do_scale_out(vmware_settings,
                                 pool_name, num_scaleout)
 
    # Get pool object again in case it has been modified
    pool_obj = api.get('pool/%s' % pool_uuid, tenant=tenant).json()
 
    new_servers = pool_obj.get('servers', [])
 
    for new_instance in new_instances:
        new_server = {
            'ip': {'addr': new_instance[1], 'type': 'V4'},
            'hostname': new_instance[0]}
        new_servers.append(new_server)
    pool_obj['servers'] = new_servers
    print('Updating pool with %s' % new_server)
    resp = api.put('pool/%s' % pool_uuid, data=json.dumps(pool_obj))
    print('API status: %d' % resp.status_code)
 
def scale_in(vmware_settings, *args):
    alert_info = json.loads(args[1])
    api, tenant = getAviApiSession()
    (pool_name, pool_uuid,
     pool_obj, num_scaleout) = scaleout_params('scalein',
                                               alert_info,
                                               api=api,
                                               tenant=tenant)
 
    remove_instances = [instance ['hostname'] for instance in
                        pool_obj['servers'][-num_scaleout:]]
    pool_obj['servers'] = pool_obj['servers'][:-num_scaleout]
    print('Scaling in pool %s by %d...' % (pool_name, num_scaleout))
    resp = api.put('pool/%s' % pool_uuid, data=json.dumps(pool_obj))
    print('API status: %d' % resp.status_code)
 
    do_scale_in(vmware_settings, remove_instances)
    
