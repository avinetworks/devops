provider "avi" {
  avi_username   = var.avi_username
  avi_tenant     = "admin"
  avi_password   = var.avi_password
  avi_controller = var.avi_controller
  avi_version    = var.avi_version
  avi_api_timeout    = 50
}

data "avi_tenant" "default_tenant" {
  name = "admin"
}
data "avi_cloud" "default_cloud" {
  name = "Default-Cloud"
}
data "avi_applicationprofile" "application_profile1" {
  name = var.application_profile1
}
data "avi_networkprofile" "network_profile1" {
  name = var.network_profile
}

resource "avi_pool" "lb_pool" {
  name         = var.pool_name
  lb_algorithm = var.lb_algorithm
  servers {
    ip {
          type = "V4"
      addr = var.server1_ip
    }
    port = var.server1_port
  }
  tenant_ref = data.avi_tenant.default_tenant.id
}

resource "avi_poolgroup" "poolgroup1" {
  name         = var.poolgroup_name
  members {
        pool_ref = avi_pool.lb_pool.id
        ratio = 100
  }
  tenant_ref = data.avi_tenant.default_tenant.id
}

resource "avi_vsvip" "test_vsvip" {
  name = "terraform-vip"
  vip {
    vip_id = "0"
    ip_address {
      type = "V4"
      addr = var.avi_terraform_vs_vip
    }
  }
  tenant_ref = data.avi_tenant.default_tenant.id
}

resource "avi_virtualservice" "dns_vs" {
  name                          = var.vs_name
  pool_group_ref                = avi_poolgroup.poolgroup1.id
  tenant_ref                    = data.avi_tenant.default_tenant.id
  vsvip_ref                     = avi_vsvip.test_vsvip.id
  cloud_ref                     = data.avi_cloud.default_cloud.id
  application_profile_ref       = data.avi_applicationprofile.application_profile1.id
  network_profile_ref           = data.avi_networkprofile.network_profile1.id
  services {
    port           = var.vs_port
    enable_ssl     = false
  }
}
