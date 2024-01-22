terraform {
  required_version = ">= 1.0.7"
  required_providers {
    vsphere = {
      source  = "hashicorp/vsphere"
     }    
    avi = {
      source  = "vmware/avi"
    }
  }

}

provider "vsphere" {
  user                   = var.vsphere_user
  password               = var.vsphere_password
  vsphere_server         = var.vsphere_server
  allow_unverified_ssl   = true
}


data "vsphere_resource_pool" "resource_pool" {
  name                  = var.vsphere_resource_pool
  datacenter_id 	= data.vsphere_datacenter.datacenter.id
}

data "vsphere_content_library" "content_library" {
  name            = "AVI"
}

data "vsphere_content_library_item" "controllerovf" {
  name        = "Controller"
  type	      = "ovf"
  library_id  = data.vsphere_content_library.content_library.id
}

resource "vsphere_virtual_machine" "controller" {
  name              = var.Controller_vm_name[count.index]
  resource_pool_id  = data.vsphere_resource_pool.resource_pool.id
  datastore_id      =  data.vsphere_datastore.datastore.id
  count             = 3
  num_cpus          = 8
  memory            = 24576
  folder            = var.vm_folder

  network_interface {
    network_id   = data.vsphere_network.management_net.id
  }
  lifecycle {
    ignore_changes = [guest_id]
  }
  disk {
    label            = "disk0"
    size             = 128
    thin_provisioned = false
  }
  clone {
   template_uuid = data.vsphere_content_library_item.controllerovf.id
  }
  vapp {
    properties = {
      "mgmt-ip"     = var.avi_ctrl_mgmt_ips[count.index]
      "mgmt-mask"   = var.subnetMask
      "default-gw"  = var.defaultGateway
    }
  }
  wait_for_guest_net_timeout = 10   # Increase in slow environments
}

resource "null_resource" "wait_https_controllers" {
  depends_on = [vsphere_virtual_machine.controller]
  count = 3

  provisioner "local-exec" {
    command = "count=1 ; while [ $(curl -k -s -o /dev/null -w \"%%{http_code}\"   https://${var.avi_ctrl_mgmt_ips[count.index]}) != \"200\" ]; do echo \"Attempt $count: Waiting for Avi Controllers to be ready...\"; sleep 5 ; count=$((count+1)) ;  if [ \"$count\" = 120 ]; then echo \"ERROR: Unable to connect to Avi Controller API\" ; exit 1 ; fi ; done"
  }
}


provider "avi" {
  avi_username   = var.avi_username
  avi_password   = var.avi_old_password
  avi_controller = var.avi_ctrl_mgmt_ips[0]
  avi_tenant     = "admin"
  avi_version    = var.avi_version
}

resource "avi_cluster" "vmware_cluster" {
  depends_on = [null_resource.wait_https_controllers]
  name   = "cluster-0-1"
  virtual_ip { 
    type = "V4"
    addr =  var.clustervip 
   }
  nodes {
    ip {
      type = "V4"
      addr = var.avi_ctrl_mgmt_ips[0]
    }
    name = vsphere_virtual_machine.controller[0].name
  }
  nodes {
    ip {
      type = "V4"
      addr = var.avi_ctrl_mgmt_ips[1]
    }
    name = vsphere_virtual_machine.controller[1].name
  }
  nodes {
    ip {
      type = "V4"
      addr = var.avi_ctrl_mgmt_ips[2]
    }
    name = vsphere_virtual_machine.controller[2].name
  }
}

resource "null_resource" "wait_https_cluster" {
  depends_on = [avi_cluster.vmware_cluster]
  count = 3

  provisioner "local-exec" {
    command = "count=1 ; while [ $(curl -k -s -o /dev/null -w \"%%{http_code}\"   https://${var.clustervip}) != \"200\" ]; do echo \"Attempt $count: Waiting for Avi Controllers to be ready...\"; sleep 5 ; count=$((count+1)) ;  if [ \"$count\" = 120 ]; then echo \"ERROR: Unable to connect to Avi Controller API\" ; exit 1 ; fi ; done"
  }
}


resource "avi_backupconfiguration" "backupconfig" {
  depends_on = [null_resource.wait_https_cluster]
  name = "Backup-Configuration"
  save_local = true
  backup_passphrase = var.backup_passphrase
}

resource "avi_systemconfiguration" "avi_sysconfig" {
  depends_on = [avi_backupconfiguration.backupconfig]
  dns_configuration {
    dynamic "server_list" {
      for_each = var.system_dnsresolvers
      content {
        type  = "V4"
        addr = server_list.value
      }
    }
  }
  ntp_configuration {
    dynamic "ntp_servers" {
      for_each = var.system_ntpservers
      content {
          server {
            type  = "DNS"
            addr = ntp_servers.value
          }
      }
    }
  }
  email_configuration {
    smtp_type = "SMTP_LOCAL_HOST"
    from_email = "admin@avicontroller.net"
    mail_server_name = "localhost"
  }
  global_tenant_config {
    tenant_vrf = false
    se_in_provider_context = true
    tenant_access_to_provider_se = true
  }  
  welcome_workflow_complete = true
}
resource "avi_useraccount" "avi_user" {
  depends_on = [avi_systemconfiguration.avi_sysconfig]
  username     = var.avi_username
  old_password = var.avi_old_password
  password     = var.avi_new_password
}
