# Cluster Deployment

Playbook Developed by:  Yuriy Andrushko and William Stoneman</br>


## Table of Contents
1.	[Introduction](#Introduction)
1.	[Installation](#Installation)
1.	[Requirements](#Requirements)
1.	[Variable Input File](#Variable-Input-File)
1.	[Execution](#Execution)
1.	[Considerations](#Considerations)




# Introduction

The purpose of this Terraform Script is to deploy an AVI 3 Node Controller Cluster and configure all required settings to bring it to a stable usable state. The Script will first initiate the deployment of 3 Avi Controller Appliances to the desired vCenter environment, utilizing a template stored on a Content Library.  The Script will then configure the following required settings: 

* Change Default Admin Password
* DNS Servers 
* NTP Servers 
* Local SMTP Configuration 
* Local Backup Configuration 



# Installation

The methods used within this Terraform Script can be found in the Avi Networks Terriform Provider (vmware/avi). The following software is required to successfully execute this Terraform Script:

Terraform (tested on Terraform version 1.1.0 and up)

# Requirements

The following prerequisites are required to successfully utilize this Workflow:

* An OVA template file for the Avi Controller Appliance. The template file needs to be uploaded to a COntent Library created on the destination vCenter.


**[Back to top](#table-of-contents)**


# Variable-Input-File

The following is a breakdown of the required Variables for this Terraform Script.

vsphere_user.default = *\<vSphere Username\>*

vsphere_password.default = *\<vSphere Password\>*

vsphere_server.default = *\vSphere Server IP/FQDN\>*

datacenter_name.default = *\<Datacenter Name\>*

cluster_name.default = *\<Cluster Name\>*

datastore_name.default = *\<Datastore Name\>*

dvs_name.default = *\<DVS Name\>*

mgmt_net_name.default = *\<Management Network Port Group Name\>*

Controller_vm_name.default = *\<Avi Controller VM Name List (Ex. ["avi-tf-01", "avi-tf-02","avi-tf-03"]\>*

vsphere_resource_pool.default = *\<Resource Pool Name\>*

vm_folder.default = *\<Folder Name\>*

avi_username.default = *\<Avi Username\>*

avi_new_password.default = *\<NEW Avi Admin Password\>*

avi_version.default = *\<Avi Controller Version (Ex. "20.1.8")\>*

avi_ctrl_mgmt_ips.default = *\<Avi Controller Management Network IP Addresse List (Ex. ["10.10.10.10", "10.10.10.11","10.10.10.12"]) \>* 

subnetMask.default = *\<Management Network Subnet Mask\>*

defaultGateway.default = *\<Management Network Default Gateway\>*

clustervip.default = *\<Cluster VIP IP Address\>*

backup_passphrase.default = *\<Backup Passphrase\>*

system_dnsresolvers.default = *\<DNS Server IP Addresses List (Ex. ["8.8.8.8", "8.8.4.4"]) \>*

system_ntpservers.default = *\<NTP Server List (Ex. ["0.us.pool.ntp.org", "1.us.pool.ntp.org"]) \>*



**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Playbook are:

1.	Execute Content Library Deployment for the 3 appliances.
2.	Wait for Controllers to become ready. Run transient API calls against the 3 Controllers. Wait for HTTP Response 200.
3.	Initiate Cluster Configuration
4.	Wait for Cluster to be ready.
5.	Configure Backup Configuration settings.
6.	Configure System Configuration settings.
7.	Update admin default password..

If the Actions steps 2-7 fail, the remaining Cluster Deployment steps will need to be executed manually.


**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this Terraform Script:

* In this version of the workflow, we are deploying the Controllers utilzing a Content Library Template. We will be releasing another version of this script that utilizes OVFTool local template deployment.

* In this version of the workflow, we are deploying the Controllers using the default "small" sizing (8 vCPU/ 24 GB with 128 GB of disk space). If you want to change the sizing of the controllers, you will need to update the num_cpus, memory and disk.size parememters in the vsphere_virtual_machine.controller Resource.

* In this version of the workflow, we do not support Licensing Configuration and license upload or Cloud Services Registration will need to be done manually. We will be updating this script to include License Configuration and Cloud Services Registration.

* In this version of the workflow, we only support Local Backup and SMTP configuration. We will be updating this script to include Remote and S3 Backup Configuration, as well as Remote SMTP configuration.

