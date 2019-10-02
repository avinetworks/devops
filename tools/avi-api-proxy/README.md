
## Avi Controller Proxy

Avi Controller Proxy enables users to connect securely to the Avi Controller API server. It uses Avi's goSDK internally for authentication and cookie based session management.  
***
**Build and Run**
`$ make build`

`$ docker image build -t avi_proxy:latest .`

`$ docker run --name avi_proxy -p <hostport>:8080 \`
`-e AVI_CONTROLLER=<cluserip> \`
`-e AVI_USERNAME=<username> \`
`-e AVI_PASSWORD=<password> \`
`-dit avi_proxy:latest`
***
**To pass a CA cert file to enable a TLS connection to the controller**
On your host machine
`$ mkdir <ca/cert/directory>`

Pass the following options with the docker run command 
`-v <ca/cert/directory>:/avi/cacert \`
`-e AVI_TLS_ENABLED=true \ `
`-e AVI_CACERT_FILE=<cacertfilename>`

Ensure that \<cacertfilename\> is inside <ca/cert/directory>
***
The avi_proxy docker container, by default, runs in a separate network namespace
and connects to the docker bridge network by default.
To run the proxy in the same network namespace as your host machine
`--network=host`
To run the proxy in the same network namespace as your docker container application
`--network=container:<name>`

