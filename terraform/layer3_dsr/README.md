# Terraform example of Avi Networks 2-tier Layer 3 DSR design

This Terraform code will build the Service Engine Groups, Virtual Services, and Pools necessary to implement the 2 Tier Layer 3 DSR design shown in this [document](https://avinetworks.com/docs/latest/direct-server-return/) with the Service Engine group configured for per-app SEs and the Virtual Services configured for BGP route injection.
## Dependencies
- Python 3.6+ for f-string support
- Python Requests module
- Terraform 0.14

This assumes that you have a network profile pre-configured named "L3DSR" for the Virtual Services to use.

### !!You will not be able to "terraform destroy" this environment, due to Avi's orchestration of the Service Engines. 

---

### Required Terraform Variables


|Variable Name|Description|
|-------------|-----------|
|`avi_username`|Controller username|
|`avi_password`|Controller password|
|`avi_tenant`|The tenant where the Virtual Services will be placed|
|`avi_version`|The version of the controller, for API versioning.|
|`avi_controller`|FQDN or IP address of the Avi controller|
|`tier_1_vrf`|Name of the Tier 1 VRF|
|`tier_2_vrf`|Name of the Tier 2 VRF|
|`back_end_subnet`|The subnet containing the servers and back end SEs (string)|
|`back_end_subnet_mask`|Subnet mask of the back end subnet in slash notation (integer, ex. 24)|
|`t1_portgroup`|Name of the port group associated with the Tier 1 subnet|
|`t2_portgroup`|Name of the port group associated with the Tier 2 subnet|
|`front_end_subnet`|The subnet containing the servers and back end SEs (string)|
|`front_end_subnet_mask`|Subnet mask of the back end subnet in slash notation (integer, ex. 24)|
|`webserver1_ip`|IP address of the first webserver (string)|
|`webserver2_ip`|IP address of the second webserver (string)|
|`avi_cloud`|Name Avi cloud object that the Virtual Services will be associated with|
|`vip_portgroup`|Name of the port group associated with the VIP subnet|
|`vip_subnet`|The subnet range for the VIPs (string)|
|`vip_subnet_mask`|Subnet mask of the VIP subnet in slash notation (integer, ex. 24)|
|`app_name`|The application name, used for naming objects (Must only be letters, numbers, or underscore)|



