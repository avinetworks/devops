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

from api.models import ControllerPortalRegistration

django.setup()

if __name__ == '__main__':
    for cpr in ControllerPortalRegistration.objects.all():
        cpr.delete()
    os.system("systemctl restart license_mgr")
    os.system("systemctl restart portalconnector")
    print("Cleaned up registration state")

