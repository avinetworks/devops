### This script wil be responsible for the below resource creation.

  1. NSXT Cloud
  2. Policy API Endpoint
  3. Controller Password Reset
  4. Content-library creation
  5. VCUSER creation
  6. NSX user creation
  7. Route Table Entry

## Minimal Requirements To Run The Script
   1. Ansible (version => 2.7)
   2. Ansible default python version should be python3
   3. Python3 >= 3.7
   4. Export PYTHONPATH

### To run the Deployment please use the below command:
```
    e.g,
        ./setup.sh
``` 
   ## `setup.sh` script will responsible to setup all requirements to run the create.sh except EXPORT PYTHONPATH.

## Note**: Before running the script please make sure to export the PYTHONPATH and update extra_vars/vars.yaml with relevant password.
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
        -a apiVersion
    
     e.g,
        export PYTHONPATH=${PWD}:$PYTHONPATH 
        ./create.sh -n nsxt_url_ip -r router_mgmt_ip -c controller_ip -p controller_password -v vcenter_ip -a apiVersion
```

### Known Issue.

   1. After running setup.sh if ansible found missing, please run the below command.
       `export PATH=$PATH:$HOME/.local/bin`
   2. Any error on Module not found run the below command.
       `export PYTHONPATH=${PWD}:$PYTHONPATH`
