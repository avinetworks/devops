from pyVmomi import vim
from pyVim.connect import SmartConnectNoSSL, Disconnect
import time

"""
This library contains some helper functions for use with the
pyVmomi library for vCenter automation.

PyVmomi is packaged in the Avi Vantage Controller image from
versions 18.1.5 onwards.
"""

def _get_obj(content, vimtype, name, folder=None):
    """
    Get the vsphere object associated with a given text name
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        folder or content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj
 
def _get_child_folder(parent_folder, folder_name):
    obj = None
    for folder in parent_folder.childEntity:
        if folder.name == folder_name:
            if isinstance(folder, vim.Datacenter):
                obj = folder.vmFolder
            elif isinstance(folder, vim.Folder):
                obj = folder
            else:
                obj = None
            break
    return obj
 
def get_folder(si, name):
    subfolders = name.split('/')
    parent_folder = si.RetrieveContent().rootFolder
    for subfolder in subfolders:
        parent_folder = _get_child_folder(parent_folder, subfolder)
        if not parent_folder:
            break
    return parent_folder
 
def get_vm_by_name(si, name, folder=None):
    """
    Find a virtual machine by its name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.VirtualMachine], name,
                    folder)
 
def get_resource_pool(si, name, folder=None):
    """
    Find a resource pool by its name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.ResourcePool], name,
                    folder)
 
def get_cluster(si, name, folder=None):
    """
    Find a cluster by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.ComputeResource], name,
                    folder)
 
def wait_for_task(task, timeout=300):
    """
    Wait for a task to complete
    """
    timeout_time = time.time() + timeout
    timedout = True
    while time.time() < timeout_time:
        if task.info.state == 'success':
            return (True, task.info.result)
        if task.info.state == 'error':
            return (False, None)
        time.sleep(1)
    return (None, None)
 
def wait_for_vm_status(vm, condition, timeout=300):
    timeout_time = time.time() + timeout
    timedout = True
    while timedout and time.time() < timeout_time:
        if (condition(vm)):
            timedout = False
        else:
            time.sleep(3)
 
    return not timedout
 
def net_info_available(vm):
    return (vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn
            and
            vm.guest.toolsStatus == vim.vm.GuestInfo.ToolsStatus.toolsOk
            and
            vm.guest.net)
 
class vcenter_session:
    def __enter__(self):
        return self.session
    def __init__(self, host, user, pwd):
        session = SmartConnectNoSSL(host=host, user=user, pwd=pwd)
        self.session = session
    def __exit__(self, type, value, traceback):
        if self.session:
            Disconnect(self.session)
