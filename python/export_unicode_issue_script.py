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
from api.models import pb_ordered
from avi.config_migration.export_import import custom_models

all_model_list = pb_ordered + custom_models
error_list = []
max_model_name_len = 0
max_model_field_len = 0
max_model_uuid_len = 0

for model_name in all_model_list:
    model = get_model_from_name(model_name)
    try:
        if 'name' not in model._meta.get_all_field_names():
            continue
        if 'uuid' not in model._meta.get_all_field_names():
            continue
    except AttributeError:
        pass
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

