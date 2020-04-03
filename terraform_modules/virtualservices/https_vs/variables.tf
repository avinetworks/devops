variable "avi_username" {
  type    = string
  default = ""
}
variable "avi_password" {
  type    = string
  default = ""
}
variable "avi_controller" {
  type    = string
  default = ""
}
variable "avi_version" {
  type    = string
  default = ""
}
variable "pool_name" {
  type    = string
  default = "pool1"
}
variable "lb_algorithm" {
  type    = string
  default = "LB_ALGORITHM_ROUND_ROBIN"
}
variable "server1_ip" {
  type    = string
  default = ""
}
variable "server1_port" {
  type    = number
  default = 8000
}
variable "ssl_key_cert1" {
  type    = string
  default = "System-Default-Cert"
}
variable "ssl_profile1" {
  type    = string
  default = "System-Standard"
}
variable "application_profile1" {
  type    = string
  default = "System-Secure-HTTP"
}
variable "poolgroup_name" {
  type    = string
  default = "poolgroup1"
}
variable "avi_terraform_vs_vip" {
  type    = string
  default = ""
}
variable "vs_name" {
  type    = string
  default = "vs1"
}
variable "vs_port" {
  type    = number
  default = "8990"
}
variable "network_profile" {
  type    = string
  default = "System-TCP-Proxy"
}

