output "vsphere_virtual_machine_vm1" {
  value = vsphere_virtual_machine.vm[0].guest_ip_addresses[0]
}

output "vsphere_virtual_machine_vm2" {
  value = vsphere_virtual_machine.vm[1].guest_ip_addresses[0]
}

output "vsphere_virtual_machine_vm3" {
  value = vsphere_virtual_machine.vm[2].guest_ip_addresses[0]
}

