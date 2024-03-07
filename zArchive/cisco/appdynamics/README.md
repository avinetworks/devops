# Appdynamics Integration

This repository includes that necessary files to deploy the Appdynamics Avi Vantage monitoring extension.

- **Requirements**
    - **python 2.7**
    - **python-requests**

- **Files**
    - **avi_controllers.json**:  This file contains the Avi Controller login information.  Any Avi controller that is desired to be monitored must be added to this file.
    - **monitor.xml**:  The Avi Vantage monitor extension configuration file
    - **avi_metrics.py**:  This python script containing all the API calls for metric values to be collected.
    - **avi_metrics.sh**:  The shell script called by the Appdynamics Standalone Machine Agent to execute the monitoring script.




# Installation
- Create a subdirectory within *<machine_agent_home>*/monitors.  
- Copy all 4 files to this sub subdirectory
- Restart the Appdynamics machine agent


## avi_controllers.json

Add Controllers to be monitored this file, password can be plaintext or base64 encoded.


EXAMPLE:

```sh
{"controllers":[
    {
    "avi_controller":"169.254.0.1",
    "location":"dc1",
    "environment":"prod",
    "avi_user":"user",
    "_comment":"ACCEPTS PLAINTEXT OR BASE64 ENCODED PASSWORD",
    "avi_pass":"dGVzdA=="
    },
    {
    "avi_controller":"169.254.0.2",
    "location":"dc2",
    "environment":"dev",
    "avi_user":"user",
    "_comment":"ACCEPTS PLAINTEXT OR BASE64 ENCODED PASSWORD",
    "avi_pass":"test"
    }
  ]
}
```




# Troubleshooting
There are two primary logs to investigate for issues; the Avi python script log and the Appdynamics machine agent log.

- *<machine_agent_home>*/monitors/*subdirectory*/avi_metrics.log
- *<machine_agent_home>*/logs/ machine-agent.log



# Appdynamics Metric Limitations
Appdynamics limits the number of metrics an agent can send as well as the number of metrics a controller can store.  The Avi Vantage monitoring extension can send a large number of metrics, especially as the deployment starts to scale and the number of the controllers clusters grows.  

It is important to understand Appdynamics limitations for your environment as well as what metrics you find important to monitor from Avi Vantage.

https://docs.appdynamics.com/display/PRO43/Metrics+Limits

## How to Reduce the Number of Metrics
If you are exceeding Appdynamics limitations for metrics the script will need to be modified to limit the number being sent.

There are a few ways to limit the number of metrics being sent via the script.
- Stop a function from running
- Remove undesired Virtual Service, Pool Member or Service Engine Metrics from being collected

### Stop a function from running ###
There are a number of functions that run independently from one another to collect metrics.  Each function is added to a list to be run.  To disable a function from running, comment out the line where it's added to the list.

The list is titled **test_functions**.  Search for **test_functions.append** in the python script to find the location for where the functions are added for execution, comment out the line with the unwanted function/metrics.


### Remove undesired Virtual Service, Pool Member or Service Engine Metrics ###
By default there are numerous metrics being pulled for all Virtual Services, Service Engines and Pool Members.  
The metrics being collected for Virtual Services, Pool Members and Service Engines are all contained within lists.  To stop a metric from being sent simply comment out the line, making sure that what is left is still a correctly formatted list.

Search the python script for the specific lists containing the metrics:
- **vs_metric_list**
- **pool_server_metric_list**
- **se_metric_list**






# Metrics Being Collected


###Controller Cluster Metrics

- Cluster node roles
- Network pool Usage
- License Usage %
- Days until license(s) expire
- Current Avi Vantage version
- Cluster Node Performance Metrics
    - controller_stats.avg_cpu_usage
    - controller_stats.avg_disk_usage
    - controller_stats.avg_mem_usage




###Service Engine Metrics:

- Virtual Server count per Service Engine
- Service Engine count
- Service Engine / Controller missed heartbeats
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






###Virtual Service Stats

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





###Virtual Service Pool Server Metrics

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
