#!/bin/bash

if [ $# -lt 2 ]
then
echo "Useage: create-avi-secret.sh <username> <password>"
exit
fi


USER=`echo -n $1 | base64`
PASS=`echo -n $2 | base64`

cat > ./avicontroller-secret.yml << EOL
apiVersion: v1
kind: Secret
metadata:
  name: avicontroller-secret
  namespace: default
type: Opaque
data:
  username: $USER
  password: $PASS
EOL

echo "File created: $(pwd)/avicontroller-secret.yml"
