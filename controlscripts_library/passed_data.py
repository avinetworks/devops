#!/usr/bin/python
#
# Sample Avi Networks controlscript
#
# This sample can be used as a guide to detail environment variables
# and arguments passed to your controlscripts
#
# Once this script is in place and the alerts configured and fired
# reports are stored on the lead controller /tmp/controlscript.log
#
# Be careful, this may output sensitive data

import os
import sys

with open('/tmp/controlscript.log', 'a') as fh:
        fh.write('\nENV_VARS\n')
        for k in os.environ.keys():
                fh.write("%s: %s\n" % (k, os.environ[k]))

        fh.write('CMD_ARGS\n')
        for i,v in enumerate(sys.argv):
                fh.write("%s: %s\n" % (i, v))