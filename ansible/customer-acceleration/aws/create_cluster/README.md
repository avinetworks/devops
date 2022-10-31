# AWS - Create NSX ALB Controller Cluster

The playbook will create controllers under a single Availability Zone.

## Pre-Requisites to interact with AWS

AWS Playbooks use BOTO and aws credentials file

Install BOTO:
```bash
pip3 install boto3
```

Once Installed setup your AWS Credentials

Edit ~/.aws/credentials
```bash
vi ~/.aws/credentials
```

Add the following lines with your details
```bash
[default]
AWS_ACCESS_KEY_ID = <YOUR_ACCESS_KEY>
AWS_SECRET_ACCESS_KEY = <YOUR_SECRET_KEY>
AWS_SESSION_TOKEN = <YOUR_SESSION_TOKEN>

The ansible playbook has been tested under Avitools container version 22.1.1 with the following software packages:
Ansible = 2.13.2
amazon.aws = 4.1.0
vmware.alb = 22.1.1
Python3 = 3.8.10
boto3 = 1.24.34

You can retrieve the container:
docker pull avinetworks/avitools:22.1.1
```