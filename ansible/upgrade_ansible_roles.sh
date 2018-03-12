#!/bin/bash

echo "Please enter role name without 'avinetworks.' "
read -p "Enter Role Name:" role_name

ansible-galaxy remove avinetworks.${role_name}
ansible-galaxy install avinetworks.${role_name}
