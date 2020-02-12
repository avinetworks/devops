Terraform Module
==================

<img src="https://cdn.rawgit.com/hashicorp/terraform-website/master/content/source/assets/images/logo-text.svg" width="600px">


Usage
---------------------
Deploy Ova or Ovf as a template on the Vcenter and run the Vmware.tf by using 
```
terraform init
terrform plan
terrform apply
```
How to Deploy Ova or Ovf template on the Vcenter
-----------------------------------------------------
Deploy the Ova/Ovf Template on VCenter Using following command 
```
ovftool --datastore=<datastore> --vmFolder=<Folder/location> --name=<template_name> --network=<Network> --importAsTemplate <ovafilepath>/file.ova vi://<vsphere_username>:<vsphere_password>@<vsphere_host>/<datacenter>/host/<cluster>
```
