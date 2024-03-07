# VMware NSX Advanced Load Balancer Controller

With this template, you can use IBM Cloud Schematics to create an NSX Advanced Load Balancer controller built on a Centos 7 host OS. Schematics uses [Terraform](https://www.terraform.io/) as the infrastructure-as-code engine. 

**Included**:
* 1 [NSX-ALB instance](https://avinetworks.com/why-avi/multi-cloud-load-balancing/)

**Requires**:
* VPC
* Subnet
* SSH Key
* NSX-ALB license

## Costs

When you apply template, the infrastructure resources that you create incur charges as follows. To clean up the resources, you can [delete your Schematics workspace or your instance](https://cloud.ibm.com/docs/schematics?topic=schematics-manage-lifecycle#destroy-resources). Removing the workspace or the instance cannot be undone. Make sure that you back up any data that you must keep before you start the deletion process.

* **NSX-ALB instance**: One instance will be created, according to the size you choose. The price for your virtual server instances depends on the flavor of the instances, how many you provision, and how long the instances are run. For more information, see [IBM VPC pricing guide](https://www.ibm.com/cloud/vpc/pricing).
* **NSX-ALB data volume**: One block volume will be created, according to the size you choose, and attached to the NSX-ALB instance.  This volume uses the 3000 IOPS storage profile. 
## Dependencies

Before you can apply the template in IBM Cloud, complete the following steps.

1.  Make sure that you have the following permissions in IBM Cloud Identity and Access Management:
    * **Manager** service access role for IBM Cloud Schematics
    * **Operator** platform role for VPC Infrastructure
2.  Download the [`ibmcloud` command line interface (CLI) tool](https://cloud.ibm.com/docs/cli/reference/ibmcloud?topic=cloud-cli-install-ibmcloud-cli).
3.  Install the `ibmcloud terraform` and `ibmcloud is` CLI plug-ins for Schematics and VPC infrastructure. **Tip**: To update your current plug-ins, run `ibmcloud plugin update`.
    *  `ibmcloud plugin install schematics`
    *  `ibmcloud plugin install vpc-infrastructure`
4.  [Create or use an existing SSH key for VPC virtual servers](https://cloud.ibm.com/docs/vpc?topic=vpc-ssh-keys).

## Configuring your deployment values

When you select the [`NSX-ALB Controller`template](https://github.com/avinetworks/devops/terraform/ibm_catalog) from the IBM Cloud catalog, you set up your deployment variables from the **Create** page. When you apply the template, IBM Cloud Schematics provisions the resources according to the values that you specify for these variables.

### Required values
Fill in the following values, based on the steps that you completed before you began.

|Variable Name|Description|
|-------------|-----------|
|`vpc`|Enter the VPC where you want the instance to be placed. |
|`subnet`|Enter the subnet where you want the instance to be placed|
|`ssh-key`|Enter the [public SSH key](https://cloud.ibm.com/docs/vpc?topic=vpc-ssh-keys) that you use to access your VPC virtual servers. |
|`zone`|Enter the zone where the VPC is created.|

### Optional values
Before you apply your template, you can customize the following default variable values.

|Variable Name|Description|Default Value|
|-------------|-----------|-------------|
|`firewall_inbound_subnet`|The source subnet to allow for inbound access to your controller. |`10.0.0.0/8`|
|`firewall_outbound_subnet`|The destination subnet to allow for outbound access from your controller.  Internet access is required for deployment.|`0.0.0.0/8`|
|`floating_ip`|Choose whether to give the controller instance a floating IP.  This isn't necessary if you're using a public gateway.  Accepts true or false.|`false`|
|`controller_size`|The size of the controller instance.  Accepts small, medium, and large.|`small`|
|`disk_size`|The size of the data disk for the controller instance.  Impacts log storage. Accepts small, medium, and large.|`small`|

## Sizing
### [Controller Size](https://avinetworks.com/docs/latest/avi-controller-sizing/)
* small:  bx2-8x32
* medium: cx2-16x32
* large:  cx2-32x64
### [Disk Size](https://avinetworks.com/docs/latest/avi-controller-sizing/)
* small:  256GB
* medium: 512GB
* large:  1024GB

## Outputs
After you apply the template your VPC resources are successfully provisioned in IBM Cloud, you can review information such as the virtual server IP addresses and VPC identifiers in the Schematics log files, in the `Terraform SHOW` section.
