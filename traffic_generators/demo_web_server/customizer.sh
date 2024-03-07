#!/bin/sh

if [ "$NOLOGO" == "yes" ]; then
    rm -rf /imgs/logo.png
fi

if [ "$APPLATENCY" == "no" ]; then
    sed -i.bak -e 's*setTimeout(function() {*//&*' -e 's*}, appResponse());*//&*' webserver.js
fi