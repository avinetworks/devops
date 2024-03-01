# Remote Authentication Configuration

Playbook Developed by:  William Stoneman</br>


## Table of Contents
1.	[Introduction](#Introduction)
1.	[Installation](#Installation)
1.	[Requirements](#Requirements)
1.	[Variable Input File](#Variable-Input-File)
1.	[Execution](#Execution)
1.	[Considerations](#Considerations)




# Introduction
The purpose of this Playbook is to configure a LDAP or SAML Authentication Profile. The playbook will also allow for the configuration of group mapping for remote group authentication.

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

* Configuration properties for either an remote LDAP or SAML authentication source.


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


### SAML Configuration Parameters
SAML_PROF_NAME: *\<SAML Profile Name\>*</br>
SAML_METADATA: *\<SAML Metadata\>*</br>
SAML_ENTITY_TYPE: *\<SAML Entity Type - AUTH_SAML_CLUSTER_VIP / AUTH_SAML_DNS_FQDN / AUTH_SAML_APP_VS \>* #Can be "AUTH_SAML_CLUSTER_VIP" or "AUTH_SAML_DNS_FQDN" or "AUTH_SAML_APP_VS" </br>
SAML_ORG_NAME: *\<SAML ORG Name\>* #If SAML_ENTITY_TYPE is set to "AUTH_SAML_APP_VS" then connent this line. </br>
SAML_DISPLAY_NAME: *\<SAML Display Name\>* #If SAML_ENTITY_TYPE is set to "AUTH_SAML_APP_VS" then connent this line. </br>
SAML_ORG_URL: *\<SAML ORG URL\>* #If SAML_ENTITY_TYPE is set to "AUTH_SAML_APP_VS" then connent this line. </br>
TECH_CONTACT_NAME: *\<Tech Contact Name\>* #If SAML_ENTITY_TYPE is set to "AUTH_SAML_APP_VS" then connent this line. </br>
TECH_CONTACT_EMAIL: *\<Tech Contact Email\>* #If SAML_ENTITY_TYPE is set to "AUTH_SAML_APP_VS" then connent this line. </br>
SAML_FQDN: *\<SAML FQDN\>* #If SAML_ENTITY_TYPE is set to "AUTH_SAML_CLUSTER_VIP" or "AUTH_SAML_APP_VS" then connent this line. </br>

### LDAP Configuration Parameters
LDAP_PROF_NAME: *\<CONTROLLER_CLUSTER_IP\>*</br>
LDAP_SERVER: [*\<Comma Seperated FQDN/IP List\>*] #Ex. [1.1.1.1,2.2.2.2,3.3.3.3] or [ad1.avi.com,ad2.avi.com]</br>
LDAP_PORT: *\<LDAP Port\>*</br>
LDAP_SEC_MODE: *\<LDAP Security Mode - AUTH_LDAP_SECURE / AUTH_LDAP_SECURE_NONE \>* #Can be "AUTH_LDAP_SECURE" or "AUTH_LDAP_SECURE_NONE" <br>
BASE_DN: *\<LDAP Base DN\>*</br>
ADMIN_BIND_DN: *\<LDAP Admin Bind DN\>*</br>
ADMIN_BIND_PASSWORD: *\<LDAP Bind Password\>*</br>
USER_SEARCH_DN: *\<User Search DN\>*</br>
USER_SEARCH_SCOPE: *\<User Search Scope - AUTH_LDAP_SCOPE_BASE / AUTH_LDAP_SCOPE_ONE / AUTH_LDAP_SCOPE_SUBTREE \>* #Can be "AUTH_LDAP_SCOPE_BASE" or "AUTH_LDAP_SCOPE_ONE" or "AUTH_LDAP_SCOPE_SUBTREE" <br>
USER_ID_ATTRIBUTE: *\<User ID Attribute\>*</br>
GROUP_SEARCH_DN: *\<Group Search DN\>*</br>
GROUP_MEM_ATTR: *\<Group Member Attribute\>* # Default is set to "member" </br>
GROUP_SEARCH_SCOPE: *\<User Search Scope - AUTH_LDAP_SCOPE_BASE / AUTH_LDAP_SCOPE_ONE / AUTH_LDAP_SCOPE_SUBTREE \>* #Can be "AUTH_LDAP_SCOPE_BASE" or "AUTH_LDAP_SCOPE_ONE" or "AUTH_LDAP_SCOPE_SUBTREE" <br>
GROUP_MEM_FULL_DN: *\<Group Member Full DN\>* # Default is set to true </br>
GROUP_FILTER: *\<Group Filter\>* # Default is set to "(objectClass=*)" </br>
IGNORE_REF: *\<Ignore Ref\>* # Default is set to false </br>

### Auth Mapping Parameters
AUTH_MAPPING: *\<\>* #List of Group Mapping array elements" <br>
[*\<Comma Seperated Group Mapping List\>*] #Ex. - {group: "<LDAP Group Name>", tenant: "<Avi Tenant Name>", role: "<Avi Role Name>"}</br> 


**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Playbook are:

1.	If SAML Profile is being created
   1. 	Define SAML object based on SAML_ENTITY_TYPE.
   1. 	Create SAML Profile   
2.	If LDAP Profile is being created
   2. 	Create LDAP Profile
3.	Assign Auth Profile to System Configuration and define Group Mapping.


**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this Playbook:

* By default the Playbook only creates a single Group Mapping. If additional Group Mappings are required, then additional array elements are required in the variables file, as well as additional Index elements will need to be added to the Assign Policy and Group Mapping section of the remote_auth playbook. 


