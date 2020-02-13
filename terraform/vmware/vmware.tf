provider "vsphere" {
  user           = var.vsphare_user
  password       = var.vsphare_password
  vsphere_server = var.vsphere_server
  allow_unverified_ssl = true
  version = "1.15.0"
}

module "vmware_deploy" {
  source = "../../terraform_modules/vmware_deploy"

  vm_datastore = ""
  vsphere_cluster = ""
  vsphere_datacenter = ""
  vm_network = ""
  vm_template = ""
  vm_name = ""
  vm_folder = "/folder/path"
}

output "controller_1" {
  value = "${module.vmware_deploy.vsphere_virtual_machine_vm1}"
}

output "controller_2" {
  value = "${module.vmware_deploy.vsphere_virtual_machine_vm2}"
}

output "controller_3" {
  value = "${module.vmware_deploy.vsphere_virtual_machine_vm3}"
}
