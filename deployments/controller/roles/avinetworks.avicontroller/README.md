# avinetworks.avicontroller

[![Build Status](https://travis-ci.org/avinetworks/ansible-role-avicontroller.svg?branch=master)](https://travis-ci.org/avinetworks/ansible-role-avicontroller)
[![Ansible Galaxy](https://img.shields.io/badge/galaxy-avinetworks.avicontroller-blue.svg)](https://galaxy.ansible.com/avinetworks/avicontroller/)

Using this module you are able to install the Avi Vantage Controlller, to your system. However, minimum requirements must be met.

## Requirements

Requires Docker to be installed. We use `avinetworks.docker` to install Docker on a host. We also specify it in our metafile.

## Role Variables

Possible variables are listed below:

### Required Variables
Could be ran with all defaults. IP will become the default main IP from ansible_default_ipv4.address

### Optional Variables
```

con_version: latest
con_cores: "{{ ansible_processor_count }}"
con_memory_gb: "{{ ansible_memtotal_mb // 1024 }}"
destination_disk: "{{ ansible_mounts|sort(reverse=True, attribute='size_total')|map(attribute='mount')|first}}"
con_disk_path: "{{ destination_disk }}opt/avi/controller/data"
con_disk_gb: 30
con_metrics_disk_path: ~
con_metrics_disk_gb: ~
con_logs_disk_path: ~
con_logs_disk_gb: ~
controller_ip: "{{ ansible_default_ipv4.address }}"
dev_name: ~
setup_json: ~
ports:
  portal_http: 80
  portal_https: 443
  sec_channel_neg: 8443
  controller_ssh: 5098
  serviceengine_ssh: 5099
  controller_cli: 5054
  snmp: 161

# Use these to add parameters manually if desired. These do not overwrite the defaults.
mounts_extras: [] # Do NOT need to include -v in each string
env_variables_extras: [] # Do NOT need to include -e in each string
ports_list_extras: [] # Do NOT need to include -p in each string
```

### Parameter Override Variables
However, you are able to provide these parameters another way. Using the following variables. This will allow the user to customize all values.  
**!!!BEWARE: USING THIS WILL ERASE DEFAULTS - USE WITH CAUTION!!!**

```

env_variables_all:
  - "CONTAINER_NAME=avicontroller"
  - "MANAGEMENT_IP={{ controller_ip | string}}"
  - "NUM_CPU={{ con_cores }}"
  - "NUM_MEMG={{ con_memory_gb }}"
  - "DISK_GB={{ con_disk_gb }}"

mounts_all:
  - "/:/hostroot/"
  - "/var/run/docker.sock:/var/run/docker.sock"
  - "{{ con_disk_path }}:/vol/"

ports_list_all:
  - "5098:5098"
  - "80:80"
  - "443:443"
  - "8443:8443"
  - "5054:5054"
  - "161:161"
```

## Dependencies

avinetworks.docker

## Example Playbook

**WARNING:**
**Before using this example please make the correct changes required for your server.  
For more information please visit [https://kb.avinetworks.com/avi-controller-sizing/] (https://kb.avinetworks.com/avi-controller-sizing/)**

**It is recommended you adjust these parameters based on the implementation desired.**

```

- hosts: servers
  roles:
    - role: avinetworks.avicontroller
      controller_ip: 10.10.27.101
      con_cores: 4                     # If not specified core count is 4
      con_memory_gb: 12                 # If not specified memory count is 12
```

The following is an example with minimum parameters.
```

- hosts: servers
  roles:
    - role: avinetworks.avicontroller
```


## License

MIT

## Author Information

Eric Anderson  
[Avi Networks](http://avinetworks.com)
