# Avi Metrics Script

The Avi Metrics script was built with the intent to pull metrics from one or more Avi controllers and send these values to a centralized metrics database(s).
The script supports a number of different endpoints; current support includes AppDynamics, Datadog, Graphite Splunk, Logstash, Elasticsearch and InfluxDB.


This repository includes that necessary files to deploy a centralized metrics script
- **Requirements**
    - **python 2.7**
    - **python-requests**


- **Files**
    - **avimetrics.py**:  This is the script that will pull the values from the Avi Controller API and forward to the metrics enpoints
    - **avi_controllers.json**:  This file contains the Avi Controller login information.  When new Avi controllers are deployed they need to be added and this file must be redeployed.
    - **metrics_endpoints.py**:  This file contains the methods for formatting the data and sending to the defined metrics endpoint(s)
    - **dockerfile**:  This file contains the commands to build a container with the metrics script    
    - **appdynamics_http.json**:  This file contains values required to send to a App Dynamics Standalone Machine Agent HTTP Listener
    - **datadog.json**:  This file contains the values required to send to the Datadog HTTP API
    - **graphite_host.json**:  This file contains the graphite host and tcp port information
    - **splunk_host.json**:  This file contains the values required to send to a Splunk HTTP Endpoint Collector API
    - **logstash.json**:  This file contains the values required to send to a Logstash input
    - **elasticsearch_host.json**:  This file contains the values required to send to the Elasticsearch document API
    - **influxdb.json**:  This file contains the values required to send to an InfluxDB HTTP API endpoint
    - **ns1.json**:  This file contains the values required to publish to a NS1 data feed







# Installation
The following files are required and must exist within the same directory for successful metric gathering.
- **avimetrics.py**
- **avi_controllers.json**
- **metrics_endpoints.py**
- **RELEVANT ENDPOINT .json file(s)**



# Usage
## avimetrics.py

Below are the available arguments that can be provided.  None of these are required.

See all available options
```sh
$ avimetrics.py -h
```


See current script version
```sh
$ avimetrics.py -v
```

Send Metrics to one or more metrics endpoints.  Valid values are:
 - appdynamics_http
 - graphite
 - datadog
 - splunk
 - logstash
 - elasticsearch
 - influxdb
 - ns1


```sh
$ avimetrics.py -m datadog -m graphite
```

Only print exceptions
```sh
$ avimetrics.py -m <endpoint> --brief
```


Print status of all metrics gathering functions - This is default
```sh
$ avimetrics.py -m <endpoint> --debug
```


Disable checking for and retrieving of realtime metrics if they are enabled within the controller, results in the default 5 minute averages
```sh
$ avimetrics.py -m <endpoint> --norealtime
```

## avi_controllers.json

To Add an Additional Controller to Monitor this file will need to modified.  Password can be plaintext or base64 encoded.

EXAMPLE:

```sh
{"controllers":[
    {
    "avi_controller":"169.254.0.1",
    "location":"dc1",
    "environment":"prod",
    "avi_user":"user",
    "_comment":"ACCEPTS PLAIN TEXT OR BASE64 ENCODED PASSWORD",
    "avi_pass":"dGVzdA=="
    },
    {
    "avi_controller":"169.254.0.2",
    "location":"nj",
    "environment":"dev",
    "avi_user":"user",
    "_comment":"ACCEPTS PLAIN TEXT OR BASE64 ENCODED PASSWORD",
    "avi_pass":"test"
    }
  ]
}
```



## appdynamics_http.json

Define the AppDynamics Standalone Machine Agent IP address and the port that the HTTP listener is listening on

EXAMPLE:

```sh
{"appdynamics":
    {
	    "server":"169.254.0.1",
	    "server_port":8293
    }
}
```



## datadog.json

Define the URL and API key used to send metrics into Datadog

EXAMPLE:

```sh
{"datadog":
    {
        "api_url" : "app.datadoghq.com/api/v1/series?api_key=",
        "api_key" : "abcdefghijgklmnopqrstuvwxyz12345"
    }
}

```



## graphite_host.json

Define the grahite server host name/ip and the tcp port carbon cache is listening on

EXAMPLE:

```sh
{"graphite":
    {
	    "server":"127.0.0.1",
	    "server_port":2003
    }
}
```



## splunk_host.json

Define the values for sending values to Splunk HTTP Endpoint Collector.

EXAMPLE:

```sh
{"splunk_server":{
    "server":"169.254.0.1",
    "_comment":"HEC_PROTOCOL OPTIONS ARE HTTP OR HTTPS",
    "hec_protocol":"https",
    "hec_port": 8088,
    "hec_token":"abcdefgh-ijkl-mnop-qrst-uvwxyz123456",
    "_comment":"INDEX TYPE EVENT OR METRIC",
    "index_type":"event",
    "index":"avimetrics"
    }

}
```


## logstash.json

Define the values for sending metrics to a Logstash endpoint.  The script will send values in a format that is expecting the configured logstash codec to be json_lines.

EXAMPLE:

```sh
{"logstash":
    {
        "_comment": "logstash codec => json_lines",
        "server": "169.254.0.1",
        "server_port": 517,
        "_comment": "tcp or udp",
        "protocol": "udp"
    }
}

```


## elasticsearch.json

Define the values for sending metrics to Elasticsearch via the document API.

EXAMPLE:

```sh
{"elasticsearch":
    {
        "server": "169.254.0.1",
        "server_port": 9200,
        "protocol" : "https",
        "index": "avimetrics",
        "_comment":"default time filter field name",
        "timestamp": "@timestamp",
        "_comment":"If using auth on elasticsearch set auth-enabled to true and modify the credential values",
        "auth-enabled": true,
        "username": "admin",
        "password": "password"
    }
}

```


## influxdb.json

Define the values for sending metrics to InfluxDB via HTTP API.  The script will send values using the InfluxDB's Line Protocol format.

EXAMPLE:

```sh
{"influxdb":
    {
        "server": "169.254.0.1",
        "server_port": 8086,
        "protocol": "https",
        "db": "avi"
    }
}
```


## ns1.json

Define the values for publishing metrics to a NS1 data feed.  The script will publish a subset of Virtual Server metrics to their corresponding NS1 meta keys, using the Virtual Server name as a label.  Further information on configuration options and examples can be found [here](./ns1.md).

EXAMPLE:

```sh
{"ns1":
    {
        "api_key": "qACMD09OJXBxT7XOuRs8",
        "datasource_id": "a53252f9e583c6708331a1daeb172e12"
    }
}
```


# Run as a container
To run this script as a container, modify the files as exampled above prior to building.

### Build the container
```sh
$ docker build -t avimetrics .
```
### Start the container
To start the container it is required to specify the metrics endpoint via the <strong>EN_METRIC_ENDPOINT</strong> environment variable.  To specify multiple endpoint seprate each with a colon, ":".  

Add the environment variable <strong>EN_NOREALTIME=True</strong> to disable retrieving realtime metrics if they are enabled within the controller, results in 5 min averages.

The example below specifies running the container with sending data to multiple endpoints.
```sh
$ docker run -d -e "EN_METRIC_ENDPOINT=graphite:datadog:appdynamics_http" --name avimetrics --restart always --log-opt max-size=1m avimetrics
```

# Metrics Being Collected


### Controller Cluster Metrics

- Cluster node roles
- Network pool Usage
- License Usage %
- Days until license(s) expire
- Current Avi Vantage version
- Cluster Node Performance Metrics
    - controller_stats.avg_cpu_usage
    - controller_stats.avg_disk_usage
    - controller_stats.avg_mem_usage



### Service Engine Metrics:

- Virtual Server count per Service Engine
- Service Engine count
- Service Engine / Controller missed heartbeats
- Service Engine connected state
- Service Engine healthscore
- Service Engine Virtual Service hosted used capacity
- Statistics for each Service Engine
    - se_if.avg_bandwidth
    - se_stats.avg_connection_mem_usage
    - se_stats.avg_connections
    - se_stats.avg_connections_dropped
    - se_stats.avg_cpu_usage
    - se_stats.avg_disk1_usage
    - se_stats.avg_mem_usage
    - se_stats.avg_dynamic_mem_usage
    - se_stats.avg_persistent_table_usage
    - se_stats.avg_rx_bandwidth
    - se_if.avg_rx_bytes
    - se_if.avg_rx_pkts
    - se_if.avg_rx_pkts_dropped_non_vs
    - se_if.avg_tx_pkts
    - se_if.avg_tx_bytes
    - se_stats.avg_ssl_session_cache_usage
    - se_if.avg_connection_table_usage
    - se_stats.max_se_bandwidth
    - se_stats.avg_eth0_bandwidth
    - se_stats.pct_syn_cache_usage
    - se_stats.avg_packet_buffer_usage
    - se_stats.avg_packet_buffer_header_usage
    - se_stats.avg_packet_buffer_large_usage
    - se_stats.avg_packet_buffer_small_usage





### Virtual Service Stats

- Virtual Service healthscore
- Virtual Service operational status (Up/Down)
- Pool member(s) operational status (Up/Down)
- Which Service Engine the Virtual Service is hosted on
- Statistics for each Virtual Service; total and broken down per Service Engine
    - l4_server.avg_errored_connections
    - l4_server.avg_rx_pkts
    - l4_server.avg_bandwidth
    - l4_server.avg_open_conns
    - l4_server.avg_new_established_conns
    - l4_server.avg_pool_complete_conns
    - l4_server.apdexc
    - l4_server.avg_total_rtt
    - l4_client.apdexc
    - l4_client.avg_bandwidth
    - l4_client.avg_application_dos_attacks
    - l4_client.avg_complete_conns
    - l4_client.avg_connections_dropped
    - l4_client.avg_new_established_conns
    - l4_client.avg_policy_drops
    - l4_client.avg_rx_pkts
    - l4_client.avg_tx_pkts
    - l4_client.avg_rx_bytes
    - l4_client.avg_tx_bytes
    - l4_client.max_open_conns
    - l4_client.avg_lossy_connections
    - l7_client.avg_complete_responses
    - l7_client.avg_client_data_transfer_time
    - l7_client.avg_client_txn_latency
    - l7_client.sum_application_response_time
    - l7_client.avg_resp_4xx_avi_errors
    - l7_client.avg_resp_5xx_avi_errors
    - l7_client.avg_resp_4xx
    - l7_client.avg_resp_5xx
    - l4_client.avg_total_rtt
    - l7_server.avg_resp_latency
    - l7_server.apdexr
    - l7_client.avg_page_load_time
    - l7_client.apdexr
    - l7_client.avg_ssl_handshakes_new
    - l7_client.avg_ssl_connections
    - l7_server.avg_application_response_time
    - l7_server.pct_response_errors
    - l7_server.avg_frustrated_responses
    - l7_server.avg_total_requests
    - l7_client.sum_get_reqs
    - l7_client.sum_post_reqs
    - l7_client.sum_other_reqs
    - l7_client.avg_frustrated_responses
    - l7_client.avg_waf_attacks
    - l7_client.pct_waf_attacks
    - l7_client.sum_total_responses
    - l7_client.avg_waf_rejected
    - l7_client.avg_waf_evaluated
    - l7_client.avg_waf_matched
    - l7_client.avg_waf_disabled
    - l7_client.pct_waf_disabled
    - l7_client.avg_http_headers_count
    - l7_client.avg_http_headers_bytes
    - l7_client.pct_get_reqs
    - l7_client.pct_post_reqs
    - l7_client.avg_http_params_count
    - l7_client.avg_uri_length
    - l7_client.avg_post_bytes
    - dns_client.avg_complete_queries
    - dns_client.avg_domain_lookup_failures
    - dns_client.avg_tcp_queries
    - dns_client.avg_udp_queries
    - dns_client.avg_udp_passthrough_resp_time
    - dns_client.avg_unsupported_queries
    - dns_client.pct_errored_queries
    - dns_client.avg_domain_lookup_failures
    - dns_client.avg_avi_errors
    - dns_server.avg_complete_queries
    - dns_server.avg_errored_queries
    - dns_server.avg_tcp_queries
    - dns_server.avg_udp_queries









### Virtual Service Pool Server Metrics

- Statistics for each invidual Pool Server
    - l4_server.avg_rx_pkts
    - l4_server.avg_tx_pkts
    - l4_server.avg_rx_bytes
    - l4_server.avg_tx_bytes
    - l4_server.avg_bandwidth
    - l7_server.avg_complete_responses
    - l4_server.avg_new_established_conns
    - l4_server.avg_pool_open_conns
    - l4_server.avg_pool_complete_conns
    - l4_server.avg_open_conns
    - l4_server.max_open_conns
