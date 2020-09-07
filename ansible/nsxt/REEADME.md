### This script wil be responsible for the below resource creation.

  1. NSXT Cloud
  2. Policy API Endpoint
  3. Controller Password Reset
  4. Content-library creation
  5. VCUSER creation
  6. NSX user creation

### To run the Deployment please use the below command:

## Note**: Before running the script please make sure to export the PYTHONPATH and update extra_vars/vars.yaml with relevant password. The script will make sure to install the requirements.
```
   Example:

       ./create.sh -- h
        
       usage:
    
        -h help
        -n nsxt_url_ip
        -r router_mgmt_ip
        -c controller_ip
        -p controller_password
        -v vcenter_ip
    
     e.g,
        export PYTHONPATH=${PWD}:$PYTHONPATH 
        ./create.sh -n nsxt_url_ip -r router_mgmt_ip -c controller_ip -p controller_password -v vcenter_ip
```
