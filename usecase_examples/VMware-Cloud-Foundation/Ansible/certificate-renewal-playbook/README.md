# Certificate Renewal

Playbook Developed by:  Juan Aristizabal and William Stoneman</br>


## Table of Contents
1.	[Introduction](#Introduction)
1.	[Installation](#Installation)
1.	[Requirements](#Requirements)
1.	[Variable Input File](#Variable-Input-File)
1.	[Execution](#Execution)
1.	[Considerations](#Considerations)




# Introduction

The purpose of this Playbook is to provide the ability to replace Application or Controller certificates that were generated using the CSR method on the Avi Controller.

# Installation

The methods used within this Playbook can be found in the Avi Networks Ansible Role (avinetworks.avisdk) or the Avi Networks Ansible Collection (vmware.alb). The following software is required to successfully execute this Playbook:

- Ansible (tested on Ansible version 2.11 and up)
- Avi Networks Ansible Collection (vmware.alb)
- Python requests-toolbelt Utility
- Python requests Utility

# Requirements

This Playbook has been tested against renewing certificate Objects for both Application and Controller certificates generated using the built in CSR process on the Avi Controller.



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

### New Certificate file
CERT_NAME: *\<Certificate Object Name\>*</br>
NEW_CERT_FILE: *\<Certificate file location\>*</br>


**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Playbook are:

1.	Replace the Certificate element field of the specified certificate Object.

If the certificate renewal failed, the Playbook will fail, and the end user will need to validate the provided information.


**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this Playbook:

* There is no way for the Playbook to validate that the provided certificate text is valid for the selected Certificate Object. Therefore, we assume the end user has validated that the provided text is correct.

* We are relying on the positive response of the Certificate Object update, that the operation was successful. Therefore, we leave it up to the end user to validate the Controller accessibility.


