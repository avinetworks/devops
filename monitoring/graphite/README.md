# Graphite Integration

This repository includes that necessary scripts to monitor Avi metrics and forward to Graphite.  

- **Requirements**
    - **python 2.7**
    - **python-requests**

- **Files**
    - **avi_controllers.json**:  This file contains the Avi Controller login information.  When new Avi controllers are deployed they need to be added and this file must be redeployed.
    - **graphite_host.json**:  This file contains the graphite host and tcp port information.
    - **avi_metrics-script-graphite.py**:  This script contains all the metrics values to be collected and forwards to graphite.




# Installation
All 3 files are required and must exist within the same directory for successful metric gathering.


# Usage
## avi-metrics-script-graphite.py

Below are the available arguments that can be provided.  None of these are required.

See all available options
```sh
$ avi-metric-script-graphite.py -h
```


See current script version
```sh
$ avi-metric-script-graphite.py -v
```


Pull metrics from only the first controller in the list
```sh
$ avi-metric-script-graphite.py -t
```


Only print exceptions
```sh
$ avi-metric-script-graphite.py --brief
```


Print status of all metrics gathering functions - This is default
```sh
$ avi-metric-script-graphite.py --debug
```


Print namespace of what is being sent to Graphite.  Used for troubleshooting is metrics are missing
```sh
$ avi-metric-script-graphite.py -n
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
    "_comment":"ACCEPTS PLAINTEXT OR BASE64 ENCODED PASSWORD",
    "avi_pass":"dGVzdA=="
    },
    {
    "avi_controller":"169.254.0.2",
    "location":"nj",
    "environment":"dev",
    "avi_user":"user",
    "_comment":"ACCEPTS PLAINTEXT OR BASE64 ENCODED PASSWORD",
    "avi_pass":"test"
    }
  ]
}
```


## graphite_host.json

Define the graphite server host name/ip and the tcp port carbon cache is listening on

EXAMPLE:

```sh
{"graphite":
    {
	    "server":"127.0.0.1",
	    "server_port":2003
    }
}
```




# Metrics Being Collected
```sh

###Controller Cluster Metrics

- Cluster status
- Vcenter cloud connector status
- ACI APIC connectivity status
- Network pool Usage
- Expiring certs
- How many cores on each ESX is being used for Service Engines
- Days until license(s) expire
- Current Avi Vantage version




###Service Engine Metrics:

- Virtual Server count per Service Engine
- Service Engine count
- Statistics for each Service Engine
    - se_stats.avg_bandwidth
    - se_if.avg_bandwidth
    - se_stats.avg_connection_mem_usage
    - se_stats.avg_connection_policy_drops
    - se_stats.avg_connections
    - se_stats.avg_connections_dropped
    - se_stats.avg_cpu_usage
    - se_stats.avg_disk1_usage
    - se_stats.avg_mem_usage
    - se_stats.avg_persistent_table_size
    - se_stats.avg_persistent_table_usage
    - se_stats.avg_rx_bandwidth
    - se_if.avg_rx_bytes
    - se_stats.avg_rx_pkts
    - se_if.avg_rx_pkts
    - se_stats.avg_rx_pkts_dropped
    - se_if.avg_rx_pkts_dropped_non_vs
    - se_stats.avg_tx_pkts
    - se_if.avg_tx_pkts
    - se_if.avg_tx_bytes
    - se_stats.avg_ssl_session_cache_usage
    - se_stats.max_connection_mem_total
    - se_stats.max_connection_table_size
    - se_if.avg_connection_table_usage
    - se_stats.avg_ssl_session_cache
    - se_stats.max_num_vs
    - se_stats.max_se_bandwidth
    - se_stats.sum_connection_dropped_memory_limit
    - se_stats.sum_connection_dropped_packet_buffer_stressed
    - se_stats.sum_connection_dropped_persistence_table_limit
    - se_stats.sum_packet_buffer_allocation_failure
    - se_stats.sum_packet_dropped_packet_buffer_stressed
    - se_stats.sum_cache_object_allocation_failure
    - se_stats.avg_eth0_rx_pkts
    - se_stats.avg_eth0_tx_pkts
    - se_stats.avg_eth0_bandwidth
    - se_stats.pct_syn_cache_usage
    - se_stats.avg_packet_buffer_usage
    - se_stats.avg_packet_buffer_header_usage
    - se_stats.avg_packet_buffer_large_usage
    - se_stats.avg_packet_buffer_small_usage
- How many Service Engines hosted on an ESX host
- Service Engine Virtual Service hosted used capacity
- How many Service Engines have debug enabled
- Service Engine individual Dispatcher CPU usage




###Virtual Service Stats

- Statistics for each Virtual Service
    - l4_server.avg_errored_connections
    - l4_server.avg_rx_pkts
    - l4_server.avg_bandwidth
    - l4_server.avg_server_count
    - l4_server.avg_open_conns
    - l4_server.avg_new_established_conns
    - l4_server.avg_pool_complete_conns
    - l4_server.sum_num_state_changes
    - l4_server.sum_rx_zero_window_size_events
    - l4_server.sum_tx_zero_window_size_events
    - l4_server.sum_out_of_orders
    - l4_server.sum_sack_retransmits
    - l4_server.sum_timeout_retransmits
    - l4_server.apdexc
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
    - l4_server.avg_total_rtt
    - l4_client.avg_total_rtt
    - l4_client.avg_rx_pkts_dropped
    - l4_client.sum_packet_dropped_user_bandwidth_limit
    - l4_client.max_open_conns
    - l7_client.avg_complete_responses
    - l7_client.avg_resp_4xx_avi_errors
    - l7_client.avg_resp_5xx_avi_errors
    - l7_client.avg_resp_4xx
    - l7_client.avg_resp_5xx
    - l7_client.avg_clien_data_transfer_time
    - l7_server.avg_resp_4xx
    - l7_server.avg_resp_5xx
    - l7_server.avg_resp_latency
    - l7_server.apdexr
    - l7_client.avg_page_load_time
    - l7_client.apdexr
    - l7_client.avg_ssl_handshakes_new
    - l7_client.avg_ssl_connections
    - l7_server.avg_application_response_time
    - l7_server.pct_response_errors
    - l7_server.avg_frustrated_responses
    - l7_client.avg_frustrated_responses
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
- Virtual Service healthscore
- Operational status (Up/Down)
- Significant Log count
- Pool member up/down status
- Which Service Engine the Virtual Service is hosted on
- How many Virtual Services hosted on an ESX host
- How many Virtual Services have full client logs enabled
- How many Virtual Services have debug enabled




###Virtual Service Pool Server Metrics

- Statistics for each Pool Server
    - l4_server.max_rx_pkts_absolute
    - l4_server.avg_rx_pkts
    - l4_server.max_tx_pkts_absolute
    - l4_server.avg_tx_pkts
    - l4_server.max_rx_bytes_absolute
    - l4_server.max_tx_bytes_absolute
    - l4_server.avg_bandwidth
    - l7_server.avg_complete_responses
    - l4_server.avg_new_established_conns
    - l4_server.avg_pool_open_conns
    - l4_server.avg_pool_complete_conns
    - l4_server.avg_open_conns
    - l4_server.max_open_conns
