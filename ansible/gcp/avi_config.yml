avi_config:
  ipamdnsproviderprofile:
    - name: ew
      tenant_ref: "/api/tenant?name=admin"
      internal_profile:
        usable_network_refs:
          - "/api/network?name=ew"
      type: IPAMDNS_TYPE_INTERNAL
    - name: ns
      tenant_ref: "/api/tenant?name=admin"
      internal_profile:
        usable_network_refs:
          - "/api/network?name=ns"
      type: IPAMDNS_TYPE_INTERNAL
    - name: ns_d
      tenant_ref: "/api/tenant?name=admin"
      internal_profile:
        dns_service_domain:
          - domain_name: "{{ project_name }}.avi.local"
      type: IPAMDNS_TYPE_INTERNAL_DNS
  network:
    - name: "ew"
      tenant_ref: "/api/tenant?name=admin"
      configured_subnets:
        - prefix:
            mask: 24
            ip_addr:
              type: "V4"
              addr: "{{ ew_subnet }}"
          static_ranges:
            - begin:
                type: "V4"
                addr: "{{ ew_subnet_start }}"
              end:
                type: "V4"
                addr: "{{ ew_subnet_end }}"
    - name: "ns"
      tenant_ref: "/api/tenant?name=admin"
      configured_subnets:
        - prefix:
            mask: 24
            ip_addr:
              type: "V4"
              addr: "{{ ns_subnet }}"
          static_ranges:
            - begin:
                type: "V4"
                addr: "{{ ns_subnet_start }}"
              end:
                type: "V4"
                addr: "{{ ns_subnet_end }}"