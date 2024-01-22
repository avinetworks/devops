variable "vsphere_user" {
  type = string
  description = <vSphere Username>
}
variable "vsphere_password" {
  type = string
  description = <vSphere Password>
}
variable "vsphere_server" {
  type = string
  description = <vSphere IP/FQDN>
}
variable "datacenter_name" {
  type = string
  description = <Datacenter Name>
}
variable "cluster_name" {
  type = string
  description = <Cluster Name>
}
variable "datastore_name" {
  type = string
  description = <Datastore Name>
}
variable "dvs_name" {
  type = string
  description = <DVS Name>
}
variable "mgmt_net_name" {
  type = string
  description = <Management Network Portgroup Name>
}
variable "local_ovf_path" {
  type = string
  description = ""
}
variable "vsphere_resource_pool" {
  type = string
  description = <Resource Pool Name>
}
variable "vm_folder" {
  type = string
  description = <Folder Name>
}
variable "avi_username" {
  type = string
  description = <Avi Username>
}
variable "avi_old_password" {
  type = string
  default = "58NFaGDJm(PJH0G"
}
variable "avi_new_password" {
  type = string
  description = <Avi Admin NEW Password>
}
variable "avi_version" {
  type = string
  description = <Avi Controller Version>
}

variable "clustervip" {
  type = string
  description = <Avi Cluster VIP IP>
}
variable "backup_passphrase" {
  type = string
  description = <Avi Backup Passphrase>
}
variable "system_dnsresolvers" {
  type = list
  description = <DNS Server IP Addresses List (Ex. ["8.8.8.8", "8.8.4.4"])>
}
variable "system_ntpservers" {
  type    = list
  description = <NTP Server List (Ex. ["0.us.pool.ntp.org", "1.us.pool.ntp.org"])>
}
variable "avi_ctrl_mgmt_ips" {
  type    = list
  description = <Avi Controller Management Network IP Addresse List (Ex. ["10.10.10.10", "10.10.10.11","10.10.10.12"])>
}
variable "subnetMask" {
  type = string
  description = <Management Network Subnet Mask>
}
variable "descriptionGateway" {
  type = string
  description = <Management Network description Gateway>
}
variable "Controller_vm_name" {
  type    = list
  description = <Avi Controller VM Name List (Ex. ["avi-tf-01", "avi-tf-02","avi-tf-03"]>
}


