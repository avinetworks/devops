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

The purpose of this Playbook is to configure a vCenter Cloud Connector. This Playbook supports the use of vCenter Content Libraries for SE image storage. This feature was introduced in 21.1.6. 

# Installation

The methods used within this Playbook can be found in the Avi Networks Ansible Collection (vmware.alb). The following software is required to successfully execute this Playbook:

- Ansible (tested on Ansible version 2.11 and up)
- Avi Networks Ansible Collection (vmware.alb)
- Python requests-toolbelt Utility
- Python requests Utility

# Requirements

The following prerequisites are required to successfully utilize this Workflow:

* A fully deployed vCenter environment is required before connecting an Avi Cluster.
* A user with sufficient permissions to create and manage the SE VMs. For a breakdown of Roles and Permissions required, please see the following KB article - https://avinetworks.com/docs/latest/roles-and-permissions-for-vcenter-nsx-t-users/


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

### vSphere Host Information
VCENTER_SERVER: *\<vCenter Server IP / FQDN\>*</br>
VCENTER_USERNAME: *\<vCenter Username\>*</br>
VCENTER_PASSWORD: *\<vCenter Password\>*</br>
DATACENTER: *\<vCenter Datacenter Name\>*</br>


### vCenter Cloud Connector Settings
CLOUD_NAME: *\<vCenter Cloud Connector Name\>*</br>
DHCP: *\<vCenter Cloud Connector DHCP Setting - true / false \>* #Default is false <br>
CLOUD_PREFIX: *\<vCenter Object Prefix\>*</br>

### DNS Profile
USE_DNS_PROFILE: *\<Use DNS Profile - true / false\>* #Default is false <br>
DNS_PROFILE_NAME: *\<DNS Profile Name\>*</br>
DNS_PROFILE_DOMAINS: *\<DNS Profile Managed Domains\>*</br>
                     *\<- name: Domain name 1\>*</br>
                     *\<- name: Domain name X\>*</br>
STATE_BASED_DNS_REGISTRATION: *\<Use State Based DNS Registration - true / false\>* #Default is false. This is used to update the DNS record based on the state fo the VS <br>

### IPAM Profile
USE_DNS_PROFILE: *\<Use IPAM Profile - true / false\>* #Default is false <br>
DNS_PROFILE_NAME: *\<IPAM Profile Name\>*</br>

### Management Network
MGMT_NET_DHCP: *\<Use DHCP for MGMT - true / false\>* #Default is false <br>
DNS_PROMGMT_NET_PORT_GROUP_NAMEFILE_NAME: *\<MGMT vCenter Port Group Name\>* # Name must match exactly as it is seen in vCenter</br>
MGMT_NET_MASK: *\<MGMT Network Mask\>* # Must be in format XX. Ex. 255.255.255.0 is 24</br>
MGMT_NET_GW: *\<MGMT Network Gateway Address\>* #Ex. 10.10.10.1</br>
MGMT_NETWORK: *\<MGMT Network Network Address\>*#Ex. 10.10.10.0</br>
MGMT_NET_TYPE: *\<MGMT Network Type\>*#Either V4 or V6. Default is V4</br>
MGMT_NET_IP_RANGE_START: *\<MGMT Network IP Pool Starting IP Range\>*</br>
MGMT_NET_IP_RANGE_END: *\<MGMT Network IP Pool Ending IP Range\>*</br>

### VIP Network
VIP_NET_DHCP: *\<Use DHCP for VIP - true / false\>* #Default is false <br>
DNS_PROMGMT_NET_PORT_GROUP_NAMEFILE_NAME: *\<VIP vCenter Port Group Name\>* # Name must match exactly as it is seen in vCenter</br>
VIP_NET_MASK: *\<VIP Network Mask\>* # Must be in format XX. Ex. 255.255.255.0 is 24</br>
VIP_NET_GW: *\<VIP Network Gateway Address\>* #Ex. 20.20.20.1</br>
VIP_NETWORK: *\<VIP Network Network Address\>*#Ex. 20.20.20.0</br>
VIP_NET_TYPE: *\<VIP Network Type\>*#Either V4 or V6. Default is V4</br>
VIP_NET_IP_RANGE_START: *\<VIP Network IP Pool Starting IP Range\>*</br>
VIP_NET_IP_RANGE_END: *\<VIP Network IP Pool Ending IP Range\>*</br>

### vCenter COntent Library
USE_CONTENT_LIBRARY: *\<Use Content Library - true / false\>* #Default is false <br>
CONTENT_LIBRARY: *\<Content Library Name\>* # Name must match exactly as it is seen in vCenter</br>

**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Playbook are:

1.	Check if VCENTER_SERVER is IP or FQDN.
2.	If VCENTER_SERVER is FQDN then check if Controller CLuster can resolve FQDN.
3.	Get Cluster Version.
4.	Create vCenter Content Library Object (If Required)
5.	Create vCenter Configuration based on Version and Content Library use.
6.	Initialize vCenter Cloud Connector.
7.	Create DNS Profile.
8.  Create IPAM Profile.
9.  Create MGMT Network Configuration.
10. Create VIP Network Configuration.
11. Update vCenter Cloud Connector with DNS/IPAM Profiles and MGMT/VIP Network Configurations.


**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this Playbook:

* This Playbook supports IPV4 and IPV6 for the MGMT and VIP networks, however it assumes the COntroller Nodes are IPV4.


