terraform {
  required_version = ">= 1.0.7"
  required_providers {
    avi = {
      source = "vmware/avi"
    }
    nsxt = {
      source = "vmware/nsxt"
    }
    vsphere = {
      source = "hashicorp/vsphere"
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

provider "vsphere" {
  user           = var.vsphere_user
  password       = var.vsphere_password
  vsphere_server = var.vsphere_server
  allow_unverified_ssl = true
}

provider "nsxt" {
  host                     = var.nsxt_url
  username                 = var.nsxt_username
  password                 = var.nsxt_password
  allow_unverified_ssl     = true
}

#Retrieve NSXT Transport Zone UUID
#Remove nsx-tr-zone if you have multiple transport zones with same name
data "nsxt_transport_zone" "nsx-tr-zone" {
  display_name   = var.transport_zone_name
}

#Retrieve vSphere Content Library UUID
data "vsphere_content_library" "library" {
  name           = var.content_library_name
}

#Creates NSX-T User on Avi controller
resource "avi_cloudconnectoruser" "nsx-t-user" {
  name           = var.nsxt_avi_user
  tenant_ref     = var.avi_tenant
  nsxt_credentials {
    password     = var.nsxt_password
    username     = var.nsxt_username
  }
}
#Creates vCenter User on Avi controller
resource "avi_cloudconnectoruser" "vcenter-user" {
  name           = var.vcenter_avi_user
  tenant_ref     = var.avi_tenant
  vcenter_credentials {
    password     = var.vsphere_password
    username     = var.vsphere_user
  }
}

#Creates NSX-T Cloud on Avi controller
resource "avi_cloud" "nsx-t-cloud" {
  depends_on     = [avi_cloudconnectoruser.nsx-t-user]
  name           = var.nsxt_cloudname
  tenant_ref     = var.avi_tenant
  vtype          = "CLOUD_NSXT"
  obj_name_prefix = var.nsxt_cloud_prefix
  nsxt_configuration {
    nsxt_url     = var.nsxt_url
    management_network_config {
      transport_zone = data.nsxt_transport_zone.nsx-tr-zone.id
      tz_type = "OVERLAY"
      overlay_segment {
        tier1_lr_id = var.mgmt_lr_id
        segment_id  = var.mgmt_segment_id
      }
    }
    data_network_config {
      transport_zone = data.nsxt_transport_zone.nsx-tr-zone.id
      tz_type = "OVERLAY"
      tier1_segment_config{
        segment_config_mode = "TIER1_SEGMENT_MANUAL"
        manual {
          tier1_lrs {
            tier1_lr_id = var.data_lr_id
            segment_id  = var.data_segment_id
          }
        }

      }

    }
    automate_dfw_rules = "false"
    nsxt_credentials_ref = avi_cloudconnectoruser.nsx-t-user.uuid
  }
}

#Creates vCenterserver on Avi controller and attaches vcenterserver to cloud
resource "avi_vcenterserver" "vc-01" {
  depends_on      = [ avi_cloudconnectoruser.vcenter-user,
                      avi_cloud.nsx-t-cloud ]
  name            = var.vcenter_id
  tenant_ref      = var.avi_tenant
  cloud_ref       = avi_cloud.nsx-t-cloud.uuid
  vcenter_url     = var.vsphere_server
  vcenter_credentials_ref = avi_cloudconnectoruser.vcenter-user.uuid
  content_lib {
    id            = data.vsphere_content_library.library.id
  }
}

