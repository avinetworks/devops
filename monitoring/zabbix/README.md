avi-zabbix-integration
========================

## Installation:

You will need to copy the avi_zabbix.py file into your `externalscripts` directory on your Zabbix server.  
**Don't forget to edit the `avi_controller`, `avi_user`, and `avi_password` values in each avi_zabbix_<integration>.py file.**

Please reference `setup.sh` to install the integration.

## Zabbix Discovery Rule
This is to be entered into the `Discovery rules` section of the Zabbix Template
- Zabbix External Script Key
  - `avi_zabbix_discovery.py[pool,-t,Demo,-c,10.130.129.34,-u,common,-p,password]`

## Zabbix Trapper

### Usage
avi_zabbix_trapper.py [-h] [-t TENANT] [-c CONTROLLER] [-u USER] [-p PASSWORD] [-z ZABBIX_SERVER] hostname entity_type [step]

### Example
- To run trapper from Zabbix External Script
  - `avi_zabbix_trapper.py[{HOST.HOST},pool,-t,Demo,-c,10.130.129.34,-u,common,-p,password,-z,10.10.10.200]`

- To run trapper from Cron Job
  - `/usr/lib/zabbix/externalscripts/avi_zabbix_trapper.py ${hostname} ${pool} -t ${tenant} -c ${controller_ip} -u ${user} -p ${password} -z ${zabbix_server}`

## Zabbix Monitor
This tool can be used by command line, or as a Zabbix External Script. Please keep in mind, each item is a separate call and can cause a lot of load on a controller. **USE WITH CAUTION**

### Usage:
`avi_zabbix_monitor.py [-h] [-t TENANT] [-c CONTROLLER] [-u USER] [-p PASSWORD] entity_type entity_name metric_id step`

### Example
`avi_zabbix_monitor.py[entity_type, entity_name, metric_id, step]`
`avi_zabbix_monitor.py[-t, tenant, -c, controller, -u, user, -p, password, entity_type, entity_name, metric_id]`


## Summary
### Description
Script used to get stats from Avi Vantage API into Zabbix

#### Positional Arguments:
|  Argument    | Description                                                  |
|:------------ |:------------------------------------------------------------ |
|  entity_type | The type of object                                           |
|  entity_name | The name of the Object                                       |
|  metric_id   | The metric_id of the object to be queried                    |
|  step        | The time period to query in seconds (Default: 300) (Optional)|

#### Optional Arguments:
|  Argument                               | Description                                     |
|:--------------------------------------- |:----------------------------------------------- |
| -h, --help                              | show this help message and exit                 |
| -t TENANT, --tenant TENANT              | The name of the tenant to run against           |
| -c CONTROLLER, --controller CONTROLLER  | IP Address of the controller                    |
| -u USER, --user USER                    | Username to authenticate against Avi Controller |
| -p PASSWORD, --password PASSWORD        | Password to authenticate against Avi Controller |
