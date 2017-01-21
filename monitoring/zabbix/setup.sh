#!/bin/bash
#
#
# @author: Eric Anderson (eanderson@avinetworks.com)

wget --no-check-certificate https://github.com/avinetworks/devops/archive/master.tar.gz
tar -xvf master.tar.gz
yum install -y python-setuptools
easy_install pip
pip install -r devops-master/monitoring/zabbix/requirements.txt
sudo cp devops-master/monitoring/zabbix/externalscripts/avi_zabbix* /usr/lib/zabbix/externalscripts/
sudo chmod +x /usr/lib/zabbix/externalscripts/avi_zabbix*
rm -rf master.tar.gz devops-master
