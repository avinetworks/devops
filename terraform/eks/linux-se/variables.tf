variable "aws_creds_file" {
  default = "~/.aws/credentials"
}

# Preferably use env vars for aws acccess and secret key
variable "aws_access_key" {
  default=""
}

variable "aws_secret_key" {
  default =""
}

# Name of the SSH key pair
variable "ssh_key_name" {
  type    = "string"
  default = "ec2_ssh_key"
}

variable "aws_region" {
  type    = "string"
  default = "us-west-2"
}

# Instance disk size
variable "ec2_disk_gb" {
  type    = "string"
  default = "40"
}

# Allocate public IP if private IP of instance
# is not reachable from this machine
variable "ec2_public_ip" {
  default = false
}

# Number of SEs
variable "se_count" {
  type    = "string"
  default = "1"
}

# Subnet IDs where the SE must be connected
variable "se_subnet" {
  type    = "list"
  default = ["subnet-050fd3525a1e1a06f", "subnet-01cd5963745b6775d", "subnet-0ba0cf2692dd8dbba"]
}

# Instance type of the ec2 instance
variable "se_instance_type" {
  type    = "string"
  default = "t2.medium"
}

# Security groups to be applied to the SE instance
# EKS node security group must be applied to allow
# traffic from SE to Pods
variable "se_security_groups" {
  type    = "list"
  default = ["sg-00148b5008bc544b6","sg-04a6bb095a2109b11"]
}

# Number of cores SE should use on the instance
# must be <= instance vCPUs
variable "se_cores" {
  type    = "string"
  default = "2"
}

# Memory SE should reserve on the instance
# Leave at least 1024 MB of memory for the OS
variable "se_mem_mb" {
  type    = "string"
  default = "3072"
}

# Disk size for SE use
# Leave at least 10 GB for the OS
variable "se_disk_gb" {
  type    = "string"
  default = "30"
}

# Avi controller version
variable "avi_version" {
  type    = "string"
  default = "18.2.2"
}

# Docker tag matching current avi version
# Check https://hub.docker.com/r/avinetworks/se/tags
variable "se_docker_tag" {
  type    = "string"
  default = "18.2.2-9224-20190306.090737"
}

# Avi controller IP address
variable "avi_controller" {
  type    = "string"
  default = "192.168.10.10"
}

# Avi cloud UUID
# Browse to https://<avi-controller-ip>/api/cloud
variable "avi_cloud" {
  type    = "string"
  default = "cloud-5d965a28-cf2a-46e1-9aa4-d657d7e87364"
}

# SE group UUID where SE should attach
# Browse to https://<avi-controller-ip>/api/serviceenginegroup
variable "avi_se_group" {
  type    = "string"
  default = "serviceenginegroup-f5b2ac93-a660-4602-be65-da15a0f048de"
}


