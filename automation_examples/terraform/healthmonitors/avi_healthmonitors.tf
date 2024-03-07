provider "avi" {
  avi_username   = "admin"
  avi_tenant     = "admin"
  avi_password   = var.avi_password
  avi_controller = var.avi_controller
  avi_version    = var.avi_version
  avi_api_timeout    = 50
}

data "avi_tenant" "default_tenant" {
  name = "admin"
}

// Example to create TCP Healthmonitor
resource "avi_healthmonitor" "tcp_healthmonitor" {
  name       = "terraform-tcp-monitor"
  type       = "HEALTH_MONITOR_TCP"
  tenant_ref = data.avi_tenant.default_tenant.id
  tcp_monitor {
    maintenance_response = ""
    tcp_half_open = false
    tcp_request = "EnterYourRequestDataHere"
    tcp_response = "EnterYourResponseDataHere"
  }
  monitor_port = "3000"
  is_federated = false
  receive_timeout = "4"
  send_interval = "10"
  failed_checks = "3"
  successful_checks = "3"
  description = ""
}

// Example to create HTTP Healthmonitor
resource "avi_healthmonitor" "http_healthmonitor" {
  name       = "terraform-http-monitor"
  type       = "HEALTH_MONITOR_HTTP"
  tenant_ref = data.avi_tenant.default_tenant.id
  http_monitor {
    exact_http_request = false
    http_request = "GET / HTTP/1.0"
    http_response = ""
    http_response_code = [
      "HTTP_2XX",
      "HTTP_3XX"
    ]
    maintenance_code = []
    maintenance_response = ""
    ssl_attributes {
      pki_profile_ref = ""
      server_name = ""
      ssl_key_and_certificate_ref = ""
      ssl_profile_ref = ""
    }
  }
  monitor_port = "3000"
  is_federated = false
  receive_timeout = "4"
  send_interval = "10"
  failed_checks = "3"
  successful_checks = "3"
  description = ""
}

// Example to create HTTPS Healthmonitor
resource "avi_healthmonitor" "https_healthmonitor" {
  name       = "terraform-https-monitor"
  type       = "HEALTH_MONITOR_HTTPS"
  tenant_ref = data.avi_tenant.default_tenant.id
  https_monitor {
    exact_http_request = false
    http_request = "GET / HTTP/1.0"
    http_response = ""
    http_response_code = [
      "HTTP_2XX",
      "HTTP_3XX"
    ]
    maintenance_code = []
    maintenance_response = ""
    ssl_attributes {
      pki_profile_ref = "profile-ref"
      server_name = "test-server"
      ssl_key_and_certificate_ref = ""
      ssl_profile_ref = ""
    }
  }
  monitor_port = "3000"
  is_federated = false
  receive_timeout = "4"
  send_interval = "10"
  failed_checks = "3"
  successful_checks = "3"
  description = ""
}

// Example to create UDP Healthmonitor
resource "avi_healthmonitor" "udp_healthmonitor" {
  name       = "terraform-udp-monitor"
  type       = "HEALTH_MONITOR_UDP"
  tenant_ref = data.avi_tenant.default_tenant.id
  udp_monitor {
    maintenance_response = ""
    udp_request = "EnterYourRequestDataHere"
    udp_response = "EnterYourResponseDataHere"
  }
  monitor_port = "3000"
  is_federated = false
  receive_timeout = "4"
  send_interval = "10"
  failed_checks = "3"
  successful_checks = "3"
  description = ""
}