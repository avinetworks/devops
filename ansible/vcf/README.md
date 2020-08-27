# [Avi Reference Architecture for VCF 3.9.1](https://avinetworks.com/docs/18.2/avi-reference-architecture-for-vcf/avi-reference-architecture-for-vcf-3.9.1/) Ansible playbooks

The Avi VCF ansible playbooks provide the ability for day 0 provisioning as well as day 1 expansion tasks.  The provided playbooks provided allow for the user to deploy a 3-node Controller Cluster, create Avi tenancy objects for user defined VCF compute workload domains and deploy Avi service engines within the compute workload domains.

--------------
## Requirements
--------------
**Python** and **ansible** are the base requirements that must be installed.  In addition to python and ansible, the following packages are also required.


### Python Modules
```
$ pip install pyvmomi avisdk dnspython netaddr
```
### Avisdk Ansible Role

```
$ ansible-galaxy install avinetworks.avisdk
```
### Linux package
```
$ apt install sshpass -y
$ yum install sshpass -y
```

--------------
## Usage
--------------
Each playbook has a corresponding variable file that requires user inputted data to successfully complete.  The variable files for each playbook denote whether specific variables are required are optional.  If a required variable if overlooked the playbook will fail to complete successfully.


--------------
### Deployment of the Avi Controller Cluster in the Management Workload Domain
--------------
```
Playbook:  vcf-ctl.yml
Variables: vcf-ctl-vars.yml
```

This playbook will deploy an Avi Controller cluster within the VCF management workload domain, baseline the controller configuration setting the admin password and creating a VM-VM anti affinity policy to host the 3 nodes of the cluster on seperate servers.

<br></br>

#### vcf-ctl-vars.yml


<table class="documentation-table" cellpadding="0" border="0">
    <tbody><tr>
        <th>Variable</th>
        <th>Choices/<font color="blue">Defaults</font></th>
        <th width="100%">Comments</th>
        </tr>
<tr>
<td >
<b>vcenter_hostname</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>IP or fqdn of VCF mgmt vCenter server used to deploy Avi Controller(s)</div>
</td>
</tr>

<tr>
<td >
<b>vcenter_username</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Username to login to vCenter server</div>
</td>
</tr>

<tr>
<td >
<b>vcenter_password</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Password used to authenticate with the vCenter server</div>
</td>
</tr>

<tr>
<td >
<b>datacenter</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>The vCenter datacenter where the Avi Controller(s) will be deployed</div>
</td>
</tr>


<tr>
<td >
<b>cluster</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>The vCenter esxi cluster name to deploy the Avi Controller(s)</div>
</td>
</tr>


<tr>
<td >
<b>datastore</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>The vCenter datastore to be used</div>
</td>
</tr>


<tr>
<td >
<b>folder</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><divstyle="font-size: small">Default is the Datacenter VM root</td>
<td>
<div>The vCenter VM folder for the Avi Controller VMs.  EX:  &ltdatacenter&gt/vm/avi</div>
</td>
</tr>


<tr>
<td >
<b>ova_path</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Local path/filename where to find the Avi Controller ova</div>
</td>
</tr>

<tr>
<td >
<b>management_network_pg</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>The network portgroup to place the Avi Controller vNICs into</div>
</td>
</tr>


<tr>
<td >
<b>avi_admin_password</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>The password to set for the local admin account</div>
</td>
</tr>


<tr>
<td >
<b>dns_server</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>DNS server the Avi Controller should be configured to use</div>
</td>
</tr>


<tr>
<td >
<b>ntp_server</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>NTP server the Avi Controller should be configured to use</div>
</td>
</tr>


<tr>
<td >
<b>ctl_memory_mb</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> 24576</td>
<td>
<div>The amount of memory in MB to assign to the Avi Controller(s)</div>
</td>
</tr>


<tr>
<td >
<b>ctl_num_cpus</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> 8</td>
<td>
<div>The number of vcpus to assign to the Avi Controller(s)</div>
</td>
</tr>

<tr>
<td >
<b>ctl_disk_size_gb</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> 128</td>
<td>
<div>The size of disk in GB to assign to the Avi Controller(s)</div>
</td>
</tr>


<tr>
<td >
<b>cluster_vip</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Cluster VIP to be used for a 3 node cluster</div>
</td>
</tr>

<tr>
<td >
<b>three_node_cluster</b><br><div style="font-size: small">boolean
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><li>True</li><li>False</li></td>
<td>
<div>Deploy 3 Avi Controller nodes and cluster them</div>
</td>
</tr>


<tr>
<td >
<b>license_file</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Local path/filename for a license file to be applied to the Avi Controller cluster</div>
</td>
</tr>


<tr>
<td >
<b>node1_mgmt_ip</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> DHCP</td>
<td>
<div>MGMT IP address to Avi Cluster node 1, if blank DHCP will be used.  <strong>Recommended to specify a static IP address</strong></div>
</td>
</tr>


<tr>
<td >
<b>node1_mgmt_mask</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> DHCP</td>
<td>
<div>Netmask to be used when static IP is assigned.  <strong>Example:</strong>  24  <strong>Recommended to specify a static IP address</strong></div>
</td>
</tr>

<tr>
<td >
<b>node1_mgmt_gw</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> DHCP</td>
<td>
<div>Gateway IP to be used when static IP is assigned.<strong>  Recommended to specify a static IP address</strong></div>
</td>
</tr>


<tr>
<td >
<b>node1_fqdn</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>FQDN for the Avi Controller Node.  When defined the FQDN will be used when defining cluster member nodes.</div>
</td>
</tr>



<tr>
<td >
<b>node2_mgmt_ip</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> DHCP</td>
<td>
<div>MGMT IP address to Avi Cluster node 2, if blank DHCP will be used.  <strong>Recommended to specify a static IP address</strong></div>
</td>
</tr>


<tr>
<td >
<b>node2_mgmt_mask</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> DHCP</td>
<td>
<div>Netmask to be used when static IP is assigned.    <strong>Example:</strong>  24  <strong>Recommended to specify a static IP address</strong></div>
</td>
</tr>



<tr>
<td >
<b>node2_mgmt_gw</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> DHCP</td>
<td>
<div>Gateway IP to be used when static IP is assigned.<strong>  Recommended to specify a static IP address</strong></div>
</td>
</tr>


<tr>
<td >
<b>node2_fqdn</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>FQDN for the Avi Controller Node.  When defined the FQDN will be used when defining cluster member nodes.</div>
</td>
</tr>


<tr>
<td >
<b>node3_mgmt_ip</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> DHCP</td>
<td>
<div>MGMT IP address to Avi Cluster node 3, if blank DHCP will be used.  <strong>Recommended to specify a static IP address</strong></div>
</td>
</tr>


<tr>
<td >
<b>node3_mgmt_mask</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> DHCP</td>
<td>
<div>Netmask to be used when static IP is assigned.    <strong>Example:</strong>  24  <strong>Recommended to specify a static IP address</strong></div>
</td>
</tr>



<tr>
<td >
<b>node3_mgmt_gw</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> DHCP</td>
<td>
<div>Gateway IP to be used when static IP is assigned.<strong>  Recommended to specify a static IP address</strong></div>
</td>
</tr>


<tr>
<td >
<b>node3_fqdn</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>FQDN for the Avi Controller Node.  When defined the FQDN will be used when defining cluster member nodes.</div>
</td>
</tr>


</tbody>
</table>




<br></br>
--------------
### Setup a Compute (VI) Workload Domain on the Avi Controller Cluster
--------------
```
Playbook:  vcf-workload.yml
Variables: vcf-workload-vars.yml
```

This playbook will create the Compute Workload Domain tenancy objects within the Avi Controller.  This includes tenant, cloud and serviceengine group.

<br></br>
#### vcf-workload-vars.yml


<table class="documentation-table" cellpadding="0" border="0">
    <tbody><tr>
        <th>Variable</th>
        <th>Choices/<font color="blue">Defaults</font></th>
        <th width="100%">Comments</th>
        </tr>
<tr>
<td >
<b>avi_controller_ip</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>IP or fqdn of Avi Controller cluster to configure</div>
</td>
</tr>

<tr>
<td >
<b>avi_username</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Username to use for authentication to the Avi Controller</div>
</td>
</tr>

<tr>
<td >
<b>avi_password</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Password to use for authentication to the Avi Controller</div>
</td>
</tr>


<tr>
<td >
<b>workload_name</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Name of the workload domain to create the Avi tenancy objects for</div>
</td>
</tr>

</tbody>
</table>



<br></br>

--------------
### Create an Avi Service Engine in the Compute (VI) Workload Domain
--------------
--------------
```
Playbook:  vcf-se.yml
Variables: vcf-se-vars.yml
```

This playbook will deploy Avi Service Engines within the VCF Compute Workload Domain.

<br></br>
#### vcf-se-vars.yml

<table class="documentation-table" cellpadding="0" border="0">
    <tbody><tr>
        <th>Variable</th>
        <th>Choices/<font color="blue">Defaults</font></th>
        <th width="100%">Comments</th>
        </tr>


<tr>
<td >
<b>avi_controller_ip</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>IP or fqdn of Avi Controller cluster for the service engine</div>
</td>
</tr>

<tr>
<td >
<b>avi_username</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Username to use for authentication to the Avi Controller</div>
</td>
</tr>

<tr>
<td >
<b>avi_password</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Password to use for authentication to the Avi Controller</div>
</td>
</tr>


<tr>
<td >
<b>workload_name</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Name of the workload domain to deploy the Avi Service Engine in</div>
</td>
</tr>

<tr>
<td >
<b>se_group</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong>  &ltworkload_domain&gt-segroup</td>
<td>
<div>Name of the Avi serviceengine group to deploy the Avi Service Engine in</div>
</td>
</tr>

<tr>
<td >
<b>vcenter_hostname</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>IP or fqdn of VCF compute vCenter server used to deploy Avi Service Engine</div>
</td>
</tr>

<tr>
<td >
<b>vcenter_username</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Username to login to vCenter server</div>
</td>
</tr>

<tr>
<td >
<b>vcenter_password</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Password used to authenticate with the vCenter server</div>
</td>
</tr>

<tr>
<td >
<b>datacenter</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>The vCenter datacenter where the Avi Service Engine will be deployed</div>
</td>
</tr>


<tr>
<td >
<b>cluster</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>The vCenter esxi cluster name to deploy the Service Engine</div>
</td>
</tr>


<tr>
<td >
<b>datastore</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>The vCenter datastore to be used</div>
</td>
</tr>


<tr>
<td >
<b>folder</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><divstyle="font-size: small">Default is the Datacenter VM root</td>
<td>
<div>The vCenter VM folder for the Avi Service Engine VM.  EX:  &ltdatacenter&gt/vm/avi</div>
</td>
</tr>


<tr>
<td >
<b>management_network_pg</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>The network portgroup to place the Avi service engine management vNIC into</div>
</td>
</tr>


<tr>
<td >
<b>data_nic_parking_pg</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>The network portgroup to place unused Avi service engine data vNIC(s) into</div>
</td>
</tr>

<tr>
<td >
<b>se_mgmt_ip</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> DHCP</td>
<td>
<div>MGMT IP address to assign to Service Engine, if blank DHCP will be used.  <strong>Recommended to specify a static IP address</strong></div>
</td>
</tr>


<tr>
<td >
<b>se_mgmt_mask</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> DHCP</td>
<td>
<div>Netmask to be used when static IP is assigned.    <strong>Example:</strong>  24 <strong>Recommended to specify a static IP address</strong></div>
</td>
</tr>

<tr>
<td >
<b>se_mgmt_gw</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> DHCP</td>
<td>
<div>Gateway IP to be used when static IP is assigned.<strong>  Recommended to specify a static IP address</strong></div>
</td>
</tr>


<tr>
<td >
<b>dns_server</b><br><div style="font-size: small">string / required
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>DNS server the Avi Service Engine should be configured to use</div>
</td>
</tr>



<tr>
<td >
<b>se_memory_mb</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> 4096</td>
<td>
<div>The amount of memory in MB to assign to the Avi Service Engine</div>
</td>
</tr>

<tr>
<td >
<b>se_memory_reserve_lock</b><br><div style="font-size: small">boolean
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><li>True</li><li>False - Default</li></td>
<td>
<div>Reserve service engine memory on esxi server</div>
</td>
</tr>


<tr>
<td >
<b>se_num_cpus</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> 2</td>
<td>
<div>The number of vcpus to assign to the Avi Service Engine</div>
</td>
</tr>

<tr>
<td >
<b>se_cpu_reserve_mhz</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"></td>
<td>
<div>Amount of CPU in mhz to reserve on esxi server for the Service Engine</div>
</td>
</tr>

<tr>
<td >
<b>se_disk_size_gb</b><br><div style="font-size: small">string
<div style="font-size: small">
</div>
</td>
<td><b></b><br><div style="font-size: small"><strong>Default:</strong> 20</td>
<td>
<div>The size of disk in GB to assign to the Avi Service Engine</div>
</td>
</tr>



</tbody>
</table>

<table class="documentation-table" cellpadding="0" border="0">
    <tbody><tr>

<tr>
<td colspan="2">
<b>data_network1</b>
<div style="font-size: small">
<span style="color: purple">dictionary</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Parameters for defining data vnic 1 on Avi Service Engine</div>
</td>
</tr>

<tr>
<td>
</td>
<td colspan="1">
<b>se_int_pg</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Port group to use for SE data nic 1, leave blank for unused</div>
</td>
</tr>


<tr>
<td>
</td>
<td colspan="1">
<b>se_int_ip</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined</div>
</td>
</tr>



<tr>
<td>
</td>
<td colspan="1">
<b>se_int_mask</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined.  <strong>Example:</strong> 24</div>
</td>
</tr>

</tbody>
</table>

<table class="documentation-table" cellpadding="0" border="0">
    <tbody><tr>

<tr>
<td colspan="2">
<b>data_network2</b>
<div style="font-size: small">
<span style="color: purple">dictionary</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Parameters for defining data vnic 2 on Avi Service Engine</div>
</td>
</tr>

<tr>
<td>
</td>
<td colspan="1">
<b>se_int_pg</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Port group to use for SE data nic 2, leave blank for unused</div>
</td>
</tr>


<tr>
<td>
</td>
<td colspan="1">
<b>se_int_ip</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined</div>
</td>
</tr>



<tr>
<td>
</td>
<td colspan="1">
<b>se_int_mask</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined.  <strong>Example:</strong> 24</div>
</td>
</tr>

</tbody>
</table>

<table class="documentation-table" cellpadding="0" border="0">
    <tbody><tr>

<tr>
<td colspan="2">
<b>data_network3</b>
<div style="font-size: small">
<span style="color: purple">dictionary</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Parameters for defining data vnic 3 on Avi Service Engine</div>
</td>
</tr>

<tr>
<td>
</td>
<td colspan="1">
<b>se_int_pg</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Port group to use for SE data nic 3, leave blank for unused</div>
</td>
</tr>


<tr>
<td>
</td>
<td colspan="1">
<b>se_int_ip</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined</div>
</td>
</tr>



<tr>
<td>
</td>
<td colspan="1">
<b>se_int_mask</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined.  <strong>Example:</strong> 24</div>
</td>
</tr>

</tbody>
</table>


<table class="documentation-table" cellpadding="0" border="0">
    <tbody><tr>

<tr>
<td colspan="2">
<b>data_network4</b>
<div style="font-size: small">
<span style="color: purple">dictionary</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Parameters for defining data vnic 4 on Avi Service Engine</div>
</td>
</tr>

<tr>
<td>
</td>
<td colspan="1">
<b>se_int_pg</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Port group to use for SE data nic 4, leave blank for unused</div>
</td>
</tr>


<tr>
<td>
</td>
<td colspan="1">
<b>se_int_ip</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined</div>
</td>
</tr>



<tr>
<td>
</td>
<td colspan="1">
<b>se_int_mask</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined.  <strong>Example:</strong> 24</div>
</td>
</tr>

</tbody>
</table>

<table class="documentation-table" cellpadding="0" border="0">
    <tbody><tr>

<tr>
<td colspan="2">
<b>data_network5</b>
<div style="font-size: small">
<span style="color: purple">dictionary</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Parameters for defining data vnic 5 on Avi Service Engine</div>
</td>
</tr>

<tr>
<td>
</td>
<td colspan="1">
<b>se_int_pg</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Port group to use for SE data nic 5, leave blank for unused</div>
</td>
</tr>


<tr>
<td>
</td>
<td colspan="1">
<b>se_int_ip</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined</div>
</td>
</tr>



<tr>
<td>
</td>
<td colspan="1">
<b>se_int_mask</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined.  <strong>Example:</strong> 24</div>
</td>
</tr>

</tbody>
</table>

<table class="documentation-table" cellpadding="0" border="0">
    <tbody><tr>

<tr>
<td colspan="2">
<b>data_network6</b>
<div style="font-size: small">
<span style="color: purple">dictionary</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Parameters for defining data vnic 6 on Avi Service Engine</div>
</td>
</tr>

<tr>
<td>
</td>
<td colspan="1">
<b>se_int_pg</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Port group to use for SE data nic 6, leave blank for unused</div>
</td>
</tr>


<tr>
<td>
</td>
<td colspan="1">
<b>se_int_ip</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined</div>
</td>
</tr>



<tr>
<td>
</td>
<td colspan="1">
<b>se_int_mask</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined.  <strong>Example:</strong> 24</div>
</td>
</tr>

</tbody>
</table>


<table class="documentation-table" cellpadding="0" border="0">
    <tbody><tr>

<tr>
<td colspan="2">
<b>data_network7</b>
<div style="font-size: small">
<span style="color: purple">dictionary</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Parameters for defining data vnic 7 on Avi Service Engine</div>
</td>
</tr>

<tr>
<td>
</td>
<td colspan="1">
<b>se_int_pg</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Port group to use for SE data nic 7, leave blank for unused</div>
</td>
</tr>


<tr>
<td>
</td>
<td colspan="1">
<b>se_int_ip</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined</div>
</td>
</tr>



<tr>
<td>
</td>
<td colspan="1">
<b>se_int_mask</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined.  <strong>Example:</strong> 24</div>
</td>
</tr>

</tbody>
</table>




<table class="documentation-table" cellpadding="0" border="0">
    <tbody><tr>

<tr>
<td colspan="2">
<b>data_network8</b>
<div style="font-size: small">
<span style="color: purple">dictionary</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Parameters for defining data vnic 8 on Avi Service Engine</div>
</td>
</tr>

<tr>
<td>
</td>
<td colspan="1">
<b>se_int_pg</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Port group to use for SE data nic 8, leave blank for unused</div>
</td>
</tr>


<tr>
<td>
</td>
<td colspan="1">
<b>se_int_ip</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined</div>
</td>
</tr>



<tr>
<td>
</td>
<td colspan="1">
<b>se_int_mask</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined.  <strong>Example:</strong> 24</div>
</td>
</tr>

</tbody>
</table>

<table class="documentation-table" cellpadding="0" border="0">
    <tbody><tr>

<tr>
<td colspan="2">
<b>data_network9</b>
<div style="font-size: small">
<span style="color: purple">dictionary</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Parameters for defining data vnic 9 on Avi Service Engine</div>
</td>
</tr>

<tr>
<td>
</td>
<td colspan="1">
<b>se_int_pg</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td>
</td>
<td>
<div>Port group to use for SE data nic 9, leave blank for unused</div>
</td>
</tr>


<tr>
<td>
</td>
<td colspan="1">
<b>se_int_ip</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined</div>
</td>
</tr>



<tr>
<td>
</td>
<td colspan="1">
<b>se_int_mask</b>
<div style="font-size: small">
<span style="color: purple">string</span>                 
</div>
</td>
</div>
</td>
<td><strong><li>Default:</strong>  DHCP if se_int_pg is defined
</td>
<td>
<div>IP address to assign to data nic.  Defaults to DHCP if blank and se_int_pg is defined.  <strong>Example:</strong> 24</div>
</td>
</tr>

</tbody>
</table>
