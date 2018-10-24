#!/usr/bin/env bash
{
    if [ ! -d "$(pwd)/avi" ]; then
        echo  "'avi' directory not found. If you want to run the configurations please create a directory name as "avi" inside the avitools/scripts and put your configuration files into it. "
        exit 1
    fi
    AVITOOLS_DOCKER_IMAGE=avinetworks/avitools:latest
    echo "Using Avitools docker image: $AVITOOLS_DOCKER_IMAGE with args: ${@}"

    if [ $# -eq 0 ]; then
        docker run --rm -w /root/avi -v $(pwd)/avi/:/root/avi \
        "$AVITOOLS_DOCKER_IMAGE" "avitools-list"
    else
        docker run --rm -w /root/avi -v $(pwd)/avi/:/root/avi \
        "$AVITOOLS_DOCKER_IMAGE" "${@}"
    fi
}