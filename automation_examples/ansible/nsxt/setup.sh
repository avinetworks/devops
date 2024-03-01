#!/bin/bash
echo "******************************************"
echo "* MAKE SURE TO SET PYTHONPATH.           *"
echo "* export PYTHONPATH=\${PWD}:\$PYTHONPATH   *"
echo "******************************************"
echo
python3 -m pip install avisdk
python3 -m pip install pyvim
python3 -m pip install pyvmomi
ansible-galaxy install avinetworks.avisdk --force
ansible-galaxy install avinetworks.aviconfig --force
ansible-galaxy install avinetworks.avicontroller_vmware --force
ansible-galaxy collection install community.vmware --force
python3 -m pip install --upgrade git+https://github.com/vmware/vsphere-automation-sdk-python.git
