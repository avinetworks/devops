# NSX-T Cloud Deployment

Script Developed by: William Stoneman</br>


## Table of Contents
1.	[Introduction](#Introduction)
1.	[Installation](#Installation)
1.	[Requirements](#Requirements)
1.	[Variable Input File](#Variable-Input-File)
1.	[Execution](#Execution)
1.	[Considerations](#Considerations)




# Introduction

The purpose of this Terraform script is to configure an NSX-T Cloud Connector. Data Segments are not required for the CLoud Connector to be successfully created.

# Installation

The methods used within this Terraform Script can be found in the Avi Networks Terriform Provider (vmware/avi). The following software is required to successfully execute this Terraform Script:

Terraform (tested on Terraform version 1.1.0 and up)

# Requirements

The following prerequisites are required to successfully utilize this Workflow:

* A fully deployed NSX-T environment is required before connecting an Avi Cluster.


**[Back to top](#table-of-contents)**


# Variable-Input-File

The following is a breakdown of the required Variables for this Terraform Script.

avi_username.default: *\<Avi Username\>*

avi_controller.default: *\<Controller Cluster/Node IP\>*

avi_password.default: *\<Avi User Password\>*


avi_tenant.default: "admin"


avi_version.default: *\<Avi Controller Version\>*


nsxt_url.default: *\<NSXT Manager FQDN/IP Address\>*


nsxt_avi_user.default: *\<NSXT Cloud Connector User Object Name\>*


nsxt_username.default: *\<NSXT Username\>*


nsxt_password.default: *\<NSXT Password\>*


vsphere_server.default: *\<vCenter Server FQDN/IP Address\>*


vcenter_avi_user.default: *\<vCenter Cloud Connector User Object Name\>*


vsphere_user.default: *\<vCenter Username\>*


vsphere_password.default: *\<vCenter Password\>*


nsxt_cloudname.default: *\<NSXT CLoud Connector Name\>*


nsxt_cloud_prefix.default: *\<NSXT Object Name Prefix\>*


transport_zone_name.default: *\<Transport Zone Name\>*


mgmt_lr_id.default: *\<MGMT T1 Name\>*


mgmt_segment_id.default: *\<MGMT Segment Name\>*


data_lr_id.default: *\<Data T1 Name\>*


data_segment_id.default: *\<Data Segment Name\>*


vcenter_id.default: *\<vCenter Connection Object Name\>*


content_library_name.default: *\<Content Library Name\>*


**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Playbook are:

1.	Retrieve Transport Zone, as well as the vCenter Content Library.
2.  Create NSXT Cloud Connector User.
3.	Create vCenter Cloud COnnector User.
4.	Create Management Object Configuration.
5.	Create Data Object Configuration.
6.	Initiate NSXT Cloud Connector.
7.	Initiate vCenter Connector.


**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this script:

* This script does not require Data Segments to be defined for it to execute successfully. This is useful if seperate teams handle the individual parts of the Cloud. To configure the intial Data Segment or add additional Data Segments at a later time, the end user can utilize the NSX-T Cloud - Data Segments script. 

* This script assumes the same transport Zone for both MGMT and Data.

* This script deploys using overlay segments for both mgmt and data (if required). VLAN segments can easily be configured.


