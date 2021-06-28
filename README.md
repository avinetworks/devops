# VMware NSX Advanced Load Balancer Controller



<!-- Start with a short description that explains what the product is, why a customer would want to install and use it, etc. The following info is used here as an example. Be sure to update it accordingly. -->

Avi Vantage delivers enterprise grade Elastic Load Balancer with SSL offload, web application security and Real-Time application performance monitoring and predictive autoscaling for applications for optimal application sizing.

With this template, you can use IBM Cloud Schematics to create an [NSX Advanced Load Balancer](https://avinetworks.com/why-avi/multi-cloud-load-balancing/) controller built on a Centos 7 host OS. Schematics uses [Terraform](https://www.terraform.io/) as the infrastructure-as-code engine.  

## Before you begin

<!-- List any prereqs including required permissions, capacity requirements, etc. The following info is used as an example. Update accordingly. -->


1.  Make sure that you have the following permissions in IBM Cloud Identity and Access Management:
    * **Manager** service access role for IBM Cloud Schematics
    * **Operator** platform role for VPC Infrastructure
2. [Create or use an existing SSH key for VPC virtual servers](https://cloud.ibm.com/docs/vpc?topic=vpc-ssh-keys).

## Required resources
* VPC
* Subnet for deploying the controller
* NSX-ALB license  (30 day trial license is preinstalled)


## Installing the software

<!-- Recommendation is to not include the large table of configuration parameters that are listed on the Create page. -->

When you select the [`NSX-ALB Controller` template](https://github.com/avinetworks/devops/terraform/ibm_catalog) from the IBM Cloud catalog, you set up your deployment variables from the **Create** page. When you apply the template, IBM 
Cloud Schematics provisions the resources according to the values that you specify for these variables.
### Production configuration
* The customer is responsible for the security, patching, and maintenance of the OS of this controller instance.  
* A 3-node [cluster](https://avinetworks.com/docs/latest/configure-controller-ha-cluster/) is recommended for production deployments, ideally each controller in a different availability zone.  Because of limitations in addressing in IBM cloud, you will not be able to use a floating IP for the cluster.

<!-- Add additional H3 level headings as needed for sections that apply to use on IBM Cloud such as network policy, persistence, cluster topologies, etc.
### H3
### H3
-->

### Sizing
The Terraform template has variables for sizing based on T-shirt sizing.  These T-shirt sizes map to the following instance and volume sizes:
#### [Controller Size](https://avinetworks.com/docs/latest/avi-controller-sizing/)
* small:  bx2-8x32
* medium: cx2-16x32
* large:  cx2-32x64
#### [Disk Size](https://avinetworks.com/docs/latest/avi-controller-sizing/)
* small:  256GB
* medium: 512GB
* large:  1024GB

---
### Required values
Fill in the following values, based on the steps that you completed before you began.

|Variable Name|Description|
|-------------|-----------|
|`vpc`|Enter the VPC where you want the instance to be placed. |
|`subnet`|Enter the subnet where you want the instance to be placed|
|`ssh-key`|Enter the [public SSH key](https://cloud.ibm.com/docs/vpc?topic=vpc-ssh-keys) that you use to access your VPC virtual servers. |
|`zone`|Enter the zone where the VPC is created.|

---
### Optional values
Before you apply your template, you can customize the following default variable values.

|Variable Name|Description|Default Value|
|-------------|-----------|-------------|
|`firewall_inbound_subnet`|The source subnet to allow for inbound access to your controller. |`10.0.0.0/8`|
|`firewall_outbound_subnet`|The destination subnet to allow for outbound access from your controller.  Internet access is required for deployment.|`0.0.0.0/8`|
|`floating_ip`|Choose whether to give the controller instance a floating IP for internet access.  This isn't necessary if you're using a public gateway.  Accepts true or false.|`false`|
|`controller_size`|The size of the controller instance.  Accepts small, medium, and large.|`small`|
|`disk_size`|The size of the data disk for the controller instance.  Impacts log storage. Accepts small, medium, and large.|`small`|

### Outputs
After you apply the template your VPC resources are successfully provisioned in IBM Cloud, you can review information such as the virtual server IP addresses and VPC identifiers in the Schematics log files, in the `Terraform SHOW` section.

The controller will take around 15 minutes to deploy, once the web interface is available, you can continue with configuring the controller and deploying Service Engines in your environment.

## Upgrading to a new version

<!-- How can a user upgrade to a new version when it's available? The following info is used as an example. Update accordingly. -->

* Upgrading to a new version of the NSX-ALB controller can be done through the web UI by navigating to Administration/Controller.
* Upgrading from the CLI/API can also be done, follwing [this guide.](https://avinetworks.com/docs/latest/flexible-upgrades/)
* The upgrade software can be downloaded from https://portal.avipulse.vmware.com/ if you have a support entitlement.


## Uninstalling the software

<!-- How can a user uninstall this product? The following info is used as an example. Update accordingly. -->

Complete the following steps to uninstall a Terraform-deployed controller from your account. 

1. Go to the **Menu** > **Schematics**.
2. Select your workspace name. 
3. Click **Actions** > **Destroy resources**. All resources in your workspace are deleted.
4. Click **Update**.
5. To delete your workspace, click **Actions** > **Delete workspace**.

This will need to be done for each controller schematic if a cluster was deployed.

This will not clean up any resources created in the environment in support of NSX-ALB, such as Service Engine hosts or custom route tables.  Those must be removed manually.

## Getting support

<!-- Reuse the support information (contact info and availability) that your team provided on the Support tab in Partner Center exactly as is. The following is an example. -->

This product is provided and supported by [Example Corp](https://support.examplecorp.com). If you encounter issues, contact Example Corp support by [chat](https://support.examplecorp.com/chat) or [phone](https://support.examplecorp.com/phone). Example Corp support is available 24 hours a day, 7 days a week, 365 days a year. Example Corp support is provided in English and French. 
