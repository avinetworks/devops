# VMWare - Create NSX ALB Controller Cluster

The playbook will create controller cluster with VIP within VCenter.

## Pre-Requisites to interact with Vmware

- Take notes of the management network you want to utilized.
- VCenter Credentials
- ovftool: https://code.vmware.com/web/tool/4.4.0/ovf
- ansible-galaxy role to deploy and verify controller in vmware: ansible-galaxy install -c avinetworks.avicontroller_vmware 