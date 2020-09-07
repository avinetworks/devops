#!/bin/bash 

function main {
                 init "$@"
                 if [[ "$#" -eq 10 ]]; then
                      echo "Configuration Deployment Started...."
                      echo 
                      requirements
		      echo ****************************************
		      echo * MAKE SURE TO SET PYTHONPATH.         *
		      echo * export PYTHONPATH=${PWD}:$PYTHONPATH *
		      echo ****************************************
		      echo
                      controller
                 else 
                     usage
                 fi
}


function requirements {
  python3 -m pip install avisdk
  python3 -m pip install pyvim
  python3 -m pip install pyvmomi
  ansible-galaxy install avinetworks.avisdk --force
  ansible-galaxy install avinetworks.aviconfig --force
  ansible-galaxy install avinetworks.avicontroller_vmware --force
  ansible-galaxy collection install community.vmware --force
  python3 -m pip install --upgrade git+https://github.com/vmware/vsphere-automation-sdk-python.git
}

function controller {
     ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook controller_update.yaml -e nsxt_url=$nsxt_url_ip -e router_mgmt_ip=$router_mgmt_ip -e controller_ip=$controller_ip -e controller_password=$controller_password -e vcenter_ip=$vcenter_ip -vv

}

function usage {
               cat <<EOF    
    usage:
    
        -h help
        -n nsxt_url_ip
        -r router_mgmt_ip
        -c controller_ip
        -p controller_password
        -v vcenter_ip

        ./create.sh -n nsxt_url_ip -r router_mgmt_ip -c controller_ip -p controller_password -v vcenter_ip
 
EOF
}

function init {
nsxt_url_ip=""
router_mgmt_ip=""
controller_ip=""
controller_password=""
vcenter_ip=""

while getopts h:n:r:c:p:v: option;
do 
    case "${option}" in
        h) usage "";exit 1
            ;;
        n) nsxt_url_ip=$OPTARG
            ;;
	r) router_mgmt_ip=$OPTARG
	    ;;
	c) controller_ip=$OPTARG
	   ;;
	p) controller_password=$OPTARG
	   ;;
        v) vcenter_ip=$OPTARG
            ;;
        \?) usage "";exit 1
            ;;
    esac
done
}
main "$@"
