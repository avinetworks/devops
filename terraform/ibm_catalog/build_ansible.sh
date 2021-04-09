#!/bin/bash
yum update -y
yum install wget python3 python3-pip docker gzip ntp epel-release -y
yum install ansible -y
systemctl enable docker
systemctl start docker
mkdir /nsxalb
mkfs.xfs /dev/vdd
echo "/dev/vdd /nsxalb xfs defaults,noatime 1 2" >> /etc/fstab
mount -a
cat << DEFAULTS > /root/defaults.template.j2
# Defaults file for avicontroller service used by /usr/sbin/avicontroller

### Set common variables ###

# If you would like to change the location of the log file, you can modify the setting here.
AVICONTROLLER_LOGFILE="/var/log/avicontroller.log"

# The following value is the management device that the controller will use.
# This interface is managed by the service and is used when working with clusters
# to properly shut down the sub-interface when a new master is chosen.
AVICONTROLLER_DEV_NAME="{{ con_dev_name }}"

# If you'd like to modify the run parameters that are supplied to the service
# you can take full control here. When starting the controller we will use
# /usr/bin/docker run ${AVICONTROLLER_DOCKER_RUN_PARAMS} so anything you put in
# here will be supplied in that manner.
AVICONTROLLER_DOCKER_RUN_PARAMS="{{ con_docker_run_params }}"
DEFAULTS
/usr/bin/ansible-galaxy install avinetworks.avicontroller
cat << EOF > /root/avicontroller.yml
---
- hosts: localhost
  vars:
    avi_con_version: 20.1.4-9087-20210215.202012
  roles:
  - role: avinetworks.avicontroller
    vars:
      con_image: "projects.registry.vmware.com/nsx_alb/controller:{{ avi_con_version }}"
      con_disk_path: /nsxalb
      con_cores: "{{ ansible_processor_cores * ansible_processor_count * ansible_processor_threads_per_core }}"
      con_disk_gb: "{{ (ansible_devices.vdd.size | splitext | first) | int - 10 }}"
  tasks:
  - template:
      src: /root/defaults.template.j2
      dest: /etc/sysconfig/avicontroller
      mode: 0644
EOF
/usr/bin/ansible-playbook /root/avicontroller.yml
systemctl restart avicontroller

