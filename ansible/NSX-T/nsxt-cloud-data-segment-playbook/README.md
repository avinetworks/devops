# NSXT Cloud Data Segment Addition

Playbook Developed by: William Stoneman</br>


## Table of Contents
1.	[Introduction](#Introduction)
1.	[Installation](#Installation)
1.	[Requirements](#Requirements)
1.	[Variable Input File](#Variable-Input-File)
1.	[Execution](#Execution)
1.	[Considerations](#Considerations)




# Introduction

The Purpose of of this Playbook is to configure the intial Data Segment or add additional Data Segments to an exisiting NSX-T Cloud configured on an Avi Cluster. When an NSX-T Cloud Connector is created through the Avi UI, it is required to configure atleast 1 Data Segment. However, when configuring an NSX-T Cloud through vRO you can configure the Cloud without this requirement. This is useful if seperate teams handle the individual parts of the Cloud. Therefore, this Playbook can be run independantly or in conjunction with the NSX-T Cloud Deployment Playbook.

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

* An operational NSX-T CLoud Connector configured on an Avi Cluster.



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

### NSXT Cloud Connector Settings
CLOUD_NAME: *\<NSXT CLoud Connector Name\>*</br>
NSXT_DATA_T1_SEG:  *\<List of Array elements of NSXT Data T1 Segments\>* #Comment if Transport Zone is type VLAN</br>
[*\< - {T1: "<T1 Router Name1>", SEG: "<Segment Name1>"} \>*] #Comment if Transport Zone is type VLAN
[*\< - {T1: "<T1 Router Name2>", SEG: "<Segment Name2>"} \>*] #Comment if Transport Zone is type VLAN
NSXT_DATA_VLAN_SEG: *\<List of Array elements of NSXT Data VLAN Segments\>* #Comment if Transport Zone is type Overlay</br> 
[*\< - {SEG: "Segment Name1>"} \>*] #Comment if Transport Zone is type Overlay
[*\< - {SEG: "Segment Name2>"} \>*] #Comment if Transport Zone is type Overlay


**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Playbook are:

1.	Retrieve Data Segment Information.
2.	Update Data Object Configuration.
3.	Update NSXT Cloud Connector.


**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this Playbook:

*


