terraform {
  required_providers {
    avi = {
      source  = "vmware/avi"
      version = "31.1.1"
    }
  }
}
provider "avi" {
  avi_username   = "admin"
  avi_tenant     = "admin"
  avi_password   = var.avi_password
  avi_controller = var.avi_controller
  avi_version    = var.avi_version
  avi_api_timeout    = 50
}

variable "avi_password" {
  type    = string
  default = "admin"
}

variable "avi_controller" {
  type    = string
}

variable "avi_version" {
  type    = string
  default = "31.1.1"
}

data "avi_tenant" "default_tenant" {
  name = "admin"
}

// Example to create sensitive log analytics profile
resource "avi_analyticsprofile" "sensitive_log_analyticsprofile" {
    name = "Sensitive-Log-AnalyticsProfile"
    tenant_ref = data.avi_tenant.default_tenant.id
    sensitive_log_profile {
        header_field_rules {
            action = "LOG_FIELD_MASKOFF"
            enabled = true
            index = 1
            match {
                match_criteria = "CONTAINS"
                match_str = ["Cookie"]
            }
            name = "mask-log-match-cookie"
        }
        header_field_rules {
            action = "LOG_FIELD_MASKOFF"
            enabled = true
            index = 2
            match {
                match_criteria = "CONTAINS"
                match_str = ["SECURITY-PASSWORD"]
            }
            name = "mask-log-match-security-password"
        }
    }
}

