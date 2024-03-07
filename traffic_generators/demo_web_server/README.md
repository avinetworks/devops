# Demo webserver

A webserver based on the original Avi webpage that we use internally for testing and demos.  This should be run as a container and environment variables can be passed to the container to modify behavior.

if NOLOGO == "yes"  then /imgs/logo.png will be removed to simulate 404 errors

if APPLATENCY" == "no" then the web server will artificially increase response times every 6 hours to simulate a broken appserver.