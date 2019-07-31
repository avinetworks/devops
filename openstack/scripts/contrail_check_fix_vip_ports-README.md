What
----
This script does sanity check on Virtual Services VIP ports. It will
report the Virtual Service VIP ports that are not having expected
configuration. When run with `--fix` flag, it will also fix the VIP port
configuration to match the expectation.

This script is meant to be used in OpenStack Contrail environment where
Avi Controller is configured with OpenStack cloud.

Contrail Versions: 3.2.x onwards.

Why
----

In the older versions of Avi (below 18.1.5), Virtual Service VIP
Addresses were moved from VIP port to SE Data Ports. When the Service
Engines get deleted from OpenStack (due to some user activity or other
reasons), and the SE Data ports are deleted from OpenStack, the VIP IP
addresses also get deleted. The VIP addresses are not available on VIP
Ports. Disable/Enable action on Virtual Services backed by such ports
will fail due to unavailability of IP address on the port.

In Avi versions starting from 18.2.x, the VIP address is kept on both
the SE data ports and the VIP ports. Deletion of SE ports will not cause
issues.

This script fixes the issues caused by above mentioned scenarios.

NOTE: This issue of failing to disable/enable the Virtual Service is
also seen when VIP ports are deleted from OpenStack cloud. This script
*WILL NOT* fix such VIP ports.


How to use
----
1. Copy the script on Avi Controller leader node to
'/opt/avi/python/bin/cloud_connector' directory.
2. Run the script using `python contrail_check_fix_vip_ports.py`
3. Find help using `-h` option, and run accordingly.


Assumption
----------
You can run the script anytime to check the if there are any VIP ports
that doesn't match expected configuration. However, if you have to 'fix'
the VIP ports it is expected that there are no actions happening on the
Virtual Service. Preferably, run this script in a maintenance window.
