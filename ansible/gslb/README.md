
# 1. Introduction
These ansible playbooks are meant for GSLB infrastructure day 1 deployment with multiple sites and day 2 operation maintainence in vSphere cloud, as well as GSLB services. It's an example of Avi's Infrastructure as code.

# 2. GSLB Site Deployment and Operation Maintainence
It includes one main playbook (*deploy_gslb_site.yml*) and a GSLB site configuration example(*gslb_site_config.yml*), as well as 5 subtask files under the tasks folder. 


## Subtasks:
- **[gslb_role.yml](tasks/gslb_role.yml)**  
This playbook loops through all the Avi sites listed in the *gslb_site_config.yml* file and check whether the gslb role specified in the configuration file exists in the Avi controller. If not, it will create the gslb role in the Avi controller. The new role will have write permission to GSLB and GSLB Geo Profile, as well as read access to virtual services and tenants. If there's already a role with the same name, the playbook will not make change to the role to avoid causing any issues. Please make sure the existing role has the proper permission for GSLB. 

- **[gslb_user.yml](tasks/gslb_user.yml)**  
This playbook loops through all the Avi sites listed in the *gslb_site_config.yml* file and check whether the gslb user specified in the configuration file exists in the Avi controller. If not, it will create the gslb user under admin tenant with the aformentioned gslb role in the Avi controller. If the user already exists, the playbook will not make change.

- **[gslb_seg.yml](tasks/gslb_seg.yml)**  
This playbook loops through all the Avi sites listed in the *gslb_site_config.yml* file. If an Avi site is defined as active member and a GSLB dedicated service engine group is defined, the playbook will check whether such SEG exists in the controller. If not, it will create the SEG. <u>Please be noted that GSLB DNS VSes should use dedicated service engine group as best practise.</u> 

- **[gslb_dns_vs.yml](tasks/gslb_dns_vs.yml)**  
This playbook loops through all the Avi sites listed in the *gslb_site_config.yml* file, and check whether those specified DNS virtual service(s) exists in the active Avi sites. If not, it will create those DNS virtual service according to the defined configuration. The DNS VS will be configured to support both TCP and UDP, following best practise. If ctrl_dnsservice key is defined as true, the DNS VS will also be added to the controller's DNS service list. <u>This is not mandatory but as best practise, we suggest to add those DNS VS(es) to Avi controller's DNS service list.</u> Please be noted that this Ansible playbook does not remove any DNS VS from Avi controllers' DNS service list. You will need a dedicated playbook for your Avi controller's system configuration to do that. 

- **[gslb_site.yml](tasks/gslb_site.yml)**  
This playbook read through the entire *gslb_site_config.yml* file, will create or modify the GSLB infrastructure with active sites, passive sites, third party sites as defined in the configuration file.

## GSLB Infra Deployment playbook:
- **[deploy_gslb_site.yml](./deploy_gslb_site.yml)**  
It's the main playbook to read GSLB site configuration and invoke the 5 sub tasks to deploy gslb infrastructure or make change to an existing gslb infra.  You can also manually run it with tags option to invoke each task individually for testing purpose. 
```
ansible-playbook deploy_gslb_site.yml -e "site_config=./gslb_site_config.yml" 

ansible-playbook deploy_gslb_site.yml  -e "site_config=./gslb_site_config.yml" --tags gslb_role|gslb_user|gslb_seg|gslb_dns_vs|gslb_site
```


## GSLB Site Configuration Example
- **[gslb_site_config.yml](./gslb_site/gslb_site_config.yml)**  
This's the configuration file containing all the information of GSLB infrastructure. Please refer to the file for details.   


# 3. GSLB Service Deployment and Operation Maintainence
It includes one main deploy playbook (*deploy_gslb_service.yml*) and a GSLB service configuration example(*webservice.yml*).

## GSLB Service Deployment playbook:
- **[deploy_gslb_service.yml](./deploy_gslb_service.yml)**  
It's the main playbook to read GSLB service configuration and then deploy a new gslb service or make change to an existing gslb service.
```
ansible-playbook deploy_gslb_service.yml -e "gslbservice=./gslb_services/webservice.yml"
```

## GSLB Service Example
- **[webservice.yml](./gslb_services/webservice.yml)**  
This's an example of GSLB service configuration yaml file. Please refer to the file for details.  

# Requirement
These ansible playbooks were tested under the following environments:   
- Ansible  
*ansible core >= 2.12.3*  
- Ansible collections  
*vmware.alb ==  22.1.1/30.1.1*   
*ansible.netcommon == 6.0.0*
- Python and other modules  
*python3 == 3.8.16/3.11.2*  
*avisdk == 22.1.1/30.1.1*
*netaddr == 0.10.1*
- Avi Controller  
*Avi == 22.1.5/30.1.1*  
- CMDs to install those packages
```
python3 -m pip install avisdk==30.1.1
python3 -m pip install netaddr==0.10.1
python3 -m pip install ansible-core==2.16.2
ansible-galaxy collection install vmware.alb:==30.1.1
ansible-galaxy collection install ansible.netcommon:==6.0.0
```

