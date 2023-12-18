variable "avi_username" {
  type    = string
  description = <Avi Username>
}

variable "avi_controller" {
  type    = string
  description = <Controller Cluster/Node IP>
}
variable "avi_password" {
  type    = string
  description = <Avi User Password>
}

variable "avi_tenant" {
  type    = string
  default = "admin"
}

variable "avi_version" {
  type    = string
  description = <Avi Controller Version>
}

variable "nsxt_url" {
  type    = string
  description = <NSXT Manager FQDN/IP Address>
}

variable "nsxt_avi_user" {
  type    = string
  description = <NSXT Cloud Connector User Object Name>
}

variable "nsxt_username" {
  type    = string
  description = <NSXT Username>
}

variable "nsxt_password" {
  type    = string
  description = <NSXT Password>
}

variable "vsphere_server" {
  type    = string
  description = <vCenter Server FQDN/IP Address>
}

variable "vcenter_avi_user" {
  type    = string
  description = <vCenter Cloud Connector User Object Name>
}

variable "vsphere_user" {
  type    = string
  description = <vCenter Username>
}

variable "vsphere_password" {
  type    = string
  description = <vCenter Password>
}

variable "nsxt_cloudname" {
  type    = string
  description = <NSXT CLoud Connector Name>
}

variable "nsxt_cloud_prefix" {
  type    = string
  description = <NSXT Object Name Prefix>
}

variable "transport_zone_name" {
  type    = string
  description = <Transport Zone Name>
}

variable "mgmt_lr_id" {
  type    = string
  description = <MGMT T1 Name>
}

variable "mgmt_segment_id" {
  type    = string
  description = <MGMT Segment Name>
}

variable "data_lr_id" {
  type    = string
  description = <Data T1 Name>
}

variable "data_segment_id" {
  type    = string
  description = <Data Segment Name>
}

variable "vcenter_id" {
  type    = string
  description = <vCenter Connection Object Name>
}

variable "content_library_name" {
  type    = string
  description = <Content Library Name>
}

