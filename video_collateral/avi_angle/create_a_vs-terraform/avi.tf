data "avi_cloud" "default_cloud" {
  name = var.avi_cloud.name
}

data "avi_tenant" "tenant" {
  name = var.tenant
}

data "avi_network" "network_vip" {
  name = var.network_name
  cloud_ref = data.avi_cloud.default_cloud.id
}

data "avi_sslkeyandcertificate" "ssl_cert1" {
  name = var.vs["sslCert"]
}

data "avi_sslprofile" "ssl_profile1" {
  name = var.vs["sslProfile"]
}

data "avi_applicationprofile" "application_profile1" {
  name = var.vs["applicationProfile"]
}

data "avi_networkprofile" "network_profile1" {
  name = var.vs["networkProfile"]
}

data "avi_vrfcontext" "vrfcontext" {
  name = var.tier1_name
  cloud_ref = data.avi_cloud.default_cloud.id
}


resource "avi_healthmonitor" "hm" {
  name = var.healthmonitor.name
  tenant_ref = data.avi_tenant.tenant.id
  type = var.healthmonitor.type
  receive_timeout = var.healthmonitor.receive_timeout
  failed_checks = var.healthmonitor.failed_checks
  send_interval = var.healthmonitor.send_interval
  successful_checks = var.healthmonitor.successful_checks
  http_monitor {
    http_request = var.healthmonitor.http_request
    http_response_code = var.http_response_code
  }
}

data "avi_healthmonitor" "hm" {
  depends_on = [avi_healthmonitor.hm]
  name = var.healthmonitor.name
}

resource "avi_pool" "lbpool" {
  depends_on = [avi_healthmonitor.hm]
  name = var.pool.name
  tenant_ref = data.avi_tenant.tenant.id
  lb_algorithm = var.pool.lb_algorithm
  vrf_ref = data.avi_vrfcontext.vrfcontext.id
  cloud_ref = data.avi_cloud.default_cloud.id
  health_monitor_refs = ["${data.avi_healthmonitor.hm.id}"]
  dynamic servers {
    for_each = [for server in var.avi_servers_ips:{
      addr = server
    }]
    content {
      ip {
        type = "V4"
        addr = servers.value.addr
      }
      port = var.pool.port
    }
  }
}

resource "avi_vsvip" "vsvip" {
  name = "vsvip-${var.vs.name}"
  tenant_ref = data.avi_tenant.tenant.id
  cloud_ref = data.avi_cloud.default_cloud.id
  vrf_context_ref = data.avi_vrfcontext.vrfcontext.id
  vip {
    vip_id = 1
    auto_allocate_ip = true
    ipam_network_subnet {
      network_ref = data.avi_network.network_vip.id
      subnet {
        mask = split("/", var.network_cidr)[1]
        ip_addr {
          type = "V4"
          addr = split("/", var.network_cidr)[0]
        }
      }
    }
  }
  dns_info {
    fqdn = "${var.vs.name}.${var.domain_name}"
  }
}

data "avi_vsvip" "vsvip" {
  depends_on = [avi_vsvip.vsvip]
  name = "vsvip-${var.vs.name}"
}

data "avi_serviceenginegroup" "seg" {
  name = var.se_group_ref
  cloud_ref = data.avi_cloud.default_cloud.id
}

resource "avi_virtualservice" "https_vs" {
  name = var.vs.name
  pool_ref = avi_pool.lbpool.id
  cloud_ref = data.avi_cloud.default_cloud.id
  tenant_ref = data.avi_tenant.tenant.id
  ssl_key_and_certificate_refs = [data.avi_sslkeyandcertificate.ssl_cert1.id]
  ssl_profile_ref = data.avi_sslprofile.ssl_profile1.id
  application_profile_ref = data.avi_applicationprofile.application_profile1.id
  network_profile_ref = data.avi_networkprofile.network_profile1.id
  vsvip_ref= data.avi_vsvip.vsvip.id
  se_group_ref= data.avi_serviceenginegroup.seg.id
  services {
    port           = var.vs.port
    enable_ssl     = var.vs.ssl
  }
  analytics_policy {
    client_insights = "NO_INSIGHTS"
    all_headers = "true"
    udf_log_throttle = "10"
    significant_log_throttle = "0"
    metrics_realtime_update {
      enabled  = "true"
      duration = "0"
    }
    full_client_logs {
      enabled = "true"
      throttle = "10"
      duration = "0"
    }
  }
  lifecycle {
    ignore_changes = [
      cloud_type
    ]
  }
}