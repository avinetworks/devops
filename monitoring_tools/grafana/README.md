This folder contains pre-built grafana dashboards for various endpoints which can be connected to grafana for monitoring VMware Avi Load Balancer. 

## graphite

- The sample dashboards can be imported in grafana when using graphitedb along with the metrics collection script

## influxdb

- The sample dashboards can be imported in grafana when using influxdb along with the metrics collection script

## prometheus

- The sample dashboards can be imported in grafana when using prometheus as an endpoint. 
- prometheus should already be integrated with VMware Avi for metrics collection using avi-api-proxy container. 
  Detailed steps are available at : https://docs.vmware.com/en/VMware-NSX-Advanced-Load-Balancer/22.1/Monitoring_Operability_Guide/GUID-4FA0F81D-CA6D-4502-A1D9-2CB0ACFB6D6A.html
- avi api proxy is available to download at https://github.com/avinetworks/devops/tree/master/tools/avi-api-proxy

- There is a sample yaml config (prometheus_sample_config.yml) which can be used for prometheus metric scrape configuration 