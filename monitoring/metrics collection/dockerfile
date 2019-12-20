############################################################
# Dockerfile to build python metrics collection script container
# Based on alpine:edge
############################################################

# Set the base image to alpine:edge
FROM alpine:3.10

# Set the working directory
WORKDIR /usr/src/avi

# File Author / Maintainer
MAINTAINER mkarnowski@avinetworks.com


################## BEGIN INSTALLATION ######################

# Set Docker environment variable
ENV EN_DOCKER=True


# Install python requirements
RUN apk add --no-cache python3 python3-dev py3-pip
RUN pip3 install --no-cache-dir requests pyyaml


# Copy scripts to directory
COPY "configuration_example.yaml" "/usr/src/avi"
COPY "metricscollection.py" "/usr/src/avi"





# Execute script
CMD ["python3", "/usr/src/avi/metricscollection.py"]
