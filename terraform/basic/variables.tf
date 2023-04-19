variable "avi_password" {
  type    = string
  default = "password"
}

variable "avi_controller" {
  type    = string
  default = "10.102.16.112"
}

variable "avi_terraform_vs_vip" {
  type = string
  default = "100.64.72.100"
}

variable "avi_test_server_p21" {
  type = string
  default = "100.64.72.111"
}

variable "avi_test_server_p22" {
  type = string
  default = "100.64.72.112"
}

variable "avi_test_server_p23" {
  type = string
  default = "100.64.72.113"
}

variable "avi_test_server_p11" {
  type = string
  default = "100.64.72.114"
}


variable "avi_test_server_p12" {
  type = string
  default = "100.64.72.115"
}
