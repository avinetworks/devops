data "ibm_is_image" "centos7" {
    name = "ibm-centos-7-6-minimal-amd64-2"
}

data "ibm_is_vpc" "deployment_vpc" {
    name = var.vpc
}

data "ibm_is_subnet" "deployment_subnet" {
    name = var.subnet
}

data "ibm_is_ssh_key" "avi_tf_key" {
    name = var.ssh-key
}

data "ibm_is_security_group" "avi_external_sg" {
    count = var.security_group == null ? 0 : 1
    name = var.security_group
}
resource "random_string" "random_name_suffix" {
    length           = 4
    special          = false
    upper = false
}

resource "ibm_is_security_group" "avi_controller" {
    count = var.security_group == null ? 1 : 0
    name = "nsxalb-controller-${random_string.random_name_suffix.result}-sg"
    vpc  = data.ibm_is_vpc.deployment_vpc.id
}

resource "ibm_is_security_group_rule" "nsxalb-ssh" {
    depends_on = [ibm_is_security_group.avi_controller]
    count = var.security_group == null ? 1 : 0
    group = ibm_is_security_group.avi_controller[0].id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    tcp {
        port_min = 22
        port_max = 22
    }
}
resource "ibm_is_security_group_rule" "nsxalb-http" {
    depends_on = [ibm_is_security_group_rule.nsxalb-ssh]
    count = var.security_group == null ? 1 : 0
    group = ibm_is_security_group.avi_controller[0].id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    tcp {
        port_min = 80
        port_max = 80
    }
}
resource "ibm_is_security_group_rule" "nsxalb-https" {
    depends_on = [ibm_is_security_group_rule.nsxalb-http]
    count = var.security_group == null ? 1 : 0
    group = ibm_is_security_group.avi_controller[0].id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    tcp {
        port_min = 443
        port_max = 443
    }
}

resource "ibm_is_security_group_rule" "nsxalb-securechannel" {
    depends_on = [ibm_is_security_group_rule.nsxalb-https]
    count = var.security_group == null ? 1 : 0
    group = ibm_is_security_group.avi_controller[0].id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    tcp {
        port_min = 8443
        port_max = 8443
    }
}
resource "ibm_is_security_group_rule" "nsxalb-securechannel-sshtunnel" {
    depends_on = [ibm_is_security_group_rule.nsxalb-securechannel]
    count = var.security_group == null ? 1 : 0
    group = ibm_is_security_group.avi_controller[0].id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    tcp {
        port_min = 5098
        port_max = 5098
    }
}
resource "ibm_is_security_group_rule" "nsxalb-ntp" {
    depends_on = [ibm_is_security_group_rule.nsxalb-securechannel-sshtunnel]
    count = var.security_group == null ? 1 : 0
    group = ibm_is_security_group.avi_controller[0].id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    udp {
        port_min = 123
        port_max = 123
    }
}

resource "ibm_is_security_group_rule" "nsxalb-icmp" {
    depends_on = [ibm_is_security_group_rule.nsxalb-ntp]
    count = var.security_group == null ? 1 : 0
    group = ibm_is_security_group.avi_controller[0].id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    icmp {
        type = 8
    }
}
resource "ibm_is_security_group_rule" "nsxalb-outbound" {
    depends_on = [ibm_is_security_group_rule.nsxalb-icmp]
    count = var.security_group == null ? 1 : 0
    group = ibm_is_security_group.avi_controller[0].id
    direction = "outbound" 
    remote = var.firewall_outbound_subnet
}

resource "ibm_is_volume" "nsxalb_volume" {
    name     = "nsxalb-controller-${random_string.random_name_suffix.result}-data"
    profile  = "general-purpose"
    zone     = var.zone
    capacity = local.disk_size_map[var.disk_size]
}

resource "ibm_is_instance" "nsxalb_controller" {
    depends_on = [ibm_is_security_group_rule.nsxalb-outbound]
    name    = "nsxalb-controller-${random_string.random_name_suffix.result}"
    image   = data.ibm_is_image.centos7.id
    profile = local.instance_type_map[var.controller_size]

    boot_volume {
        name = "nsxalb-controller-${random_string.random_name_suffix.result}-boot"
    }

    primary_network_interface {
        name = "nsxalb-controller-${random_string.random_name_suffix.result}-mgmt"
        subnet = data.ibm_is_subnet.deployment_subnet.id
        security_groups = [ var.security_group == null ? ibm_is_security_group.avi_controller[0].id :  data.ibm_is_security_group.avi_external_sg[0].id]
    }

    vpc       = data.ibm_is_vpc.deployment_vpc.id
    zone      = var.zone
    keys      = [data.ibm_is_ssh_key.avi_tf_key.id]
    user_data = templatefile("build_ansible.sh", { nsxalb_version = var.nsxalb_version })
    volumes = [ibm_is_volume.nsxalb_volume.id]
}

resource "ibm_is_floating_ip" "nsx_alb_floatingip" {
    count = var.floating_ip == "true" ? 1 : 0
    name   = "nsxalb-controller-${random_string.random_name_suffix.result}-fip"
    target = ibm_is_instance.nsxalb_controller.primary_network_interface[0].id
}



output "controller_publicip" {
    value = [ibm_is_floating_ip.nsx_alb_floatingip.*.address]
}

output "controller_private_ip" {
    value = ibm_is_instance.nsxalb_controller.primary_network_interface.0.primary_ipv4_address
}
