
## Avi Controller API Proxy

Avi Controller API Proxy enables users to connect securely to the Avi Controller API server. It uses Avi's goSDK internally for authentication and cookie based session management.  
***
**Build and Run**
`$ docker image build -t avi-api-proxy:latest .`

`$ docker run --name avi-api-proxy -p <hostport>:8080 \`<br/>
`-e AVI_CONTROLLER=<cluserip> \`<br/>
`-e AVI_USERNAME=<username> \`<br/>
`-e AVI_PASSWORD=<password> \`<br/>
`-e AVI_TIMEOUT=60 \`<br/>
`-dit avi-api-proxy:latest`<br/>
***

Note: AVI_TIMEOUT metric is in seconds, so AVI_TIMEOUT=60 means 60 seconds.


**To pass a CA cert file to enable a TLS connection to the controller**
On your host machine
`$ mkdir <ca/cert/directory>`

Pass the following options with the docker run command 
`-v <ca/cert/directory>:/avi/cacert \`<br/>
`-e AVI_TLS_ENABLED=true \ `<br/>
`-e AVI_CACERT_FILE=<cacertfilename>`<br/>

Ensure that \<cacertfilename\> is inside <ca/cert/directory>
***
The avi-api-proxy docker container, by default, runs in a separate network namespace
and connects to the docker bridge network by default.
To run the proxy in the same network namespace as your host machine
`--network=host`
To run the proxy in the same network namespace as your docker container application
`--network=container:<name>`

