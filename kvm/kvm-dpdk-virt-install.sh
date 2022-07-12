#!/bin/bash -x 

printf "\n Please ensure the following before trying to bringup guest VM on Linux KVM/QEMU\n"
printf "PRE-REQ:\n"
printf "1. Ensure CPU virtualization extension is available. It can be checked by via /proc/cpuinfo output.\n"
printf "2. Please copy over se.qcow2 & controller.qcow2 images to /var/lib/libvirt/images/ directory.\n"
printf "3. Ensure qemu-kvm & virsh packages are installed.\n\n"

read -p "Enter y/n to continue (y/[N])? " -r
if [[ $REPLY =~ ^[Nn]$ ]]; then
    exit 1
fi

printf "Do you want to create: \n1) Create AVI Service Engine VM,  2) Create AVI Controller VM, 3) Destroy AVI Service Engine VM,  4) Destroy AVI Controller VM\n[Enter 1/2/3/4]: "
read option
echo -n "Enter VM name: "
read vm_name

if [ $option -eq 3 ] || [ $option -eq 4 ]; then
	virsh destroy $vm_name
	virsh undefine $vm_name
	rm -rf /var/lib/libvirt/images/$vm_name.qcow2
    	rm -rf /var/lib/libvirt/images/$vm_name
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
DIR=/var/lib/libvirt/images/

if [ $option -eq 1 ]; then
    # Location of cloud image
    IMAGE=$DIR/$vm_name.qcow2
    cp $DIR/se.qcow2 $IMAGE
    
    # Start clean
    rm -rf $DIR/$vm_name
    mkdir -p $DIR/$vm_name
    
    pushd $DIR/$vm_name > /dev/null
    
	    # Number of virtual CPUs
        echo -n "Enter num of vcpus for the VM [Recommended to configure num vcpus >= num queues planned per macvtap interface]: "
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
        
        echo -n "Enter AVI Controller IP: "
        read ctlr_ip
	echo "AVICNTRL: $ctlr_ip" >> $META_DATA 
        
	echo -n "Enter AVI Controller Auth-Token: "
        read auth_tkn
        echo "AVICNTRL_AUTHTOKEN: $auth_tkn" >> $META_DATA 
        
        echo -n "Enter AVI SE Mgmt IP: "
        read se_mgmt_ip
        echo "avi.mgmt-ip.SE: $se_mgmt_ip" >> $META_DATA 
        
        echo -n "Enter AVI SE Mgmt-IP Mask: "
        read se_mgmt_mask
        echo "avi.mgmt-mask.SE: $se_mgmt_mask" >> $META_DATA 
        
        echo -n "Enter AVI SE Default Gateway: "
        read se_def_gw
        echo "avi.default-gw.SE: $se_def_gw" >> $META_DATA 
	    
	echo -n "Enter num of parent interfaces from which macvtap intf individually will be created for guest VM: "
        read num_parent_intf
	    while [ $num_parent_intf -gt 0 ]; do
            echo -n "Enter parent interface name from which macvtap intf is to be created for guest VM: "
            read parent_intf_name
	        echo -n "Enter num of child macvtap intf from this parent interface for guest VM: "
            read num_dev
	        while [ $num_dev -gt 0 ]; do
		        nwk_dv_str="$nwk_dv_str --network type=direct,source=$parent_intf_name,source_mode=bridge,model=virtio"
		        echo $nwk_dv_str
		        let num_dev=num_dev-1 
	        done
            let num_parent_intf=num_parent_intf-1 
	    done
        
	echo -n "Enter num of queues (in power of 2 upto max 16) per macvtap intf [Recommended value is 4 for best performance]: "
        read queue_num
        
	echo -n "Enter bond-ifs sequence [Enter 0 if no bond-scenario]"
    	read bond_seq
	    if [ "$bond_seq" != "0" ]; then
            echo "avi.bond-ifs.SE: $bond_seq" >> $META_DATA 
	    fi

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
        	virt-install --noreboot --import --name $vm_name --ram $MEM --vcpus $CPUS --disk \
        	$IMAGE,format=qcow2,bus=virtio,size=$disk_size --check all=off --disk $CI_ISO,device=cdrom --network \
        	type=direct,source=$host_mgmt_intf,source_mode=bridge,model=virtio $nwk_dv_str --os-type=linux --noautoconsole
	
	virsh dumpxml $vm_name > /etc/libvirt/qemu/$vm_name.xml
	sed -i "/interface type='direct'/a \      \<driver name=\'vhost' queues=\'$queue_num'/>" /etc/libvirt/qemu/$vm_name.xml
	virsh define /etc/libvirt/qemu/$vm_name.xml
	virsh start $vm_name
        
	# Eject cdrom
        virsh change-media $vm_name hda --eject --config >> $vm_name.log
	
        # Remove the unnecessary cloud init files
        rm $USER_DATA $CI_ISO
        
    popd > /dev/null

elif [ $option -eq 2 ]; then
    # Location of cloud image
    IMAGE=$DIR/$vm_name.qcow2
    cp $DIR/controller.qcow2 $IMAGE
    
    # Start clean
    rm -rf $DIR/$vm_name
    mkdir -p $DIR/$vm_name
    
    pushd $DIR/$vm_name > /dev/null
        
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
        
        	virt-install --import --name $vm_name --ram $MEM --vcpus $CPUS --disk \
        	$IMAGE,format=qcow2,bus=virtio,size=$disk_size --disk $CI_ISO,device=cdrom --network \
        	type=direct,source=$host_mgmt_intf,source_mode=bridge,model=virtio --os-type=linux --noautoconsole
        # Eject cdrom
        virsh change-media $vm_name hda --eject --config >> $vm_name.log
        
        # Remove the unnecessary cloud init files
        rm $USER_DATA $CI_ISO
        
    popd > /dev/null
fi
