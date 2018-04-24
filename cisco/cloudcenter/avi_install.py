#!/usr/bin/env python
import os
from subprocess import STDOUT, check_call
import pip
import sys



pip_sources = [
    'urllib3',
    'argparse',
    'requests',
    ]


def install_packages():
    global pip_sources
    for pip_pkg in pip_sources:
        pip.main(['install', pip_pkg])


if __name__ == '__main__':
    try:
        print 'avi install'
        install_packages()
        from avi_python_client import execute_avi
        action = 'START' if len(sys.argv) < 2 else sys.argv[1].upper()
        execute_avi(action)
    except Exception as e:
        print e
        f = open('FAILURE','w')
        f.write(str(e))
        f.close()
