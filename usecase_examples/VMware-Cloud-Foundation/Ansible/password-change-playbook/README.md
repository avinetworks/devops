# Password Change

Playbook Developed by:  Juan Aristizabal and William Stoneman</br>


## Table of Contents
1.	[Introduction](#Introduction)
1.	[Installation](#Installation)
1.	[Requirements](#Requirements)
1.	[Variable Input File](#Variable-Input-File)
1.	[Execution](#Execution)
1.	[Considerations](#Considerations)




# Introduction

The purpose of this Playbook is to allow the end user to change the password for ANY AVI User, NSX-T Cloud connector Credential Object or vCenter Cloud connectory Credential Object. The Playbook, allows you to specify if you want to update an Avi user password or an NSX-T Cloud Connector, or both.

# Installation

The methods used within this Playbook can be found in the Avi Networks Ansible Role (avinetworks.avisdk) or the Avi Networks Ansible Collection (vmware.alb). The following software is required to successfully execute this Playbook:

- Ansible (tested on Ansible version 2.11 and up)
- Avi Networks Ansible Collection (vmware.alb)
- Python requests Utility

# Requirements

There are no pre requisite configuration requirements for this Workflow.



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

### NSX-T and vCenter Credentials Information
NSXT_CLOUDCONNECTORUSER: <NSX-T Cloud Connector User Object Name> #If only changing vCenter password then comment line.
NSXT_PASSWORD: <New NSX-T Cloud Connector Password> #If only changing vCenter password then comment line.
NSXT_VCENTER_CLOUDCONNECTORUSER: <vCenter Cloud Connector User Object Name> #If only changing NSX-T password then comment line.
NSXT_VCENTER_PASSWORD: <New vCenter Cloud Connector Password> #If only changing NSX-T password then comment line.

### Avi User Credentials Information
AVI_USER: *\<Avi Username\>*</br>
AVI_PASSWORD: *\<New Avi User Password\>*</br>
AVI_ADMIN_CURRENT_PASSWORD: <Current Avi admin Password> #If not updating admin password then comment line.

**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Playbook are:

1. Decision – Change NSX-T Cloud Connector password?
   1. 	Yes – Change NSX-T Cloud Connector password based on provided information.
   1. 	No – Continue with Playbook.
1. Decision – Change vCenter Cloud Connector password?
   1. 	Yes – Change vCenter Cloud Connector password based on provided information.
   1. 	No – Continue with Playbook.
1. Decision – Change Avi User password?
   1. 	Yes – Change Avi User password based on previded information.
   1. 	No – End Playbook. 


* If the NSX-T Cloud Connector password change failed, the Playbook will fail, and the end user will need to validate the provided information.

* If the vCenter Cloud Connector password change failed, the Playbook will fail, and the end user will need to validate the provided information.

* If the Avi User password change failed, the Playbook will fail, and the end user will need to validate the provided information.


**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this Playbook:

* We are relying on the positive response of the password change, that the operation was successful. In the case of the Avi user, there is not a way to validate the password change was successful. Therefore, we leave it up to the end user to validate the user account is still accessible.

* For the NSX-T Cloud Connector change, we again rely on the positive response of the password change, that the operation was successful. Therefore, we assume the end user is updating the Object with the correct password.


