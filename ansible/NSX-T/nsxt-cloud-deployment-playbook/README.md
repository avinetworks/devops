# NSX-T Cloud Deployment

Playbook Developed by: William Stoneman</br>


## Table of Contents
1.	[Introduction](#Introduction)
1.	[Installation](#Installation)
1.	[Requirements](#Requirements)
1.	[Variable Input File](#Variable-Input-File)
1.	[Execution](#Execution)
1.	[Considerations](#Considerations)




# Introduction

The purpose of this Playbook is to configure an NSX-T Cloud Connector. This Playbook supports the creation of both Overlay and VLAN NSX-T Cloud Connector Configurations. Data Segments are not required for the CLoud Connector to be successfully created.

# Installation

The methods used within this Playbook can be found in the Avi Networks Ansible Role (avinetworks.avisdk) or the Avi Networks Ansible Collection (vmware.alb). The following software is required to successfully execute this Playbook:

- Ansible (tested on Ansible version 2.11 and up)
- Avi Networks Ansible Collection (vmware.alb)
- Python requests-toolbelt Utility
- Python pyvmomi Utility
- VMWare OVFTools Utility
- Python requests Utility

# Requirements

The following prerequisites are required to successfully utilize this Workflow:

* A fully deployed NSX-T environment is required before connecting an Avi Cluster.


**[Back to top](#table-of-contents)**


# Variable-Input-File

The following is a breakdown of the required Variables for this Playbook.

### Cluster IP for Avi Controller
CONTROLLER_CLUSTER_IP: <Controller Cluster/Node IP> # Cluster ip.

### Controller Credentials
AVI_CREDENTIALS:
  controller: *\<CONTROLLER_CLUSTER_IP\>*</br>
  username: *\<Avi Username\>*</br>
  password: *\<Avi User Password\>*</br>
  api_version: *\<Avi Controller Version\>* #Ex. "22.1.3"

### NSXT Cloud Connector Users
NSXT_CLOUDCONNECTORUSER: *\<NSXT Cloud Connector User Object Name\>*</br>
NSXT_USERNAME: *\<NSXT Username\>*</br>
NSXT_PASSWORD: *\<NSXT Password\>*</br>
NSXT_VCENTER_CLOUDCONNECTORUSER: *\<NSXT vCenter Cloud COnnector User Object Name \>*</br>
NSXT_VCENTER_USERNAME: *\<vCenter Username\>*</br>
NSXT_VCENTER_PASSWORD: *\<vCenter Password\>*</br>

### NSXT Cloud Connector Settings
CLOUD_NAME: *\<NSXT CLoud Connector Name\>*</br>
DHCP: *\<NSXT CLoud Connector DHCP Setting - true / false \>* #Default is false <br>
CLOUD_PREFIX: *\<NSXT Object Prefix\>*</br>
NSXT_MANAGER: *\<NSXT Manager FQDN/IP Address\>*</br>
NSXT_MGMT_TZ: *\<NSXT Management Transport Zone\>*</br>
NSXT_MGMT_T1: *\<NSXT Management Tier 1 Router\>* #Comment if Transport Zone is type VLAN</br>
NSXT_MGMT_SEG: *\<NSXT Management Segment\>*</br>
NSXT_DATA_TZ: *\<NSXT Data Transport Zone\>*</br>
NSXT_DATA_T1_SEG:  *\<List of Array elements of NSXT Data T1 Segments\>* #Comment if Transport Zone is type VLAN</br>
[*\< - {T1: "<T1 Router Name1>", SEG: "<Segment Name1>"} \>*] #Comment if Transport Zone is type VLAN
[*\< - {T1: "<T1 Router Name2>", SEG: "<Segment Name2>"} \>*] #Comment if Transport Zone is type VLAN
NSXT_DATA_VLAN_SEG: *\<List of Array elements of NSXT Data VLAN Segments\>* #Comment if Transport Zone is type Overlay</br> 
[*\< - {SEG: "Segment Name1>"} \>*] #Comment if Transport Zone is type Overlay
[*\< - {SEG: "Segment Name2>"} \>*] #Comment if Transport Zone is type Overlay


### vCenter Settings
VCENTER_CONN_NAME: *\<vCenter Connection Object Name\>*</br>
VCENTER_HOST: *\<vCenter Host FQDN/IP Address\>* #Must be how the vCenter Host is represented in the NSX-T Manager (FQDN or IP Address)</br>
CONTENT_LIBRARY: *\<Content Library Name\>*</br>


**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Playbook are:

1.	Create NSXT Cloud Connector User.
2.	Create vCenter Cloud COnnector User.
3.	Retrieve MGMT and Data Transport Zone, as well as the vCenter COntent Library.
4.	Create Management Object Configuration.
5.	Create Data Object Configuration.
6.	Initiate NSXT Cloud Connector.
7.	Initiate vCenter Connector.


**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this Playbook:

* This Playbook does not require Data Segments to be defined for it to execute successfully. This is useful if seperate teams handle the individual parts of the Cloud. To configure the intial Data Segment or add additional Data Segments at a later time, the end user can utilize the NSX-T Cloud - Data Segments Playbook. 


