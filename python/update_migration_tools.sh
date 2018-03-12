#!/usr/bin/env bash

if [ -z "$1" ]; then
  read -p "Enter Desired SDK Version: " MGRTN_VERSION
else
  MGRTN_VERSION=$1
fi

echo "Upgrading sdk to $MGRTN_VERSION"
sudo pip install -U avisdk==$MGRTN_VERSION avimigrationtools==$MGRTN_VERSION
sudo rm -rf /opt/avi/python/lib/avi/sdk
sudo ln -s /usr/local/lib/python2.7/dist-packages/avi/sdk /opt/avi/python/lib/avi/sdk
sudo rm -rf /opt/avi/python/lib/avi/migrationtools
sudo ln -s /usr/local/lib/python2.7/dist-packages/avi/migrationtools /opt/avi/python/lib/avi/migrationtools
