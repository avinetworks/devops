#!/usr/bin/env python
#!/usr/bin/python3
############################################################################
# ========================================================================
# Copyright 2023 VMware, Inc. All rights reserved. VMware Confidential
# ========================================================================
###

import sys, os, django

sys.path.append('/opt/avi/python/bin/portal')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal.settings_full')

import yaml
from api.models import ControllerPortalRegistration
from api.models import LicenseStatus # Comment out for versions lower than 21.1.3
from api.models import ControllerLicense
from avi.infrastructure.datastore import Datastore

django.setup()


VERSION_FILE_PATH = "/bootstrap/VERSION"
def get_controller_version():
    try:
        with open(VERSION_FILE_PATH, 'r') as file:
            ctrlr_props = file.read()
    except IOError as err:
        print(f"Error while opening version file. Error: {err}")
        return ""

    try:
        c = yaml.safe_load(ctrlr_props)
        controller_version = c.get("Version", "")
        return controller_version
    except yaml.YAMLError as err:
        print(f"Error parsing YAML: {err}")
        return ""


if __name__ == '__main__':
    ds = Datastore()

    for cpr in ControllerPortalRegistration.objects.all():
        cpr.delete()
    
    controller_version = get_controller_version()
    print(f"Controller version is : {controller_version}")

    if controller_version >= "21.1.3":
        # Delete license status object
        for ls in LicenseStatus.objects.all():
            ls.delete() 

        # Delete only virtual licenses from the database
        for controllerLicense in ControllerLicense.objects.all():
            filteredLicenses = []
            for license in controllerLicense.json_data['licenses']:
                if(license['license_type'] != "Virtual"):
                    filteredLicenses.append(license)

            controllerLicense.json_data['licenses'] = filteredLicenses
            
            
            # Save the modified license back to the database
            controllerLicense.save()
            controllerLicense.save_pb()

            ds.save('controllerlicense', controllerLicense.json_data['uuid'], controllerLicense.protobuf(), None)


        # Delete all licenses from datastore (Deleting licenses from datastore deleting licenses from DB also)

    os.system("systemctl restart license_mgr")
    os.system("systemctl restart portalconnector")
    print("Cleaned up registration state")

