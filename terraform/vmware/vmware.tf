provider "vsphere" {
  user           = ""
  password       = ""
  vsphere_server = ""
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
  vm_folder = ""
}

output "api_public" {
  value = "${module.vmware_deploy.vsphere_virtual_machine_output}"
}
