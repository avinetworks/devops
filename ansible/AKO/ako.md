#Avi Kubernetes Operator (AKO)  Deployment

Playbook Developed by: William Stoneman</br>


## Table of Contents
1.	[Introduction](#Introduction)
1.	[Installation](#Installation)
1.	[Requirements](#Requirements)
1.	[Variable Input File](#Variable-Input-File)
1.	[Execution](#Execution)
1.	[Example](#Example)      
1.	[Considerations](#Considerations)




# Introduction

The purpose of this Playbook is to configure an Avi Kubernetes Operator in a Kubernetes environment. 

# Installation

The methods used within this Playbook can be found in the Kubernetes (K8S) Collection (kubernetes.core). The following software is required to successfully execute this Playbook:

Ansible server:
- Ansible (tested on Ansible version 2.11 and up)
- kubernetes.core Collection

Remote Kubernetes server:
- Python3 (tested 3.12 and up)
- pip3
- openshift python module (part of playbook deployment)
- pyyaml python module (part of playbook deployment)
- kubernetes python module (part of playbook deployment)


# Requirements

The following prerequisites are required to successfully utilize this Workflow:

* Using the following KB article, determine the appropriate AKO version for the Kubernetes deployment and NSX ALB versions running in your environment. (KB for newest release of AKO 1.11 at time of writting)
  https://docs.vmware.com/en/VMware-NSX-Advanced-Load-Balancer/1.11/Avi-Kubernetes-Operator-Guide/GUID-4EA9A7D3-13F7-42A1-BC5D-FCFB1B1CC0BE.html
  
* Using the following KB article, determine the approriate HELM version for the kubernetes deployment version running in your environment.
  https://helm.sh/docs/topics/version_skew/


**[Back to top](#table-of-contents)**


# Variable-Input-File

The following is a breakdown of the required Variables for this Playbook.

### HELM Variables

HELM_VERSION: <helm version release> #Ex. 3.13.3


### AKO Variables

VALUE_FILE: <ako value file name> #Stored in the root of the workflow project.
CHART_VERSION: <ako version release> #Ex. 1.10.3



**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Playbook are:

1.	Install pre-requisite python modules on remote Kubernetes host.
2.  Install helm on remote Kubernetes host.
3.  Copy over AKO values YAML file from Ansible Host to remote Kubernetes host.
4.  Deploy AKO chart using values files on remote Kubernetes host.


**[Back to top](#table-of-contents)**

# Example

The following is an example of script execution:

`ansible-playbook playbooks/deploy_ako.yaml -i 192.168.130.10, -u ubuntu -k -vvvv`

* Provide the Remote Kubernetes host IP/FQDN in the *-i* parameter. Make sure the include the trailing ','.
* Provide the Remote Kubernetes host Username in the *-u* parameter. This user needs to have Sudoers access to install the required re-requisite python modules.
* The *-k* is used to prompt for the Remote Kubernetes User Password. This is a secured way of providing the password, as it is not stored in plaintext.



**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this Playbook:

* The AKO values YAML file for version 1.11 is included in the root of the workflow project. If a different version of the AKO values YAML file is required, it can be retrieved by running the following command:
  helm show values oci://projects.registry.vmware.com/ako/helm-charts/ako --version [version number] > values.yaml
  
  
* The AKO values YAML file will need to be updated with the required configuration. The following are required fields that need to be updated:
  1. clusterName - A unique identifier for the kubernetes cluster, that helps distinguish the objects for this cluster in the avi controller.
  2. layer7Only - If this flag is switched on, then AKO will only do layer 7 loadbalancing.
  3. nodeNetworkList - Network and cidrs are used in pool placement network for vcenter cloud. Node Network details are not needed when in nodeport mode / static routes are disabled / non vcenter clouds.
  4. vipNetworkList - Network information of the VIP network. Multiple networks allowed only for AWS Cloud. 
  5. ControllerSettings - This section outlines settings on the Avi controller that affects AKO's functionality.
  6. avicredentials - NSX ALB Username and Password.  

    
    

*For a full list of variables please view the following KB article - https://github.com/akshayhavile/load-balancer-and-ingress-services-for-kubernetes/blob/5068a3d4ce5b37895521d967ed239adb0a5d9e94/docs/install/helm.md#parameters*


