# Locust files for testing Avi functionality

This is a collection of [locust](https://locust.io/) files for testing and demonstrating Avi features.

Most of them require a customized version of [Requests Toolbelt](https://github.com/requests/toolbelt) that's included in this folder.  This is needed to be able to spoof source IP addresses as well as set specific TLS and cipher parameters for the connection.

Notes:
- A file that contains "spoof" in the title will spoof the source IP to specific IPs in the locust file, so they will require layer 2 adjacency in order for return traffic to work.  
- A file containing "true client ip" will set an X-Forwarded-For header with the simulated client IP, and will require True Client IP to be configured on the virtual service to get the expected results.  These will also try to derive the IP of the host to be used as the sourceIP
- Hackazon files are meant to be run against a back end [Hackazon](https://github.com/rapid7/hackazon) server
- DVWA files are meant to be run against a back end [dvwa](https://github.com/digininja/DVWA) server
- Avidemo files are meant to be run against the [Avi demo](https://github.com/avinetworks/devops/traffic_generators/demo_web_server) webserver 
