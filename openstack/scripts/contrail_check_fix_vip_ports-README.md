What
----
This script checks for vip ports which doesn't have vip in the
'fixed_ips' field and fixes it on demand.

Why
----
In the older versions, the vip ports relinquishes the ips due
to movement of ip objects.

How
----
This script needs to run on controller node under the directory
'/opt/avi/python/bin/cloud_connector'. For more options, use -h.

Assumption
----------
There should be no VS related operation done in background or
parallel to this script run.
