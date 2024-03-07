terraform {
  required_version = ">= 1.0.7"
  required_providers {
    avi = {
      source = "vmware/avi"
    }

  }
}



provider "avi" {
  avi_username   = var.avi_username
  avi_tenant     = var.avi_tenant
  avi_password   = var.avi_password
  avi_controller = var.avi_controller
  avi_version    = var.avi_version
}

data "avi_sslkeyandcertificate" "custom_csr" {
  name = var.cert_name
}


resource "avi_sslkeyandcertificate" "terraform_vs_cert" {
  name = var.cert_name
  tenant_ref = data.avi_sslkeyandcertificate.custom_csr.tenant_ref
  uuid = data.avi_sslkeyandcertificate.custom_csr.uuid
  certificate {
    certificate = file(var.cert_file)
  }
  key = data.avi_sslkeyandcertificate.custom_csr.key
  type= "SSL_CERTIFICATE_TYPE_VIRTUALSERVICE"
}

