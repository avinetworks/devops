#!/bin/bash
#
# Created on Sept 21, 2016
# @author: Eric Anderson (eanderson@avinetworks.com)

wget --no-check-certificate https://github.com/avinetworks/avi-zabbix-integration/archive/master.tar.gz
tar -xvf master.tar.gz
sudo cp avi-zabbix-integration-master/externalscripts/avi_zabbix* /usr/lib/zabbix/externalscripts/
sudo chmod +x /usr/lib/zabbix/externalscripts/avi_zabbix*
rm -rf master.tar.gz avi-zabbix-integration-master
