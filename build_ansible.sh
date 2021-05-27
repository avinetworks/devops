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
/usr/bin/ansible-galaxy install avinetworks.avicontroller
cat << EOF > /root/avicontroller.yml
---
- hosts: localhost
  vars:
    avi_con_version: 20.1.5-9148-20210415.070829
  roles:
  - role: avinetworks.avicontroller
    vars:
      con_image: "projects.registry.vmware.com/nsxalb/controller:{{ avi_con_version }}"
      con_disk_path: /nsxalb
      con_cores: "{{ ansible_processor_cores * ansible_processor_count * ansible_processor_threads_per_core }}"
      con_disk_gb: "{{ (ansible_devices.vdd.size | splitext | first) | int - 10 }}"
  #tasks:
  #- template:
      #src: /root/defaults.template.j2
      #dest: /etc/sysconfig/avicontroller
      #mode: 0644
EOF
/usr/bin/ansible-playbook /root/avicontroller.yml
systemctl restart avicontroller

