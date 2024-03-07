variable "avi_username" {}
variable "avi_password" {}
variable "avi_tenant" {}
variable "avi_version" {}
variable "avi_controller" {}
variable "tier_1_vrf" {}
variable "tier_2_vrf" {}
variable "server_subnet" {}  # subnet in dotted decimal for back end servers and SEs (ex. 10.10.10.0)
variable "front_end_subnet" {} # subnet in dotted decimal for front end SEs (ex. 10.10.10.0)
#variable "vs_ip" {} 
variable "t2_portgroup" {} # name of vsphere port group for Tier 2
variable "t1_portgroup" {} # name of vsphere port group for Tier 1
variable "front_end_subnet_mask" {} # subnet mask in slash notation (integer, ex. 24)
variable "server_subnet_mask" {} # subnet mask in slash notation (integer, ex. 24)
variable "webserver1_ip" {}
variable "webserver2_ip" {}
variable "avi_cloud" {}
variable "vip_portgroup" {} ## name of vsphere port group for portgroup associated with VIP range
variable "vip_subnet" {} # subnet in dotted decimal for VIPs (ex. 10.10.10.0)
variable "vip_subnet_mask" {} # subnet mask in slash notation (integer, ex. 24)
variable "app_name" {}
