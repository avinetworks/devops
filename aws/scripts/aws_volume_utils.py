"""
Prerequisites
1. The script needs to be run on a controller. It makes use of datastore to get the cloud credentials.
2. This script performs ModifyVolume operation and requires an additional IAM permission "ec2:ModifyVolume" to work.
3. The AWS cloud is configured in 1 of the 3 ways -
    a. Using Access/Secret key
        i. In this case, the additional permission, "ec2:ModifyVolume",  has to be added to the user whose access/secret key
           is being used to create the cloud.
    b. Using IAM role
        i. In this case, the additional permission, "ec2:ModifyVolume", has to be added to the IAM role associated with the controller.
    c. Using Cross account access
        i. The additional permission, "ec2:ModifyVolume", has to be added to the cross account role that gets assumed 
           for the cloud creation.

Steps to Run the script -

Extending the root volumes - (volumes should be extended to a minimum of 15G, but can be extended to more)
1. python <path_to_aws_volume_utils.py> --size 15

Root volume extended size can be verified by running below command
1. python aws_volume_utils.py --list-volumes

Now, for the extended disk size to get reflected in the SE, following commands are to be run -
1. python aws_volume_utils.py --list-se-ips > /tmp/se_ips

2. for se in `cat /tmp/se_ips` ; do echo $se ; ssh -i /etc/ssh/id_se aviseuser@$se 'sudo growpart /dev/nvme0n1 3;sudo resize2fs /dev/nvme0n1p3'  ; echo ; echo ; done > /tmp/disk_fixup_output

"""

from __future__ import print_function
import argparse
import boto3
import boto.exception
import boto.sts
import dateutil.parser
import time

from avi.infrastructure.datastore import (Datastore,
    db_table_name_from_pb)
from avi.protobuf import common_pb2
from avi.protobuf.cloud_objects_pb2 import Cloud
from avi.protobuf.system_pb2 import SystemConfiguration
from botocore.config import Config
from boto.utils import get_instance_metadata

ASSUME_ROLE_EXP = 3600


class AwsObjectsHandler(object):
    def __init__(self):
        self.ds = Datastore()

    def _get_iam_keys(self, region, username, password, xrole=None, expsecs=None,
        pxhost=None, pxport=None, pxuser=None, pxpass=None):
        akey = skey = tkey = None
        errmsg = None
        expiry = None
        if username and password:
            akey = username
            skey = password
        else:
            meta = get_instance_metadata(timeout=5, num_retries=2)
            try:
                iamsc = meta['iam']['security-credentials']
                role  = next(iter(iamsc.keys()), None)
                if role:
                    akey = iamsc[role]['AccessKeyId']
                    skey = iamsc[role]['SecretAccessKey']
                    tkey = iamsc[role]['Token']
                    expiry = dateutil.parser.parse(iamsc[role]['Expiration'])
            except:
                pass
        if xrole:
            akey = skey = tkey = None
            expiry = None
            try:
                stsc = boto.sts.connect_to_region(region, aws_access_key_id=username,
                    aws_secret_access_key=password, proxy=pxhost, proxy_port=pxport,
                    proxy_user=pxuser, proxy_pass=pxpass)
                if stsc:
                    stsk = stsc.assume_role(xrole, 'avi-xaccess', duration_seconds=expsecs)
                    akey = stsk.credentials.access_key
                    skey = stsk.credentials.secret_key
                    tkey = stsk.credentials.session_token
                    expiry = dateutil.parser.parse(stsk.credentials.expiration)
            except Exception as e:
                errmsg = e.message if isinstance(e, boto.exception.BotoServerError) and e.message else str(e)
        return (akey, skey, tkey, expiry, errmsg)

    def _get_kwargs(self, awscfg, proxy=None, expsecs=ASSUME_ROLE_EXP):
        kwargs = dict()
        awscfg = awscfg
        expiry = None
        emsg   = None
        if not awscfg.use_iam_roles:
            kwargs['aws_access_key_id'] = awscfg.access_key_id
            kwargs['aws_secret_access_key'] = awscfg.secret_access_key
        if proxy and proxy.host and proxy.port:
            kwargs['proxy']      = proxy.host
            kwargs['proxy_port'] = proxy.port
            kwargs['proxy_user'] = proxy.username
            kwargs['proxy_pass'] = proxy.password
        if getattr(awscfg, 'iam_assume_role', None):
            (akey, skey, tkey, expiry, emsg) = self._get_iam_keys(awscfg.region, kwargs.get('aws_access_key_id'),
                kwargs.get('aws_secret_access_key'), xrole=awscfg.iam_assume_role, expsecs=expsecs,
                pxhost=kwargs.get('proxy'), pxport=kwargs.get('proxy_port'),
                pxuser=kwargs.get('proxy_user'), pxpass=kwargs.get('proxy_pass'))
            kwargs['aws_access_key_id'] = akey
            kwargs['aws_secret_access_key'] = skey
            kwargs['security_token']    = tkey
        return (kwargs, expiry, emsg)

    def _get_boto3_config(self, kwargs):
        proxy_host = kwargs.get('proxy')
        proxy_port = kwargs.get('proxy_port')
        proxy_user = kwargs.get('proxy_user')
        proxy_pass = kwargs.get('proxy_pass')
        url = None
        if proxy_host and proxy_port:
            url = '%s:%s' % (proxy_host, proxy_port)
            if proxy_user and proxy_pass:
                url = '%s:%s@' % (proxy_user, proxy_pass) + url
        if not url:
            return None
        proxy_dict = {proxy: proxy + '://' + url for proxy in ['http', 'https']}
        config = Config(proxies=proxy_dict)
        return config

    def _get_vpconn(self, cloud):
        cc_cfg = cloud['config']
        proxy = cc_cfg.proxy_configuration
        if not proxy:
            syscfg = self.ds.get_all(db_table_name_from_pb(SystemConfiguration()))[0]
            syscfg = syscfg['config']
            proxy = syscfg.proxy_configuration
        aws_cfg = cc_cfg.aws_configuration
        kwargs, _, emsg = self._get_kwargs(aws_cfg, proxy)
        if emsg:
            print("Can not create AWS SDK client, cloud: %s, error: %s" % (cc_cfg.uuid, emsg))
            return None
        config = self._get_boto3_config(kwargs)
        vpconn = boto3.client('ec2', aws_cfg.region,
            aws_access_key_id=kwargs.get('aws_access_key_id'),
            aws_secret_access_key=kwargs.get('aws_secret_access_key'),
            aws_session_token=kwargs.get('security_token'),
            config=config)
        return vpconn

    def _get_instances(self, vpconn, cc_cfg):
        qfilter = [
            {
                'Name': 'tag:AVICLOUD_UUID',
                'Values': ['%s:%s' % (cc_cfg.name, cc_cfg.uuid)]
            },
            {
                'Name': "vpc-id",
                "Values": [cc_cfg.aws_configuration.vpc_id]
            }
        ]
        all_instances = []
        next_token = None
        while True:
            if next_token:
                instances = vpconn.describe_instances(Filters=qfilter,
                    NextToken=next_token, MaxResults=1000)
            else:
                instances = vpconn.describe_instances(Filters=qfilter,
                    MaxResults=1000)
            all_instances.extend(instances.get('Reservations', []))
            next_token = instances.get('NextToken')
            if next_token is None:
                break
        return all_instances

    def _get_se_ips(self, vpconn, cc_cfg):
        se_ips = []
        reservations = self._get_instances(vpconn, cc_cfg)
        for resv in reservations:
            for ins in resv['Instances']:
                if ins.get('PrivateIpAddress'):
                    se_ips.append(ins.get('PrivateIpAddress'))
        return se_ips


    def _get_se_root_volumes(self, vpconn, cc_cfg):
        reservations = self._get_instances(vpconn, cc_cfg)
        volume_ids = []
        for resv in reservations:
            for ins in resv['Instances']:
                for bdm in ins['BlockDeviceMappings']:
                    if bdm['DeviceName'] == ins['RootDeviceName']:
                        volume_ids.append(bdm['Ebs']['VolumeId'])
        if len(volume_ids) == 0:
            return None
        volumes = vpconn.describe_volumes(VolumeIds=volume_ids)
        volume_sizes = {vol['VolumeId']:vol['Size'] for vol in volumes['Volumes']}
        return volume_sizes

    def _modify_se_root_disk_size(self, vpconn, volumes, target_size):
        for volume, vsize in volumes.items():
            try:
                if vsize >= target_size:
                    continue
                print("Updating the volume {} from {}GB to {}GB".format(volume, vsize, target_size))
                vpconn.modify_volume(VolumeId=volume, Size=target_size)
                time.sleep(1)
            except Exception as e:
                print("Failed to update the volume {}, error: {}".format(volume, str(e)))

    def handle(self, args):
        try:
            clouds = self.ds.get_all(db_table_name_from_pb(Cloud()))
        except Exception as e:
            print('Failed to get Clouds from Datastore, error: {}'.format(str(e)))
            return
        for cloud in clouds:
            try:
                cc_cfg = cloud['config']
                if cc_cfg.vtype != common_pb2.CLOUD_AWS:
                    continue
                vpconn = self._get_vpconn(cloud)
                if not vpconn:
                    continue
                if args.list_se_ips:
                    ips = self._get_se_ips(vpconn, cc_cfg)
                    for ip in ips:
                        print(ip)
                volumes = self._get_se_root_volumes(vpconn, cc_cfg)
                if not volumes:
                    continue
                if args.list_volumes:
                    print('{} - {}'.format(cc_cfg.name, cc_cfg.uuid))
                    for key, val in volumes.items():
                        print(key, val)
                if args.size:
                    self._modify_se_root_disk_size(vpconn, volumes, args.size)
            except Exception as e:
                print("Observed failure for cloud, uuid: {}, error: {}".format(cloud['config'].uuid, str(e)))


def args_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list-volumes', action='store_true',
        help='List all SE root volumes')
    parser.add_argument('-s', '--size', default=0, type=int,
        help='Target size in GB for SE volumes')
    parser.add_argument('--list-se-ips', action='store_true',
        help='List all SE IPs')
    return parser.parse_args()

if __name__ == "__main__":
    args = args_parse()
    handler = AwsObjectsHandler()
    handler.handle(args)
