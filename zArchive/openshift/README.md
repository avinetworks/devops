# Openshift Setup of Service Engine

The following shows how to setup serviceengines using single node setup beautifully described by Grant Shipley @ Redhat.

https://github.com/gshipley/installcentos

Here are steps to configure a quick one node openshift setup.

<TODO>

## Requirements

 - centos
 - VM / Host with 8 cores and 24 GB RAM.
 - ```pip install avisdk>=18.1.5b3``` 
 - ```ansible-galaxy install avinetworks.avisdk```
 - ```ansible-galaxy install avinetworks.aviconfig```

## Avi Setup

A service account with name avi is created. The Avi SE pod role and cluster bindings are setup. All this setup I hope
to convert to an Ansible role such that user only needs to provide IP address of the host, avi controller,
and openshift cloud name.

```bash
oc create -f sa.json
oc create -f avisepodrole.yaml
oc create -f avisepodclusterbinding.yaml
oc describe sa avi
```

Now that avi service account is setup, let us get the service token that is needed to configure in avi controller.

```bash
oc describe secret <name of secret from oc describe sa avi>
```

Eg.
```bash
[root@localhost openshift]# oc describe sa avi
Name:                avi
Namespace:           default
Labels:              <none>
Annotations:         <none>
Image pull secrets:  avi-dockercfg-t9lh4
Mountable secrets:   avi-token-wqw8h
                     avi-dockercfg-t9lh4
Tokens:              **avi-token-xxxx**
                     **avi-token-yyyy**
Events:              <none>

```

The controller secret should be 
```bash
oc describe secret avi-token-xxxx

    Name:         avi-token-xxxx
    Namespace:    default
    Labels:       <none>
    Annotations:  kubernetes.io/created-by=openshift.io/create-dockercfg-secrets
                  kubernetes.io/service-account.name=avi
                  kubernetes.io/service-account.uid=da3bf0f3-e3c9-11e8-8e1b-005056b01820
    
    Type:  kubernetes.io/service-account-token
    
    Data
    ====
    ca.crt:          1070 bytes
    namespace:       7 bytes
    service-ca.crt:  2186 bytes
    token:           **adfa.adfafd.u_wjbB-3hcCGUgNvPj-SZr5kRAR-adfa-adf-dfasdf**

```

Now store the above token into ~/.openshift_service_token

Call the ansible setup to update controller using playbook

```bash
ansible-playbook controller_kcloud.yml -e "controller_ip=<xxxxx> password=<yyyy>"
```
The above playbook will perform following high level tasks
- Setup East West and North South Networks
- Setup IPAM Profile and IPAM DNS profiles for use in Openshift cluster
- Setup Avi OpenShift/K8s cloud with above settings such that it can integrate with the above created cluster.

## App Description
It is setup as a north-south service as avicicd.default.grastogi.avi.local with two backend services
avisvccicdblue and avisvccicdgreen each with its deployment.
There are four files in the openshift_app.
```bash
ls bluegreen_app
os-dc-http-avicicdsvcblue.json  os-dc-http-avicicdsvcgreen.json  os-ro-avicicd.yaml  os-svc-ew-http-avicicdsvcblue.json  
os-svc-ew-http-avicicdsvcgreen.json
```

- os-svc-ew-http-avicicdsvcblue.json: This sets up the blue service with deployment config 
  os-dc-http-avicicdsvcblue.json
- os-svc-ew-http-avicicdsvcgreen.json: This sets up the green service with deploymet config 
  os-dc-http-avicicdsvcgreen.json
- os-ro-avicicd.yaml: This sets up the virtualservice in avi using hostname (avicicd.default.grastogi.avi.local) and pool group with the two service.
 
