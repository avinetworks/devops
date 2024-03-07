# NS1 Metric Configuration

## Options
* `api_key` - The NS1 API key to use for authorization when publishing updates.
* `datasource_id` - The ID of the NS1 Data Source to publish updates to.
* `endpoint` (optional) - The absolute URL of the NS1 API endpoint to publish updates to.  If not defined in configuration, defaults to `https://api.nsone.net`.
* `metric_map` (optional) - The mapping of Avi Virtual Server metrics to NS1 meta keys to publish updates to.  If not defined in configuration, by default `l4_server.avg_bandwidth`, `l4_client.avg_complete_conns` and `l7_server.avg_total_requests` will be mapped to the `loadavg`, `connections` and `requests` NS1 meta keys, respectively.

## Examples

## Minimal Configuration
```
{"ns1":
    {
        "api_key": "qACMD09OJXBxT7XOuRs8",
        "datasource_id": "a53252f9e583c6708331a1daeb172e12"
    }
}
```

### Custom Endpoint
```
{"ns1":
    {
        "endpoint": "https://privatedns.test.io"
        "api_key": "qACMD09OJXBxT7XOuRs8",
        "datasource_id": "a53252f9e583c6708331a1daeb172e12"
    }
}
```

### Custom Metric Mapping
```
{"ns1":
    {
        "api_key": "qACMD09OJXBxT7XOuRs8",
        "datasource_id": "a53252f9e583c6708331a1daeb172e12",
        "metric_map": {
            "l7_client.avg_page_load_time": "loadavg",
            "l7_server.avg_resp_latency": "priority"
        }
    }
}
```
