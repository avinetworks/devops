############################################################
# Dockerfile to build python avi-monitor script container
# Based on alpine:edge
############################################################

# Set the base image to alpine:edge
FROM alpine:edge

# Set the working directory
WORKDIR /usr/src/avi

# File Author / Maintainer
MAINTAINER mkarnowski@avinetworks.com


################## BEGIN INSTALLATION ######################

# Set Docker environment variable
ENV EN_DOCKER=True


# Install python requirements
RUN apk add --no-cache python python-dev py-pip redis supervisor
RUN pip install --no-cache-dir requests flask redis gunicorn
RUN touch /etc/supervisord.log
RUN chmod 777 /etc/supervisord.log
RUN chmod 777 /usr/src/avi



# Copy scripts to directory
COPY "prometheus_exporter.py" "/usr/src/avi"
COPY "virtualservice_static.py" "/usr/src/avi/virtualservice_static.py"
COPY "serviceengine_static.py" "/usr/src/avi"
COPY "servicediscovery.py" "/usr/src/avi"
COPY "pool_static.py" "/usr/src/avi"
COPY "controller_static.py" "/usr/src/avi"
COPY "supervisord.conf" "/etc"

EXPOSE 8080/tcp


# Execute script
#CMD ["python", "/usr/src/avi/prometheus_exporter.py"]
ENTRYPOINT ["/usr/bin/supervisord"]



