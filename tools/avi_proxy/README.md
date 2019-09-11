Avi Controller Proxy


make build

docker image build -t avi_proxy:latest .

docker run --name avi_proxy -p <hostport>:8080 \
-e AVI_CONTROLLER=10.52.3.103 \
-e AVI_USERNAME=admin \
-e AVI_PASSWORD=avi123 \
-dit avi_proxy:latest


*To pass a CA cert file to enable a TLS connection to the controller*
On your host machine
mkdir <ca/cert/directory>


Pass the following with the docker run command 
-v <ca/cert/directory>:/avi/cacert \
-e AVI_TLS_ENABLED=true \ 
-e AVI_CACERT_FILE=<cacertfilename>

<cacertfilename> should be in <ca/cert/directory>


The docker container, by default, runs in a separate network namespace
and connects to the docker bridge network by default.
To run the proxy in the same network namespace as your host machine
--network=host
To run the proxy in the same network namespace as your docker container application
--network=container:<name>

