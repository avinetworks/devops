# avi_deploy_horizon

Setup Avi Configuration for Horizon Applications based off Avi KBs.
- [L4L7](https://avinetworks.com/docs/latest/horizon-307-single-vip/)<br>
- [L7N+1](https://avinetworks.com/docs/20.1/horizon-in-n-plus-one-mode-using-307-solution/)<br>
- [CS](https://avinetworks.com/docs/latest/configure-avi-vantage-for-vmware-horizon/#connection)

The playbooks will deploy Avi VirtualService and it's dependencies configuration.  Any ConnectionServer/UAG configuration will have to be done separately.

## Requirements

```bash
pip install avisdk
ansible-galaxy collection install vmware.alb
```

## Variables

The variables control what usecase gets deployed, currently the following usecases are supported:<br>
[L4L7](https://avinetworks.com/docs/latest/horizon-307-single-vip/)<br>
[L7N+1](https://avinetworks.com/docs/20.1/horizon-in-n-plus-one-mode-using-307-solution/)<br>
[CS](https://avinetworks.com/docs/latest/configure-avi-vantage-for-vmware-horizon/#connection)

```yaml
DEPLOYMENT_TYPE: <usecase>
```

Also other variables to help customize the applications
```yaml
VS_SSLCERT: <certkey-profile-name>   # Custom SSL Certificate for the VirtualService
VS_IPADDR: <IP Address>              # IP Address for your VirtualService
SERVERS_FQDN_IP:                     # List of dictionaries with server information (FQDN Required for L4L7 usecase)
  - ip: <ip of backendserver>
    fqdn: <fqdn of backendserver>
```

### Unified Access Gateway
To Setup UAG Configuration using L4L7 Deployment on custom Tenant/Cloud and ServiceEngineGroup on Avi Loadbalancer<br>
[Avi KB Reference for L4L7 Deploy](https://avinetworks.com/docs/latest/horizon-307-single-vip/)
```yaml
CLOUD_NAME: VMware-Cloud
TENANT_NAME: uag-ca01
SEG_NAME: UAG_SEG

DEPLOYMENT_TYPE: L4L7
DEPLOYMENT_NAME: EXT_UAG

VS_IPADDR: 10.10.10.10
VS_SSLCERT: testself
SERVERS_FQDN_IP:
  - ip: 1.1.1.1
    fqdn: uag1.vsvip.int
  - ip: 2.2.2.2
    fqdn: uag2.vsvip.int
```

### Connection Server
To Setup Connection Server Configuration on Avi Loadbalancer <br>
[Avi KB Reference for CS Deploy](https://avinetworks.com/docs/latest/configure-avi-vantage-for-vmware-horizon/#connection)
```yaml
CLOUD_NAME: Default-Cloud
TENANT_NAME: admin
SEG_NAME: Default-Group

DEPLOYMENT_TYPE: CS
DEPLOYMENT_NAME: INT_CS

VS_IPADDR: 10.10.10.11
VS_SSLCERT: testself
SERVERS_FQDN_IP:
  - ip: 1.1.1.1
  - ip: 2.2.2.2
```

## Example Playbook

```yaml
- hosts: localhost
  connection: local
  gather_facts: false
  vars:
    AVI_CREDENTIALS:
      controller: 10.10.10.10
      username: "admin"
      password: "VMware1!"
      api_version: "20.1.6"
  tasks:
  - import_role:
      name: avi_deploy_horizon
    vars:
      vars_file: example_uag_vars.yml
    name: Build UAG Virtual Service on Avi
  - import_role:
      name: avi_deploy_horizon
    vars:
      vars_file: example_cs_vars.yml
    name: Build CS Virtual Service on Avi
```
