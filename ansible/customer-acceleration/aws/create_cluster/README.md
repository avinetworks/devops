# AWS - Create NSX ALB Controller Cluster

The playbook will create controllers under a single Availability Zone.

## Pre-Requisites to interact with AWS

AWS Playbooks use BOTO and aws credentials file

Install BOTO:
```bash
pip install boto
```

Once Installed setup your AWS Credentials

Edit ~/.aws/credentials
```bash
vi ~/.aws/credentials
```

Add the following lines with your details
```bash
[default]
aws_access_key_id = <YOUR_ACCESS_KEY>
aws_secret_access_key = <YOUR_SECRET_KEY>
```