

data "vsphere_datacenter" "datacenter" {
  name = var.datacenter_name
}

data "vsphere_compute_cluster" "compute_cluster" {
  name          = var.cluster_name
  datacenter_id = data.vsphere_datacenter.datacenter.id
}

data "vsphere_datastore" "datastore" {
  name          = var.datastore_name
  datacenter_id = data.vsphere_datacenter.datacenter.id
}

data "vsphere_distributed_virtual_switch" "dvs" {
  name          = var.dvs_name
  datacenter_id = data.vsphere_datacenter.datacenter.id
}

data "vsphere_network" "management_net" {
  name                            = var.mgmt_net_name
  distributed_virtual_switch_uuid = data.vsphere_distributed_virtual_switch.dvs.id
  datacenter_id                   = data.vsphere_datacenter.datacenter.id
}
