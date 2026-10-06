## Avi Controller AWS IAM Policies

This directory contains IAM policies and trust policies used by Avi Controller components on AWS. Below is a brief description of each file and the notable permissions/resources it targets.

### avicontroller-asg-policy.json
- Purpose: Read-only access to Auto Scaling metadata.
- Key actions: `autoscaling:DescribeAutoScalingGroups`, `DescribeAutoScalingInstances`, `DescribeLaunchConfigurations`.

### avicontroller-ec2-policy.json
- Purpose: Manage EC2 networking, instances, AMIs, and snapshots associated with Avi resources.
- Key actions: Security groups (`Authorize/Revoke/Delete`), instance lifecycle (`Start/Stop/Terminate/RunInstances`), ENIs, EIPs, AMI import/registration, snapshots.
- Scope: Generally `Resource: *` with conditions on `ec2:ResourceTag/AVICLOUD_UUID` or `avicloud_uuid` where applicable.

### avicontroller-iam-policy.json
- Purpose: Read IAM metadata about Avi roles and policies, and pass the `vmimport` role to VM Import/Export.
- Key actions: `iam:Get*`, `iam:List*` for roles/policies/instance-profiles, and `iam:PassRole` on the `vmimport` role.
- Resources: Avi role/policy ARNs (e.g., `arn:aws:iam::*:role/AviController-Refined-Role`, `arn:aws:iam::*:policy/AviController*`) and `vmimport` role.
- Required: The `AviControllerPassVmimportRole` statement must have `<Account_ID>` replaced with your 12-digit AWS account ID. Unlike the wildcards elsewhere in this directory, this is not optional scoping — IAM rejects the policy document with `MalformedPolicyDocument` if the placeholder is left in place.
    - `ec2:ImportSnapshot` passes the `vmimport` service role to VM Import/Export, so the caller needs `iam:PassRole` on that role. Without it, SE AMI creation fails with `AuthFailure ... not authorized to perform iam:PassRole` and the cloud goes into a failed state. AWS began enforcing this requirement after these policies were first published (JIRA AV-296569).
-Scope: Replace the prefix value as per the deployment.     
    - Role name used is AviController-Refined-Role
    - instance_profile_name should be same as Role name
    - use a common prefix for policy name in this example it is <AviController>

### avicontroller-iam-XAccess-policy.json
- Purpose: Broad read access to IAM account metadata for discovery.
- Key actions: `iam:Get*`, `iam:List*` including account aliases and attached policies.
- Resources: `*` (read-only).

### avicontroller-kms-policy.json
- Purpose: Use KMS keys for envelope encryption.
- Key actions: `kms:CreateGrant`, `Decrypt`, `DescribeKey`, `GenerateDataKey(*)`, `ReEncrypt*`.
- Resources: `arn:aws:kms:*:*:key/*` plus list operations on `*`.
- Scope: Replace `Resource: *` with conditions by providing the specific <key_id_to_be_used> value as per the deployment `arn:aws:kms:*:*:key/<key_id_to_be_used>` 
   

### avicontroller-kms-vmimport.json
- Purpose: Allow decrypt for VM Import/Export flows.
- Key actions: `kms:Decrypt`.
- Resources: `arn:aws:kms:*:*:key/*`.

### avicontroller-r53-policy.json
- Purpose: Manage Route 53 records in hosted zones.
- Key actions: `route53:ChangeResourceRecordSets`, `ListResourceRecordSets`, and read-only hosted zone queries.
- Resources: `arn:aws:route53:::hostedzone/*` (for record changes) and `*` for reads.
- Scope: Replace `*` with Route53 <hosted_zone_id> as per the deployment `arn:aws:route53:::hostedzone/<hosted_zone_id>`

### avicontroller-role-trust.json
- Purpose: Trust policy for the Avi Controller role to be assumed by EC2 instances.
- Principal: `ec2.amazonaws.com`.
- Action: `sts:AssumeRole`.

### avicontroller-s3-policy.json
- Purpose: Manage Avi SE artifact buckets and objects.
- Key actions: Bucket lifecycle (`Create/Delete/List/Tagging`) and object operations (`Get/Put/Delete`, multipart).
- Resources: `arn:aws:s3:::avi-se-*` and `arn:aws:s3:::avi-se-*/*`.
- Scope: Replace `avi` with the new_se_prefix as per the deployment `arn:aws:s3:::<new_se_prefix>-se-*`

### avicontroller-sqs-sns-policy.json
- Purpose: Manage SQS queues and SNS topics used for ASG notifications.
- Key actions: SQS queue management (`Create/Delete/Purge/ReceiveMessage/...`), SNS topic management (`Create/Delete/Publish/Subscribe/...`), ASG notification configuration.
- Resources: `arn:aws:sqs:*:*:avi-sqs-cloud-*`, `arn:aws:sns:*:*:avi-asg-cloud-*`, plus some list/read on `*`.

### vmimport-role-policy.json
- Purpose: Permissions for the `vmimport` role to import snapshots and register AMIs from S3.
- Key actions: `s3:GetBucketLocation`, `s3:ListBucket`, `s3:GetObject`, and EC2 image/snapshot operations (`CopySnapshot`, `ModifySnapshotAttribute`, `RegisterImage`, `Describe*`).
- Resources: S3 `avi-se-*` buckets and all EC2 for describes.
- Scope: Replace `avi` with the new_se_prefix as per the deployment `arn:aws:s3:::<new_se_prefix>-se-*`. This must match the prefix used in `avicontroller-s3-policy.json` — if the two differ, the `vmimport` role cannot read the SE image from the bucket the Controller created and image import fails.

### vmimport-role-trust.json
- Purpose: Trust policy for the `vmimport` role.
- Principal: `vmie.amazonaws.com` with `sts:ExternalId` = `vmimport`.
- Action: `sts:AssumeRole`.

Notes
- These policies are examples/templates and may require scoping based on your organization needs to your account, regions, KMS keys, Route 53 hosted zone IDs, or resource tags.


