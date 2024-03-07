#!/bin/bash -x 

printf "\nPlease ensure the following before trying to bringup VM on Linux KVM/QEMU\n"
printf "PRE-REQ:\n"
printf "1. Ensure Intel Virtualisation Technology in CPU configuration is Enabled & SRIOV-support in PCI support is Enabled. It can be checked by entering setup mode @ bootup time.\n"
printf "2. In grub config [/etc/default/grub] add intel_iommu=on in GRUB_CMDLINE_LINUX statement. Rebuild grub config via 'sudo update-grub' on Ubuntu distros or via 'grub2-mkconfig -o /boot/grub2/grub.cfg' on others. \nEnsure the same is reflected in 'cat /proc/cmdline' output.\n"
printf "3. Please copy over se.qcow2 & controller.qcow2 images to root directory.\n"
printf "4. Ensure qemu-kvm & virsh packages are installed.\n\n"

read -p "Enter y/n to continue (y/[N])? " -r
if [[ $REPLY =~ ^[Nn]$ ]]; then
    exit 1
fi

printf "Do you want to create: \n1) Create AVI Service Engine VM,  2) Create AVI Controller VM, 3) Destroy AVI Service Engine VM,  4) Destroy AVI Controller VM\n[Enter 1/2/3/4]: "
read option
echo -n "Enter VM name: "
read vm_name

if [ $option -eq 3 ]; then
	virsh destroy $vm_name
	virsh undefine $vm_name
	rm -rf /var/lib/libvirt/images/$vm_name.qcow2
    rm -rf $vm_name
	exit 0
elif [ $option -eq 4 ]; then
	virsh destroy $vm_name
	virsh undefine $vm_name
	rm -rf /var/lib/libvirt/images/$vm_name.qcow2
    rm -rf $vm_name
	exit 0
fi

# Check if domain already exists
virsh dominfo $vm_name > /dev/null 2>&1
if [ "$?" -eq 0 ]; then
    echo -n "[WARNING] $vm_name already exists.  "
    read -p "Do you want to overwrite $vm_name (y/[N])? " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        virsh destroy $vm_name > /dev/null
        virsh undefine $vm_name > /dev/null
    else
        echo -e "\nNot overwriting $vm_name. Exiting..."
        exit 1
    fi
fi

# Directory to store images
DIR=~/

if [ $option -eq 1 ]; then
    # Location of cloud image
    IMAGE=/var/lib/libvirt/images/$vm_name.qcow2
    cp se.qcow2 /var/lib/libvirt/images/
    mv /var/lib/libvirt/images/se.qcow2 $IMAGE
    
    # Start clean
    rm -rf $DIR/$vm_name
    mkdir -p $DIR/$vm_name
    
    pushd $DIR/$vm_name > /dev/null
    
        rm -rf *
        
        # Number of virtual CPUs
        echo -n "Enter num of vcpus for the VM: "
        read CPUS
       	
	    echo -n "Do you want to enable pinning CPU for the VM: "
	    read pinning_option
        # Amount of RAM in MB
        echo -n "Enter RAM[in MB] for the VM: "
        read MEM
        echo -n "Enter disk_size[in GB] for the VM: "
        read disk_size
        
        echo -n "Enter host management interface name: "
        read host_mgmt_intf
        
        # Host Physical Function
        # echo -n "Enter parent interface name from which Virtual Function will be pass-through to VM: "
        # read intf_name
        
        echo -n "Please upfront ensure to correctly configure the VFs being passed in trust mode, mac, vlan\n"
        read -p "Enter y/n to continue if already done the above (y/[N])? " -r
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            exit 1
        fi

	    echo -n "Enter total num VFs will be pass-through to VM: "
        read total_num_vfs
	    while [ $total_num_vfs -gt 0 ]; do
        	echo -n "Enter Virtual Function name will be pass-through to VM: "
        	read virt_intf_name
        	virt_func_bdf=`ethtool -i $virt_intf_name | grep "bus-info" | cut -f2 -d " "`
		    virt_func_bdf="${virt_func_bdf//./_}" 
		    virt_func_bdf="${virt_func_bdf//:/_}" 
        	host_device="pci_$virt_func_bdf"
		    host_dv_str="$host_dv_str --host-device=$host_device"
		    echo $host_dv_str
		    let total_num_vfs=total_num_vfs-1 
	    done

        echo -n "Enter bond-ifs sequence [Enter 0 if no bond-scenario]"
	    read bond_seq
: '	
	    ifup $intf_name 
        phy_func_bdf=`ethtool -i $intf_name | grep "bus-info" | cut -f2 -d " "`
        echo 16 > /sys/bus/pci/devices/$phy_func_bdf/sriov_numvfs
        total_virt_func_bdf=`lspci | grep "Ethernet" | grep "Intel Corporation" | grep "Virtual Function" | egrep  -i "82599|X520|X540|X550|X552|X710|XL710"| head -n16 | cut -d " " -f1`
	    echo $total_virt_func_bdf > bdf_list
	    vf_num=0
	    for word in $total_virt_func_bdf; do
		    #echo "testing bdf: $word"
		    driver_in_use=($(lspci -s $word -vvv | grep "Kernel driver in use" | cut -f5 -d " "))
		    #echo "driver_in_use: $driver_in_use"
		    if [[ $driver_in_use == "vfio-pci" ]]; then
			    vf_num=$((vf_num + 1))
			    continue	
		    fi
		    virt_func_bdf="$word"
		    break
	    done 
	    #echo "chosen virtual function: $virt_func_bdf"
	virt_func_bdf="${virt_func_bdf//./_}" 
	virt_func_bdf="${virt_func_bdf//:/_}"
        host_device="pci_0000_$virt_func_bdf"
'
        
        # Cloud init files
        USER_DATA=user-data
        META_DATA=avi_meta-data
        CI_ISO=/var/lib/libvirt/images/$vm_name-cidata.iso
        
: '	
	# Host Physical Function
        printf "Enter vlan-id in which Virtual Function will be hosted [Enter 0 if a tagged interface will be created from the VF]\n"
        read vf_vlan_id	
 	
	    vf_mac=($(ip link show eno2 | grep "vf $vf_num" | cut -f8 -d " " | sed 's/,$//'))
 	    ifdown $intf_name
	    ip link set dev $intf_name vf $vf_num trust on
	    ip link set $intf_name vf $vf_num vlan 0
	    ip link set $intf_name vf $vf_num vlan $vf_vlan_id
	    ip link set $intf_name vf $vf_num mac $vf_mac
	    ifup $intf_name
'	        
        echo -n "Enter AVI Controller IP: "
        read ctlr_ip
        echo "AVICNTRL: $ctlr_ip" >> $META_DATA 
        
        echo -n "Enter AVI Controller Auth-Token: "
        read auth_tkn
        echo "AVICNTRL_AUTHTOKEN: $auth_tkn" >> $META_DATA 
        
	    if [ "$bond_seq" != "0" ]; then
            echo "avi.bond-ifs.SE: $bond_seq" >> $META_DATA 
	    fi
        
        echo -n "Enter AVI SE Mgmt IP: "
        read se_mgmt_ip
        echo "avi.mgmt-ip.SE: $se_mgmt_ip" >> $META_DATA 
        
        echo -n "Enter AVI SE Mgmt-IP Mask: "
        read se_mgmt_mask
        echo "avi.mgmt-mask.SE: $se_mgmt_mask" >> $META_DATA 
        
        echo -n "Enter AVI SE Default Gateway: "
        read se_def_gw
        echo "avi.default-gw.SE: $se_def_gw" >> $META_DATA 
        
        # Create log file
        touch $vm_name.log
        
        cat > $USER_DATA << _EOF_
        #cloud-config
        # Hostname management
        preserve_hostname: False
        hostname: $vm_name
        # Configure where output will go
        output: 
        all: ">> /var/log/cloud-init.log"
_EOF_
        
        # Create CD-ROM ISO with cloud-init config
        echo "$(date -R) Generating ISO for cloud-init..."
        echo "genisoimage -output $CI_ISO -volid cidata -joliet -r $USER_DATA $META_DATA"
        genisoimage -output $CI_ISO -volid cidata -joliet -r $USER_DATA $META_DATA &>> $vm_name.log
        
        echo "$(date -R) Installing the domain and adjusting the configuration..."
        echo "[INFO] Installing with the following parameters:"
        echo "virt-install --import --name $vm_name --ram $MEM --vcpus $CPUS --disk
        $IMAGE,format=qcow2,bus=virtio,size=$disk_size --disk $CI_ISO,device=cdrom --network
        type=direct,source=eno1.100,source_mode=bridge,model=virtio --os-type=linux --os-variant=ubuntu16.04 --noautoconsole $host_dv_str"
        
    	if [[ $pinning_option =~ ^[Yy]$ ]]; then
        	virt-install --import --name $vm_name --ram $MEM --vcpus $CPUS --disk \
        	$IMAGE,format=qcow2,bus=virtio,size=$disk_size --check all=off --disk $CI_ISO,device=cdrom --network \
        	type=direct,source=$host_mgmt_intf,source_mode=bridge,model=virtio --os-type=linux --os-variant=ubuntu16.04 --noautoconsole $host_dv_str --cpuset=auto
	    else
        	virt-install --import --name $vm_name --ram $MEM --vcpus $CPUS --disk \
        	$IMAGE,format=qcow2,bus=virtio,size=$disk_size --check all=off --disk $CI_ISO,device=cdrom --network \
        	type=direct,source=$host_mgmt_intf,source_mode=bridge,model=virtio --os-type=linux --os-variant=ubuntu16.04 --noautoconsole $host_dv_str
	    fi
	
        # Eject cdrom
        virsh change-media $vm_name hda --eject --config >> $vm_name.log
        
        # Remove the unnecessary cloud init files
        rm $USER_DATA $CI_ISO
        
    popd > /dev/null

elif [ $option -eq 2 ]; then
    # Location of cloud image
    IMAGE=/var/lib/libvirt/images/$vm_name.qcow2
    cp controller.qcow2 /var/lib/libvirt/images/
    mv /var/lib/libvirt/images/controller.qcow2 $IMAGE
    
    # Start clean
    rm -rf $DIR/$vm_name
    mkdir -p $DIR/$vm_name
    
    pushd $DIR/$vm_name > /dev/null
        
        rm -rf *
        
        # Number of virtual CPUs
        echo -n "Enter num of vcpus for the VM: "
        read CPUS
        
        # Amount of RAM in MB
        echo -n "Enter RAM[in MB] for the VM: "
        read MEM
        echo -n "Enter disk_size[in GB] for the VM: "
        read disk_size
        
        echo -n "Enter host management interface name: "
        read host_mgmt_intf
        
        # Cloud init files
        USER_DATA=user-data
        META_DATA=avi_meta-data
        CI_ISO=/var/lib/libvirt/images/$vm_name-cidata.iso
        
        #echo "instance-id: $vm_name; local-hostname: $vm_name" >> $META_DATA
        
        echo -n "Enter AVI Controller Mgmt IP: "
        read ctrl_mgmt_ip
        echo "avi.mgmt-ip.CONTROLLER: $ctrl_mgmt_ip" >> $META_DATA 
        
        echo -n "Enter AVI Controller Mgmt-IP Mask: "
        read ctrl_mgmt_mask
        echo "avi.mgmt-mask.CONTROLLER: $ctrl_mgmt_mask" >> $META_DATA 
        
        echo -n "Enter AVI Controller Default Gateway: "
        read ctrl_def_gw
        echo "avi.default-gw.CONTROLLER: $ctrl_def_gw" >> $META_DATA 
        
        # Create log file
        touch $vm_name.log
        
        cat > $USER_DATA << _EOF_
        #cloud-config
        # Hostname management
        preserve_hostname: False
        hostname: $vm_name
        # Configure where output will go
        output: 
          all: ">> /var/log/cloud-init.log"
_EOF_
        
        # Create CD-ROM ISO with cloud-init config
        echo "$(date -R) Generating ISO for cloud-init..."
        echo "genisoimage -output $CI_ISO -volid cidata -joliet -r $USER_DATA $META_DATA"
        genisoimage -output $CI_ISO -volid cidata -joliet -r $USER_DATA $META_DATA &>> $vm_name.log
        
        echo "$(date -R) Installing the domain and adjusting the configuration..."
        echo "[INFO] Installing with the following parameters:"
        echo "virt-install --import --name $vm_name --ram $MEM --vcpus $CPUS --disk
        $IMAGE,format=qcow2,bus=virtio,size=$disk_size --disk $CI_ISO,device=cdrom --network
        type=direct,source=$host_mgmt_intf,source_mode=bridge,model=virtio --os-type=linux --os-variant=ubuntu16.04 --noautoconsole"
        
    	if [[ $pinning_option =~ ^[Yy]$ ]]; then
        	virt-install --import --name $vm_name --ram $MEM --vcpus $CPUS --disk \
        	$IMAGE,format=qcow2,bus=virtio,size=$disk_size --disk $CI_ISO,device=cdrom --network \
        	type=direct,source=$host_mgmt_intf,source_mode=bridge,model=virtio --os-type=linux --os-variant=ubuntu16.04 --noautoconsole --cpuset=auto
	    else
        	virt-install --import --name $vm_name --ram $MEM --vcpus $CPUS --disk \
        	$IMAGE,format=qcow2,bus=virtio,size=$disk_size --disk $CI_ISO,device=cdrom --network \
        	type=direct,source=$host_mgmt_intf,source_mode=bridge,model=virtio --os-type=linux --os-variant=ubuntu16.04 --noautoconsole
	    fi
        
        # Eject cdrom
        virsh change-media $vm_name hda --eject --config >> $vm_name.log
        
        # Remove the unnecessary cloud init files
        rm $USER_DATA $CI_ISO
        
    popd > /dev/null
fi
