# Failed Node Replacement

Playbook Developed by:  William Stoneman</br>


## Table of Contents
1.	[Introduction](#Introduction)
1.	[Installation](#Installation)
1.	[Requirements](#Requirements)
1.	[Variable Input File](#Variable-Input-File)
1.	[Execution](#Execution)
1.	[Considerations](#Considerations)




# Introduction

The purpose of this Playbook is to redeploy a failed Avi Controller Node and reconfigure the Avi Cluster. The playbook will first set the cluster to a single Node cluster using the Leader Node, then deploy an Avi Controller Appliances to the desired vCenter environment, utilizing a remote Linux host running ovftool. The playbook will finally rebuild the cluster using the new Node and the original Leader and second Follower Nodes.

# Installation

The methods used within this Playbook can be found in the Avi Networks Ansible Role (avinetworks.avisdk) or the Avi Networks Ansible Collection (vmware.alb). The following software is required to successfully execute this Playbook:

- Ansible (tested on Ansible version 2.11 and up)
- Avi Networks Ansible Collection (vmware.alb)
- VMWare Ansible Collection (community.vmware)
- Avi Networks Ansible Role (avinetworks.avicontroller_vmware)
- Python requests-toolbelt Utility
- Python pyvmomi Utility
- VMWare OVFTools Utility
- Python requests Utility

# Requirements

The following prerequisites are required to successfully utilize this Workflow:

* An OVA template file for the Avi Controller Appliance. The template file needs to be put in a directory that the Playbook can access.

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

### Vmware vCenter Credentials and Other Parameters
VCENTER_HOST: *\<vCenter FQDN/IP Address\>* # In a VCF environment, provide the Management Domain vCenter Server</br>
VCENTER_USER: *\<vCenter Username\>*</br>
VCENTER_PASSWORD: *\<vCenter User Password\>*</br>
DATACENTER: *\<vCenter Datacenter Name\>*</br>
VMWARE_CLUSTER_NAME: *\<vCenter Cluster Name\>*</br>
VMWARE_DATASTORE: *\<vCenter Datastore Name\>*</br>
CON_FOLDER: *\<vCenter VM Folder Name - Format= *\<Datacenter Name\>*/vm/*\<VM Folder Name\>*\>* #Ex. "datacenter01/vm/Avi"
CON_RESOURCE_POOL: "*\<vCenter VM Resource Pool Name\>*</br>
OVFTOOL_PATH: <OVF Tool Install Path> #Linux Default Install Path is "/usr/bin" -  DownloadLink: https://code.vmware.com/web/tool/4.4.0/ovf

### Controller OVA Image Location
OVA_PATH: <Avi Controller OVA File Path>


**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Playbook are:

1.	Retrieve Cluster Node parameters and Failed Node VM specs.
2.  Set Avi Cluster as a single Node Cluster using Leader Node.
3.  Turn off Failed Node VM and append "-Old" to VM name.
4.  Execute ovftool commands for the new appliance.
5.	Wait for Controller to become ready. Run transient API calls against the “initial-data” API path. Wait for HTTP Response 200.
6.	Initiate Cluster Configuration
7.	Wait for Cluster to be ready.


**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this Playbook:

* The newest release supports NSX ALB 22.x+ and the customization of VM resources (vCPU, RAM and disk space).


