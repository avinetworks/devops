#####################################################################################
#  Script to get max CPU usage by Avi SEs over given time period
#  usage: python core_useage.py [-h] [-v AVI_VERSION] [-s STARTDATE] [-e ENDDATE]
#                        [-d DAYS]
#                        avi_ip avi_user avi_password
#  
#  Get max CPU usage.
#  
#  positional arguments:
#    avi_ip                IP address of Avi Controller Leader or Cluster IP
#    avi_user              Avi username
#    avi_password          Avi password
#  
#  optional arguments:
#    -h, --help            show this help message and exit
#    -v AVI_VERSION, --avi_version AVI_VERSION
#                          Avi version
#    -s STARTDATE, --startdate STARTDATE
#                          The Start Date - format YYYY-MM-DD (Inclusive)
#    -e ENDDATE, --enddate ENDDATE
#                          The End Date format YYYY-MM-DD (Inclusive)
#    -d DAYS, --days DAYS  Number of days from startdate for before enddate
#
#  Eg. for maximum usage for month of August 2019
#      python core_useage.py 10.56.0.82 admin password -s 2019-08-01 -e 2019-08-31
#
#  Eg. for maximum usage for 31 days starting 2019-08-01
#      python core_useage.py 10.56.0.82 admin password -s 2019-08-01 -d 31
#
#  Requires Avi SDK installed:
#      pip install avisdk
#
#####################################################################################

from avi.sdk.avi_api import ApiSession
import json
import requests
import argparse
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class AviUsage:
    
    # Authenticates with Avi controller API and sets the SSL session
    def __init__(self, avi_ip, avi_user, avi_pswd, avi_version):
        self.avi_api = ApiSession(avi_ip, avi_user, avi_pswd, api_version = avi_version)


    # Runs the API and gets the statis
    def get_max_core_usage(self, sdate, edate, limit):
        metrics_api = "/analytics/metrics/controller"
        params = {
            'metric_id': 'controller_stats.max_num_se_cores',
            'step': 86400,
            'start': sdate,
            'stop': edate,
            'limit': limit,
            'pad_missing_data': 'false'
        }

        ret = self.avi_api.get(path = metrics_api, params = params)
        #print(json.dumps(ret.json()))
        count = ret.json()['count']
        if count > 0:
            max_usage = ret.json()['results'][0]['series'][0]['header']['statistics']['max']
            min_usage = ret.json()['results'][0]['series'][0]['header']['statistics']['min']
            sdate = ret.json()['results'][0]['series'][0]['header']['statistics']['min_ts']
            edate = ret.json()['results'][0]['series'][0]['header']['statistics']['max_ts']
            return (max_usage, min_usage, sdate, edate)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Get CPU usage.')
    parser.add_argument('avi_ip', help = 'IP address of Avi Controller Leader or Cluster IP')
    parser.add_argument('avi_user', help = 'Avi username')
    parser.add_argument('avi_password', help = 'Avi password')
    parser.add_argument('-v', '--avi_version', help = 'Avi version', default = '18.2.5')
    parser.add_argument('-s', "--startdate", help="The Start Date - format YYYY-MM-DD (Inclusive)")
    parser.add_argument('-e', "--enddate", help="The End Date format YYYY-MM-DD (Inclusive)")
    parser.add_argument('-d', "--days", help="Number of days from startdate for before enddate", default = '30')
    args = parser.parse_args()
    usg = AviUsage(args.avi_ip, args.avi_user, args.avi_password, args.avi_version)
    (max_cpu, min_cpu, sdate, edate) = usg.get_max_core_usage(args.startdate, args.enddate, args.days)
    print('CPU usage between %s and %s:' % (sdate, edate))
    print("  Max CPU: %s" % max_cpu)
    print("  Min CPU: %s" % min_cpu)
