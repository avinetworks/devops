# Avi Networks GSLB Topology Deployment

This script can be used to deploy avi gslb topology configuration to one or many avi controllers.

## Variables
/vars/dns_topology_policy.yaml - Define rules used for topology policy

Example with a single rule:
```
dns_topology_policies:
  - ipaddrgroup_name: region-site-1
    topology_rule_name: regional-policy-site-1-rule
    topology_rule_index: 1
    preferred_site: gslb-1b
    fallback_sites:
      - thirdparty-site1
      - thirdparty-site2
      - thirdparty-site3
    prefixes:
      - ip: 10.0.0.0
        mask: 8
```

Example with multiple rules:
```
dns_topology_policies:
  - ipaddrgroup_name: region-site-1
    topology_rule_name: regional-policy-site-1-rule
    topology_rule_index: 1
    preferred_site: gslb-1b
    fallback_sites:
      - thirdparty-site1
      - thirdparty-site2
      - thirdparty-site3
    prefixes:
      - ip: 10.0.0.0
        mask: 8
  - ipaddrgroup_name: region-site-2
    topology_rule_name: regional-policy-site-2-rule
    topology_rule_index: 2
    preferred_site: gslb-1c
    fallback_sites:
      - thirdparty-site3
      - thirdparty-site2
      - thirdparty-site1
    prefixes:
      - ip: 50.0.0.0
        mask: 8
```

/vars/gslb_site_vars.yaml - Define rules used for topology policy

Example with a single gslb site (use the cluster floating management IP/FQDN)
```
gslb_sites:
  - controller: 10.10.10.10
    name: gslb-1a
    api_version: 18.2.8
    cloud_name: Default-Cloud
    tenant_name: admin
    vs_name: dns-vip
```

Example with a multiple gslb sites (use the cluster floating management IP/FQDN)
```
gslb_sites:
  - controller: 10.10.10.10
    name: gslb-1a
    api_version: 18.2.8
    cloud_name: Default-Cloud
    tenant_name: admin
    vs_name: dns-vip
  - controller: 10.10.10.11
    name: gslb-1a
    api_version: 18.2.8
    cloud_name: Default-Cloud
    tenant_name: admin
    vs_name: dns-vip
```

/vars/creds.yaml - Define rules used for topology policy
```
avi_controller_username: avi-username - Replace with your username
avi_controller_password: avi-test-password - Replace with your password
```

## Usage
It is recommended that you always use an encrypted vault. The creds.yaml file needs to be encrypted.

Run the playbook without vault:
```
ansible-playbook avi_topology_policy.yaml
```

Run the playbook with vault password file:
```
ansible-playbook avi_topology_policy.yaml --vault-password-file ../vault_pass
```

Run the playbook with vault password:
```
ansible-playbook avi_topology_policy.yaml --ask-vault-pass
```
