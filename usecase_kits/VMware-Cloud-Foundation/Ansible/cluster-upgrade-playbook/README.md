# Cluster Upgrade

Playbook Developed by:  Juan Aristizabal and William Stoneman</br>


## Table of Contents
1.	[Introduction](#Introduction)
1.	[Installation](#Installation)
1.	[Requirements](#Requirements)
1.	[Variable Input File](#Variable-Input-File)
1.	[Execution](#Execution)
1.	[Considerations](#Considerations)




# Introduction

The purpose of this Playbook is to upgrade an AVI Cluster. The Workflow will first initiate the upload of the upgrade packages(s), based on the upgrade path selected. We offer the following 3 Upgrade paths:

* Base Image Upgrade Only
* Patch Image Upgrade Only
* Base and Patch Image Upgrade

# Installation

The methods used within this Playbook can be found in the Avi Networks Ansible Role (avinetworks.avisdk) or the Avi Networks Ansible Collection (vmware.alb). The following software is required to successfully execute this Playbook:

- Ansible (tested on Ansible version 2.11 and up)
- Avi Networks Ansible Collection (vmware.alb)
- Avi Networks Ansible Role (avinetworks.avicontroller_vmware)
- Python requests-toolbelt Utility
- Python pyvmomi Utility
- Python requests Utility

# Requirements

The following prerequisites are required to successfully utilize this Workflow:

* The upgrade package(s) based on the upgrade path selected. The upgrade file(s) needs to be put in a directory that the Playbook can access.



**[Back to top](#table-of-contents)**


# Variable-Input-File

The following is a breakdown of the required Variables for this Playbook.

### Cluster IP for Avi Controller
CONTROLLER_CLUSTER_IP: <Controller Cluster/Node IP> # This can be either cluster ip or the ip of the leader controller.

### Controller Credentials
AVI_CREDENTIALS:
  controller: *\<CONTROLLER_CLUSTER_IP\>*</br> 
  username: *\<Avi Username\>*</br>
  password: *\<Avi User Password\>*</br>
  api_version: *\<Avi Controller Version\>* #Ex. "22.1.3"

### Upgrade files info
BASE_UPGRADE_FILE: *\<Base Upgrade Package File Location\>*</br>
BASE_UPGRADE_VERSION: *\<Base Upgrade Package Version\>* #Ex. 22.1.3</br>
PATCH_UPGRADE_FILE: *\<Patch Upgrade Package File Location\>*</br>
PATCH_UPGRADE_VERSION: *\<Patch Upgrade Package Version\>* #Ex. 2p1



**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Playbook are:

1.	Determine Upgrade Path.
2.	Based on Upgrade Path, upload upgrade package(s). 
3.	Retrieve Cluster Leader IP Address and current firmware version.
4.	Initiate Cluster upgrade based on upgrade path selected.
5.	Process Upgrade validation for Controller Cluster nodes. Wait for upgrade to complete Successfully.


If the Cluster nodes encounter an error during the upgrade process, the Playbook will fail. The end User will need to manually resolve the issue and continue the upgrade. 


**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this Playbook:

* Another configuration decision that needs to be taken into consideration before running the Playbook, is the HA model selected for the SE group hosting the Virtual Services. If HA mode N+M in Buffer Mode is used, then the Virtual Services will be running on a single SE. When the SE is upgraded, the Virtual Services hosted on that SE will go down. We contemplated allowing the end user to select that the Virtual Services get scaled out, however we decided against that in the end. We felt that there were a lot of factors to consider in allowing for that configuration, and if the end user wanted to scale out the Virtual Services, it should be done manually.


