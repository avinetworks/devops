# External-DNS Supervisor Service Configuration

## Overview

This folder contains a **deployment-specific configuration** for the External-DNS Supervisor Service running on VMware Cloud Foundation with Aria (VCF-A). The YAML file here represents customized settings for a particular supervisor deployment and is **not** the complete Supervisor Service package.

## What is External-DNS Supervisor Service?

External-DNS is a Kubernetes operator that automatically manages DNS records for services and ingresses in your VKS clusters. It integrates with external DNS providers (like PowerDNS, AWS Route53, Azure DNS, etc.) to synchronize Kubernetes resources with DNS records.

For VMware vSphere environments, External-DNS is available as a **Supervisor Service**, which provides automated lifecycle management including installation, upgrades, and configuration.

The documentation for installing Supervisor Services on a supervisor is [here](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vsphere-supervisor-services-and-standalone-components/latest/managing-supervisor-services-with-vsphere-iaas-control-plane/supervisor-service-life-cycle-management-and-consumption/install-a-supervisor-service-on-supervisors.html).

## Official Supervisor Service Package

The complete External-DNS Supervisor Service package is maintained in the official VMware Supervisor Services repository:

🔗 **[VMware Supervisor Services - External-DNS](https://github.com/vsphere-tmm/Supervisor-Services/tree/main/external-dns)**

### Download the Package

To download the official External-DNS Supervisor Service package:

1. Visit **[support.broadcom.com free software downloads section](https://support.broadcom.com/group/ecx/free-downloads)**
2. Look for **vSphere Supervisor Services** packages
3. Download the External-DNS Supervisor Service package

> **Note**: You need appropriate Broadcom support credentials to access the download portal.

## What's in This Folder?

This folder contains **deployment-specific configuration** for External-DNS:

- **`externaldns.yml`** - Kubernetes Deployment manifest with environment-specific settings for External-DNS

This is an **example configuration** showing how External-DNS was deployed in a specific environment. It includes:
- PowerDNS provider configuration
- Domain filtering settings
- Synchronization settings
- Custom parameters for a particular deployment

## How to Use

### Option 1: Deploy as Supervisor Service (Recommended)

1. **Install via vCenter UI:**
   - Navigate to Workload Management → Supervisor → Services
   - Add the External-DNS service from the service catalog
   - Configure using the provided `values.yaml` during installation

2. **Benefits:**
   - Automated lifecycle management
   - Integrated with vSphere platform
   - Simplified upgrades and patching
   - Platform-level monitoring and support

### Option 2: Use This Configuration as Reference

If you've already installed External-DNS as a Supervisor Service, you can use the YAML in this folder as a reference for:

1. **Customizing your deployment** - Adapt the configuration parameters to your environment
2. **Understanding the structure** - See how External-DNS is configured for PowerDNS integration
3. **Troubleshooting** - Compare your configuration with this working example

## Configuration Highlights

The `externaldns.yml` in this folder demonstrates:

```yaml
args:
  - --source=service        # Watch Kubernetes Services
  - --source=ingress        # Watch Kubernetes Ingresses
  - --provider=pdns         # PowerDNS provider
  - --pdns-server=...       # PowerDNS server URL (sanitized)
  - --pdns-api-key=...      # API key for authentication (sanitized)
  - --domain-filter=...     # Only manage specific domains
  - --log-level=debug       # Logging verbosity
  - --interval=30s          # Sync interval
```

> ⚠️ **SANITIZED VALUES**: The configuration in this folder has been sanitized and contains placeholder values. You must replace these with your actual environment settings.

## Prerequisites

Before deploying External-DNS:

- vSphere 8.0 or later with Workload Management enabled
- A supervisor cluster configured and running
- A DNS provider configured and accessible (PowerDNS, Route53, Azure DNS, etc.)
- API credentials for your DNS provider
- Network connectivity from supervisor to DNS provider

## Supported DNS Providers

External-DNS supports many DNS providers including:

- **PowerDNS** (shown in this example)
- AWS Route53
- Azure DNS
- Google Cloud DNS
- Cloudflare
- And many more...

For a complete list, see the [External-DNS documentation](https://github.com/kubernetes-sigs/external-dns#status-of-providers).

## Integration with Avi Load Balancer

This External-DNS configuration works seamlessly with the Avi Load Balancer blueprints in the parent directories:

1. Deploy a Virtual Service or Ingress using the Avi blueprints
2. External-DNS automatically detects the new service
3. DNS records are created in your DNS provider
4. Applications become accessible via DNS names

### Example Flow:

```
L7 Ingress Blueprint (L7_ssl.yml)
  ↓
Creates Kubernetes Ingress with hostname
  ↓
External-DNS detects Ingress
  ↓
Creates DNS A record → points to Avi Virtual Service IP
  ↓
Application accessible at hostname
```

## Customization

To customize for your environment, modify these key parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--pdns-server` | Your PowerDNS API endpoint | `http://pdns.yourdomain.com` |
| `--pdns-api-key` | Authentication key | Your API key |
| `--domain-filter` | Domains to manage | `example.com` |
| `--txt-owner-id` | Unique identifier | `my-cluster` |

## Troubleshooting

### Check External-DNS Logs

```bash
kubectl logs -n <namespace> deployment/external-dns
```

### Common Issues

1. **DNS records not created**: Check domain-filter matches your ingress hostnames
2. **Authentication errors**: Verify API key is correct
3. **Rate limiting**: Adjust --interval parameter
4. **Network connectivity**: Ensure supervisor can reach DNS provider

## Documentation Links

- 📖 [VMware Supervisor Services Official Repo](https://github.com/vsphere-tmm/Supervisor-Services)
- 📖 [External-DNS Kubernetes Project](https://github.com/kubernetes-sigs/external-dns)
- 📖 [VMware vSphere Documentation](https://docs.vmware.com/en/VMware-vSphere/)
- 📖 [VCF-A Documentation](https://docs.vmware.com/en/VMware-Cloud-Foundation/)

## Support

For issues with:
- **Supervisor Service installation**: Contact VMware Global Support Services (GSS)
- **Configuration questions**: Refer to the External-DNS documentation
- **DNS provider issues**: Contact your DNS provider support

## Related Blueprints

This External-DNS configuration is designed to work with:
- `../L7_nossl.yml` - Layer 7 load balancing without SSL
- `../L7_ssl.yml` - Layer 7 load balancing with SSL
- `../L7_ssl_vault_annotations.yml` - L7 with automated certificate management

All blueprints in the parent directory can automatically register DNS records when External-DNS is deployed.

---

**Note**: This is a deployment-specific example. Always download the official Supervisor Service package from support.broadcom.com and customize according to your environment's requirements.
