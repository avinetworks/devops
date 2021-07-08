terraform {
  required_providers {
    ibm = {
      source = "IBM-Cloud/ibm"
      #version = "<provider version>"
    }
  }
}

provider "ibm" {
  generation       = 2
  region           = var.region
  ibmcloud_timeout = 300
}