'''
    Starting from the ALB Version 20.1.6 and 21.1.1 the name of the Config Objects Length Cannot Exceed more than 256 characters.


    Before Upgrading to versions 20.1.6, 21.1.1 and above we will have to identify the Objects whose name is greater than 256 characters and reduce the length of such objects.


    This Python Script Will help in identifying the objects name.

    root@controller:/home/admin# python3 show-object-name-more-than-256-chars.py -h
	usage: show-object-name-more-than-256-chars.py [-h] [-c AVI_CONFIG] [-l OBJ_LENGTH]
	optional arguments:
		-h, --help show this help message and exit
		-c AVI_CONFIG, --avi_config AVI_CONFIG
		Avi Controller Configuration file
		-l OBJ_LENGTH, --obj_length OBJ_LENGTH
		Length of the object names
'''

#!/usr/bin/python3
import os
import sys
from pprint import pprint
import json
import argparse
from avi.sdk.avi_api import ApiSession
import urllib3
urllib3.disable_warnings()

class SetupData(): pass
setupdata = SetupData()

def init_setupdata():
    setupdata.controller = {}
    setupdata.params = {}
    setupdata.data = {}

def load_avi_config():
    config_file = setupdata.params.get('avi_config')
    try:
        avi_config = json.load(open(config_file, 'r'))
    except Exception as err:
        print('Error: Hit error while loading config - %s' % err)
    setupdata.data['avi_config'] = avi_config
    pass

def display_fix_config_details():
    fix_config = setupdata.data['fix_config']
    length = setupdata.params['obj_length']
    if fix_config:
        print("INFO: %s objects has obj name length greater than %s\n" % (', '.join(fix_config.keys()), length))
        parsed_config = []
        for ckey in fix_config.keys():
            print(ckey+' Name'+': ','\n\n'.join([x['name'] for x in fix_config[ckey]]),'\n')
    else:
        print("INFO: No config objects has names greater than %s" % length)

def fetch_objects_higher_length():
    avi_config = setupdata.data['avi_config']
    length = setupdata.params['obj_length']
    fix_config = {}
    for obj_key in avi_config.keys():
        if obj_key == 'META': continue
        #if not obj_key == 'AlertSyslogConfig': continue
        for obj in avi_config[obj_key]:
            #import pdb; pdb.set_trace()
            name = obj.get('name')
            if name and len(name) >= length:
                if not obj_key in fix_config:
                    fix_config[obj_key] = []
                fix_config[obj_key].append(obj)
    setupdata.data['fix_config'] = fix_config
    display_fix_config_details()
    pass



def fix_object_name_length():
    # load avi configuration
    load_avi_config()
    # fetch the list of objects that has names greater than 256 chars
    fetch_objects_higher_length()
    pass


def do_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--avi_config", default='./avi_config',
            help="Avi Controller Configuration file")
    parser.add_argument("-l", "--obj_length", default=256,
            help="Length of the object names")

    args = parser.parse_args()
    init_setupdata()
    setupdata.params['avi_config'] = args.avi_config
    setupdata.params['obj_length'] = int(args.obj_length)

    if not os.path.isfile(setupdata.params['avi_config']):
        print('Error: Avi config file %s does not exist - ' % setupdata.params['avi_config'])
        sys.exit(1)

    # invoke fix object name length
    fix_object_name_length()


# Main script execution block
if __name__ == '__main__':
    do_main()

# End of script
