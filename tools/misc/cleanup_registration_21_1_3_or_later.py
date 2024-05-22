#!/usr/bin/env python
#!/usr/bin/python3
############################################################################
# ========================================================================
# Copyright 2024 VMware, Inc. All rights reserved. VMware Confidential
# ========================================================================
###

import sys, os, django

sys.path.append('/opt/avi/python/bin/portal')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal.settings_full')

import yaml
from api.models import ControllerPortalRegistration
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

def is_version_less_than(version, target_version):
    version_parts = version.split('.')
    target_parts = target_version.split('.')
    
    if len(version) == 0 or len(version) != 3 :
        return False

    for i in range(min(len(version_parts), len(target_parts))):
        if int(version_parts[i]) < int(target_parts[i]):
            return True
        elif int(version_parts[i]) > int(target_parts[i]):
            return False
    
    return False

if __name__ == '__main__':
    ds = Datastore()

    for cpr in ControllerPortalRegistration.objects.all():
        cpr.delete()
    print("Controller's registration state is cleared.")
    
    controller_version = get_controller_version()
    print(f"Controller version is : {controller_version}")

    if is_version_less_than(controller_version, "21.1.3") :
         print("Controller version is less than 21.1.3 no license clean up needed.")
    else:
        from api.models import LicenseStatus

        # Delete license status object
        for ls in LicenseStatus.objects.all():
            ls.delete() 

        # Delete only virtual licenses from the database
        for controllerLicense in ControllerLicense.objects.all():
            if 'licenses' in controllerLicense.json_data:
                filteredLicenses = []
                for license in controllerLicense.json_data['licenses']:
                    if 'license_type' in license and license['license_type'] != "Virtual" :
                        filteredLicenses.append(license)

                controllerLicense.json_data['licenses'] = filteredLicenses
                
                # Save the modified license back to the database
                controllerLicense.save()
                controllerLicense.save_pb()

                ds.save('controllerlicense', controllerLicense.json_data['uuid'], controllerLicense.protobuf(), None)

        print("Controller's license state is cleared.")
       
    os.system("systemctl restart license_mgr")
    os.system("systemctl restart portalconnector")

