# KVM installation helper scripts

Please ensure the following pre-requisites are in place before trying to bring up the SE guest VM on Linux KVM/QEMU

1. Ensure CPU virtualization extension is available. It can be checked via /proc/cpuinfo output.
2. Please copy over se.qcow2 & controller.qcow2 images to /var/lib/libvirt/images/ directory.
3. Ensure qemu-kvm & virsh packages are installed.