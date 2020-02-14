provider "avi" {
  avi_username   = var.avi_username
  avi_password   = var.avi_password
  avi_controller = "${module.vmware_deploy.vsphere_virtual_machine_vm1}"
  avi_tenant     = "admin"
}

resource "avi_useraccount" "avi_user" {
  username     = var.avi_username
  old_password = var.avi_current_password
  password     = var.avi_new_password
}

resource "avi_cluster" "vmware_cluster" {
  name = "cluster-0-1"
  nodes {
    ip {
      type = "V4"
      addr = "${module.vmware_deploy.vsphere_virtual_machine_vm1}"
    }
    name = "${module.vmware_deploy.vsphere_virtual_machine_vm1}"
  }
  nodes {
    ip {
      type = "V4"
      addr = "${module.vmware_deploy.vsphere_virtual_machine_vm2}"
    }
    name = "${module.vmware_deploy.vsphere_virtual_machine_vm2}"
  }
  nodes {
    ip {
      type = "V4"
      addr = "${module.vmware_deploy.vsphere_virtual_machine_vm3}"
    }
    name = "${module.vmware_deploy.vsphere_virtual_machine_vm3}"
  }
}


output "avi_cluster_output" {
  value = "${avi_cluster.vmware_cluster}"
}