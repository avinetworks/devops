#!/usr/bin/python
#pylint:  skip-file

import sys, os
if __name__ != "__main__":
    sys.exit(0)

import django
from django.conf import settings
from django.apps import apps
import simplejson

print "# Script to list objects which would cause issue during full system export or upgrade due to non-ASCII characters in names"
    
os.environ['DJANGO_SETTINGS_MODULE'] = 'portal.settings_full'
sys.path.append("/opt/avi/python/bin/portal")
if not apps.ready and not settings.configured:
    django.setup()

from avi.rest.view_utils import get_model_from_name
from api.models import config_models
config_model_list = config_models[:]

error_list = []
max_model_name_len = 0
max_model_field_len = 0
max_model_uuid_len = 0

for model_name in config_model_list:
    model = get_model_from_name(model_name)
    if 'name' not in model._meta.get_all_field_names():
        continue
    try:
        query = "select id,uuid,name from %s;"%(model._meta.db_table)
        rows = model.objects.raw(query)
    except:
        continue
    for row in rows:
        name = row.name
        uuid = row.uuid
        try:
            str(name)
        except UnicodeEncodeError as e:
            error_list.append([model_name,name,uuid])
            if max_model_name_len < len(model_name):
                max_model_name_len = len(model_name)
            if max_model_field_len < len(name):
                max_model_field_len = len(name)
            if max_model_uuid_len < len(uuid):
                max_model_uuid_len = len(uuid)

print ""
for rec in error_list:
    print " " + rec[0].ljust(max_model_name_len+5,' ') + rec[1].ljust(max_model_field_len+5,' ') + rec[2].ljust(max_model_uuid_len+5,' ')

sys.exit(0)

