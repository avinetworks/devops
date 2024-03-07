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
resource "random_string" "random_name_suffix" {
    length           = 4
    special          = false
    upper = false
}

resource "ibm_is_security_group" "avi_controller" {
    name = "nsxalb-controller-${random_string.random_name_suffix.result}-sg"
    vpc  = data.ibm_is_vpc.deployment_vpc.id
}

resource "ibm_is_security_group_rule" "nsxalb-ssh" {
    depends_on = [ibm_is_security_group.avi_controller]
    group = ibm_is_security_group.avi_controller.id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    tcp {
        port_min = 22
        port_max = 22
    }
}
resource "ibm_is_security_group_rule" "nsxalb-http" {
    depends_on = [ibm_is_security_group_rule.nsxalb-ssh]
    group = ibm_is_security_group.avi_controller.id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    tcp {
        port_min = 80
        port_max = 80
    }
}
resource "ibm_is_security_group_rule" "nsxalb-https" {
    depends_on = [ibm_is_security_group_rule.nsxalb-http]
    group = ibm_is_security_group.avi_controller.id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    tcp {
        port_min = 443
        port_max = 443
    }
}

resource "ibm_is_security_group_rule" "nsxalb-securechannel" {
    depends_on = [ibm_is_security_group_rule.nsxalb-https]
    group = ibm_is_security_group.avi_controller.id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    tcp {
        port_min = 8443
        port_max = 8443
    }
}
resource "ibm_is_security_group_rule" "nsxalb-securechannel-sshtunnel" {
    depends_on = [ibm_is_security_group_rule.nsxalb-securechannel]
    group = ibm_is_security_group.avi_controller.id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    tcp {
        port_min = 5098
        port_max = 5098
    }
}
resource "ibm_is_security_group_rule" "nsxalb-ntp" {
    depends_on = [ibm_is_security_group_rule.nsxalb-securechannel-sshtunnel]
    group = ibm_is_security_group.avi_controller.id
    direction = "inbound" 
    remote = var.firewall_inbound_subnet
    udp {
        port_min = 123
        port_max = 123
    }
}
resource "ibm_is_security_group_rule" "nsxalb-outbound" {
    depends_on = [ibm_is_security_group_rule.nsxalb-ntp]
    group = ibm_is_security_group.avi_controller.id
    direction = "outbound" 
    remote = var.firewall_outbound_subnet
}

resource "ibm_is_volume" "nsxalb_volume" {
    name     = "nsxalb-controller-${random_string.random_name_suffix.result}-data"
    profile  = "general-purpose"
    zone     = var.zone
    capacity = var.disk_size_map[var.disk_size]
}

resource "ibm_is_instance" "nsxalb_controller" {
    depends_on = [ibm_is_security_group_rule.nsxalb-outbound]
    name    = "nsxalb-controller-${random_string.random_name_suffix.result}"
    image   = data.ibm_is_image.centos7.id
    profile = var.instance_type_map[var.controller_size]

    boot_volume {
        name = "nsxalb-controller-${random_string.random_name_suffix.result}-boot"
    }

    primary_network_interface {
        name = "nsxalb-controller-${random_string.random_name_suffix.result}-mgmt"
        subnet = data.ibm_is_subnet.deployment_subnet.id
        security_groups = [ibm_is_security_group.avi_controller.id]
    }

    vpc       = data.ibm_is_vpc.deployment_vpc.id
    zone      = var.zone
    keys      = [data.ibm_is_ssh_key.avi_tf_key.id]
    user_data = file("build_ansible.sh")
    volumes = [ibm_is_volume.nsxalb_volume.id]
}

resource "ibm_is_floating_ip" "nsx_alb_floatingip" {
    count = var.floating_ip ? 1 : 0
    name   = "nsxalb-controller-${random_string.random_name_suffix.result}-fip"
    target = ibm_is_instance.nsxalb_controller.primary_network_interface[0].id
}



output "controller_publicip" {
    value = concat(ibm_is_floating_ip.nsx_alb_floatingip.*.address, list(""))
}

output "controller_private_ip" {
    value = ibm_is_instance.nsxalb_controller.primary_network_interface.0.primary_ipv4_address
}
