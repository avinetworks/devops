# NSXT Cloud Data Subsequent Segment Creation

Scripts Developed by: William Stoneman</br>

# Introduction

The purpose of this file is to lay out the steps to create subsequent NSX-T Data Segment after the NSX-T Cloud Connector has been successfully created and the intial Data Segment is configured. 

The information provided below is for demonstration purposes only, and you should update the variables with the information from your environment.

# Low Level Process Review


1. Create tf script:
```hcl
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

data "avi_cloud" "nsxt" {
  name = "NSX-T" # Update with desired Cloud Connector Name
}

output "nsxt" {
  value = data.avi_cloud.nsxt.uuid
}
```

2. Create variables file:
```hcl
variable "avi_username" {
  type    = string
  description = <Avi CLuster Username>
}

variable "avi_controller" {
  type    = string
  description = <Avi Cluster VIP IP>
}
variable "avi_password" {
  type    = string
  description = <Avi Cluster Username Password>
}

variable "avi_tenant" {
  type    = string
  default = "admin"
}

variable "avi_version" {
  type    = string
  default = "20.1.6"
}

variable "data_lr_id" {
  type    = string
  description = <T1 ROuter Name>
}

variable "data_segment_id" {
  type    = string
  description = <Segment Name>
}
```


3. Run *terraform init*.

4. Run *terraform plan*, and copy the uuid from the output.

5. Append the following to the terraform script:
```hcl
resource "avi_cloud" "nsx-t-cloud" {
  # (resource arguments)
}
```
6. run *terraform import avi_cloud.nsx-t-cloud <cloud uuid copied in step 4>*

7. Run *terraform show* and copy the output.

8. Edit the tf script avi_cloud section and add the output from step 6. (The Information listed below is for demonstration purposes)
```hcl
terraform {
  required_version = ">= 1.0.7"
  required_providers {
	avi = {
	  source = "vmware/avi"
	  version = "21.1.1"
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

data "avi_cloud" "nsxt" {
  name = "NSX-T"
}

output "nsxt" {
  value = data.avi_cloud.nsxt.uuid
}

resource "avi_cloud" "nsx-t-cloud" {
	dhcp_enabled      = "true"
	id                = "https://10.10.10.10/api/cloud/cloud-e4ac05d3-135f-4840-b473-9c88c3192c5b"
	ipam_provider_ref = "https://10.10.10.10/api/ipamdnsproviderprofile/ipamdnsproviderprofile-9e91ff51-925f-4660-8319-d6d866113334"
	license_tier      = "ENTERPRISE"
	license_type      = "LIC_CORES"
	name              = "NSX-T"
	obj_name_prefix   = "WS"
	tenant_ref        = "https://10.10.10.10/api/tenant/admin"
	uuid              = "cloud-e4ac05d3-135f-4840-b473-9c88c3192c5b"
	vtype             = "CLOUD_NSXT"

	nsxt_configuration {
		nsxt_credentials_ref = "https://10.10.10.10/api/cloudconnectoruser/cloudconnectoruser-235a3f52-a279-40f4-8b49-f6b75c7f18f0"
		nsxt_url             = "10.206.40.245"

		data_network_config {
			transport_zone = "/infra/sites/default/enforcement-points/default/transport-zones/3208eed0-cc1a-4ad4-8f94-3db219cb3d8e"
			tz_type        = "OVERLAY"
			vlan_segments  = []

			tier1_segment_config {

				manual {
					tier1_lrs {
						segment_id  = "jda-sedata-a"
						tier1_lr_id = "Router-T1A"
					}
				}
			}
		}

		management_network_config {
			transport_zone = "/infra/sites/default/enforcement-points/default/transport-zones/3208eed0-cc1a-4ad4-8f94-3db219cb3d8e"
			tz_type        = "OVERLAY"

			overlay_segment {
				segment_id  = "/infra/segments/semanagement"
				tier1_lr_id = "/infra/tier-1s/Router-T1A"
			}
		}
	}
}
```

9. Edit the data_network_config section of the avi_cloud resource. Add the new data sengment to the manual section:

```hcl
manual {
	tier1_lrs {
		segment_id  = "jda-sedata-a"
		tier1_lr_id = "Router-T1A"
	}
	tier1_lrs {
		segment_id  = var.data_segment_id
		tier1_lr_id = var.data_lr_id
	}
}
```	
AND REMOVE ID LINE (The Information listed below is for demonstration purposes):
```hcl
id              = "https://10.10.10.10/api/cloud/cloud-f02c1589-dabd-4394-9cc1-ccab61c812b2"
```

10. Run *terraform plan*.

11. Run *terraform apply*.

