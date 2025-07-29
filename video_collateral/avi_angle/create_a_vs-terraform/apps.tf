variable "healthmonitor" {
  type = map
  default = {
    name = "tfHm1"
    type = "HEALTH_MONITOR_HTTP"
    receive_timeout = "1"
    failed_checks = "2"
    send_interval= "1"
    successful_checks = "2"
    http_request= "HEAD / HTTP/1.0"
  }
}

variable "http_response_code" {
  type = list
  default = ["HTTP_2XX", "HTTP_3XX", "HTTP_5XX"]
}

#### Pool variables

variable "pool" {
  type = map
  default = {
    name = "terraform-pool"
    lb_algorithm = "LB_ALGORITHM_ROUND_ROBIN"
    poolHm = "tfHm1"
    port = "80"
  }
}

#### VS variables

variable "vs" {
  type = map
  default = {
    name = "terraform-app"
    port = "443"
    ssl = "true"
    applicationProfile = "System-Secure-HTTP"
    networkProfile = "System-TCP-Proxy"
    sslProfile = "System-Standard"
    sslCert = "System-Default-Cert"
  }
}