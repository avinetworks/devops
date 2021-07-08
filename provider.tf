terraform {
  required_providers {
    ibm = {
      source = "IBM-Cloud/ibm"
      #version = "<provider version>"
    }
  }
}

provider "ibm" {
  region           = var.region
  ibmcloud_timeout = 300
}