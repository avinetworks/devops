
// Avi Provider variables
variable "avi_username" {
  type = "string"
  default = "admin"
}

variable "avi_password" {
  type = "string"
  default = ""
}

variable "avi_current_password" {
  type = "string"
  default = ""
}

variable "avi_new_password" {
  type = "string"
  default = ""
}

// Vsphare provider variables
variable "vsphare_user" {
  type = "string"
  default = ""
}

variable "vsphare_password" {
  type = "string"
  default = ""
}

variable "vsphere_server" {
  type = "string"
  default = ""
}
