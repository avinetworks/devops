# Cluster Deployment

Playbook Developed by:  Juan Aristizabal and William Stoneman</br>


## Table of Contents
1.	[Introduction](#Introduction)
1.	[Installation](#Installation)
1.	[Requirements](#Requirements)
1.	[Variable Input File](#Variable-Input-File)
1.	[Execution](#Execution)
1.	[Considerations](#Considerations)




# Introduction

The purpose of this Playbook is to deploy an AVI 3 Node Controller Cluster and configure all required settings to bring it to a stable usable state. The Playbook will first initiate the deployment of 3 Avi Controller Appliances to the desired vCenter environment, utilizing a remote Linux host running ovftool.  The Playbook will then configure the following required settings: 

* Change Default Admin Password
* DNS Servers 
* NTP Servers 
* SMTP Configuration 
* Local/Remote Backup Configuration 
* Licensing Configuration

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

* For the license configuration, either a Avi Networks License YML file or a VMWare License Key is required.



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

### Controller Name and IP Addresses
CONTROLLER_IP_1: *\<Node 1 IP Address\>*</br>
CONTROLLER_NAME_1: *\<Node 1 Name\>*</br>
CONTROLLER_IP_2: *\<Node 2 IP Address\>*</br>
CONTROLLER_NAME_2: *\<Node 2 Name\>*</br>
CONTROLLER_IP_3: *\<Node 3 IP Address\>*</br>
CONTROLLER_NAME_3: *\<Node 3 Name\>*</br>
CLUSTER_NAME: *\<Avi Cluster Name> #Ex. "cluster01"

### Controller Default Password
OLD_PASSWORD: "58NFaGDJm(PJH0G" #Found on download image page

### Controller Configuration Details
DNS_SERVERS: [*\<Comma Seperated IP List\>*] #Ex. [1.1.1.1,2.2.2.2,3.3.3.3]</br>
NTP_SERVERS: [*\<Comma Seperated FQDN/IP List\>*] #Ex. [1.1.1.1,2.2.2.2,3.3.3.3] or [dns1.avi.com,dns2.avi.com]</br>
NTP_TYPE: *\<Object Type\>*  #If servers are hostname use type "DNS", if IP use type "V4" </br>
BACKUP_PASSPHRASE: *\<Backup Passphrase\>*</br>
REMOTE_BACKUP_USER: <Remote Backup User\>* #Username on destination server </br>
REMOTE_BACKUP_PASSWORD: *\<Remote Backup User Password\>*</br>
BACKUP_TO_REMOTE_HOST: *\<no/yes\>* #If Backu to Remote Host then use yes. Otherwise, if Backup to Localhost then use no.</br>
REMOTE_BCKUP_DIR: *\<Remote Backup Directory\>* #Ex "/root"</br>
REMOTE_BACKUP_HOST: *\<Remote Backup Host IP Address\>*</br>
LICENSE_FILE: *\<Avi License File Location\>* #If using VMWare License Key then comment this line.</br>
SERIAL_KEY: *\<VMWare License Key\>* #If using Avi License File then comment this line.</br>
SMTP_SERVER_TYPE: *\<SMTP Server Type - SMTP_LOCAL_HOST / SMTP_SERVER\>* #Can be either "SMTP_LOCAL_HOST" or "SMTP_SERVER"</br>
SMTP_FROM_EMAIL: *\<SMTP From Email Address\>*</br>
SMTP_SERVER_NAME: *\<SMTP Remote Server Name\>* #If SMTP_SERVER_TYPE is set to "SMTP_LOCAL_HOST" then comment this line.</br>
SMTP_SERVER_PORT: *\<SMTP Remote Server Port\>* #If SMTP_SERVER_TYPE is set to "SMTP_LOCAL_HOST" then comment this line.</br>
SMTP_USERNAME: *\<SMTP Remote Server Username\>* #If SMTP_SERVER_TYPE is set to "SMTP_LOCAL_HOST" then comment this line.</br>
SMTP_PASSWORD: *\<SMTP Remote Server User Password\>* #If SMTP_SERVER_TYPE is set to "SMTP_LOCAL_HOST" then comment this line.</br>
SMTP_DISABLE_TLS: *\<Disable SMTP TLS - true / false\>*</br>

### Controller Management Network Setup
CON_MGMT_PORTGROUP: *\<vCenter Port Group Name\>*</br>
CON_MGMT_MASK: *\<Avi Controller Node Network Mask\>*</br>
CON_DEFAULT_GW: *\<Avi Controller Node Default Gateway\>*</br>

### Vmware vCenter Credentials and Other Parameters
VCENTER_HOST: *\<vCenter FQDN/IP Address\>* # In a VCF environment, provide the Management Domain vCenter Server</br>
VCENTER_USER: *\<vCenter Username\>*</br>
VCENTER_PASSWORD: *\<vCenter User Password\>*</br>
DATACENTER: *\<vCenter Datacenter Name\>*</br>
VMWARE_CLUSTER_NAME: *\<vCenter Cluster Name\>*</br>
VMWARE_DATASTORE: *\<vCenter Datastore Name\>*</br>
CON_FOLDER: *\<vCenter VM Folder Name - Format= *\<Datacenter Name\>*/vm/*\<VM Folder Name\>*\>* #Ex. "datacenter01/vm/Avi"
OVFTOOL_PATH: <OVF Tool Install Path> #Linux Default Install Path is "/usr/bin" -  DownloadLink: https://code.vmware.com/web/tool/4.4.0/ovf

### Controller OVA Image Location
OVA_PATH: <Avi Controller OVA File Path>


**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Playbook are:

1.	Execute ovftool commands for the 3 appliances.
2.	Wait for Controllers to become ready. Run transient API calls against the “initial-data” API path. Wait for HTTP Response 200.
3.	Update admin default password.
4.	Configure System Configuration settings.
5.	Configure Backup Configuration settings.
6.	Initiate Cluster Configuration
7.	Wait for Cluster to be ready.
8.	Configure Licensing.

If the Actions steps 3-8 fail, the remaining Cluster Deployment steps will need to be executed manually.


**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this Playbook:

* The newest release supports NSX ALB 22.x+ and the customization of VM resources (vCPU, RAM and disk space).


