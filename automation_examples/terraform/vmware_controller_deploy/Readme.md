Terraform Module
==================

<img src="https://cdn.rawgit.com/hashicorp/terraform-website/master/content/source/assets/images/logo-text.svg" width="600px">


Usage
---------------------
Deploy Ova or Ovf as a template on the Vcenter and run the terraform modules by using following commands 
```
terraform init
```
To Deploy controller vm on the Vcenter
```
terraform apply -target=module.vmware_deploy
```
To Set the password for Controller
```
terraform apply -target=avi_useraccount.avi_user
```
To Create the cluster
```
terraform apply -target=avi_cluster.vmware_cluster
```
How to Deploy Ova or Ovf template on the Vcenter
-----------------------------------------------------
Deploy the Ova/Ovf Template on VCenter Using following command 
```
ovftool --datastore=<datastore> --vmFolder=<Folder/location> --name=<template_name> --network=<Network> --importAsTemplate <ovafilepath>/file.ova vi://<vsphere_username>:<vsphere_password>@<vsphere_host>/<datacenter>/host/<cluster>
```
