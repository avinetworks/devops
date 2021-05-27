variable "ssh-key" {
    description = "The name of the IBM Cloud SSH Key allowed to administer the controller instance"
}
variable "subnet" {
    description = "The name of the subnet the instance will be deployed to"
}
variable "vpc" {
    description = "The name of the VPC the instance will be deployed to"
}
variable "zone" {
    description = "The name of the zone the instance will be deployed to"
}
variable "firewall_inbound_subnet" {
    description = "The source subnet to allow for inbound traffic in the controller security group"
    default = "10.0.0.0/8"
} 

variable "firewall_outbound_subnet" {
    description = "The destination subnet to allow in the controller security group for outbound traffic (if controller can't reach internet, install will fail)"
    default = "0.0.0.0/0"
} 

variable "floating_ip" {
    description = "If set to true, a floating IP will be assigned to the instance.  Unnecessary if you have a public gateway assigned to the subnet"
    default = false
    validation {
        condition     = contains([true, false], var.floating_ip)
        error_message = "Argument \"floating_ip\" must be either \"true\" or \"false\"."
    }
}
variable "controller_size" {
    description = "The CPU and Memory size of the NSX ALB controller"
    type = string
    default = "medium"
    validation {
        condition     = contains(["small", "medium", "large"], var.controller_size)
        error_message = "Argument \"controller_size\" must be either \"small\", \"medium\", or \"large\"."
    }
}
variable "instance_type_map" {
    description = "A map from tshirt size to instance size, don't edit unless you need additional size customization"
    type = map
    default = {
        small  = "bx2-8x32"
        medium = "cx2-16x32"
        large  = "cx2-32x64"
    }
}

variable "disk_size" {
    description = "The data disk size of the NSX ALB controller"
    type = string
    default = "small"
    validation {
        condition     = contains(["small", "medium", "large"], var.disk_size)
        error_message = "Argument \"disk_size\" must be either \"small\", \"medium\", or \"large\"."
    }
}
variable "disk_size_map" {
    description = "A map from tshirt size to disk size, don't edit unless you need additional size customization"
    type = map
    default = {
        small  = "256"
        medium = "512"
        large  = "1024"
    }
}
