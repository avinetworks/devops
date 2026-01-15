# Aria Automation & VCF-A Load Balancer Automation Blueprints

This repository contains automation blueprints for deploying and managing NSX Advanced Load Balancer (ALB) resources using VMware Aria Automation and VMware Cloud Foundation - Automation (VCF-A).

## Overview

These blueprints demonstrate Infrastructure as Code (IaC) patterns for automated load balancer provisioning across different VMware platforms:

- **Aria Automation (aria_auto/)**: Blueprints for deploying ALB/Avi load balancers in vCenter and NSX-T environments (Aria Automation 8.18.1patch3)
- **VCF-A (vcf-a/)**: Blueprints for deploying load balancers in VMware Cloud Foundation - Automation using Kubernetes ingress patterns (All Apps orgs in VCF-A 9)

## Directory Structure

```
ariaauto-vcfa/
├── aria_auto/                    # Aria Automation blueprints
│   ├── fullstack_deployment.yaml         # Full stack: VMs + Load Balancer
│   ├── nsxt_with_servers.yaml            # NSX-T cloud with server pools
│   ├── nsxt_with_sg.yaml                 # NSX-T with security group integration
│   ├── ssl_and_dns.yaml                  # SSL termination + DNS automation
│   ├── ssl_dns_tenant.yaml               # Multi-tenant SSL/DNS deployment
│   ├── Create VS - NSX-T cloud.yml       # Virtual Service with NSX-T
│   ├── Create VS - vCenter Cloud - AppProfile dropdown _ 1.yml  # vCenter virtual service
│   ├── add a content switch rule for a new standalone pool/  # Content switching automation
│   │   ├── add_pool.yml                  # Pool creation blueprint
│   │   └── abx_action_patch_httppolicy.py  # ABX action for HTTP policy updates
│   └── event subscription for generating an SSL certificate/  # Certificate automation
│       └── abx_action_request_cert.py    # ABX action for certificate requests
│
└── vcf-a/                        # VCF-A blueprints
    └── vcf9 blueprints/
        ├── L4.yml                        # Layer 4 load balancing
        ├── L7_nossl.yml                  # Layer 7 without SSL
        ├── L7_ssl.yml                    # Layer 7 with SSL
        ├── L7_ssl_vault_annotations.yml  # L7 with cert-manager/Vault integration
        └── external-dns/
            └── externaldns.yml           # External DNS automation
```

## Aria Automation Blueprints

### Full Stack Deployments

#### `fullstack_deployment.yaml`
Complete infrastructure deployment including:
- Apache web server VMs (Ubuntu 18.04)
- Avi LB Virtual Service
- Pool configuration with health monitors
- Optional SSL termination
- WAF policy application
- Cloud-init configuration for automated web server setup

**Key Features:**
- Scalable deployment (small/medium/large)
- Automatic load balancer algorithm selection
- Dynamic server pool registration
- Integrated with vCenter cloud

#### `nsxt_with_servers.yaml` & `nsxt_with_sg.yaml`
NSX-T specific deployments:
- **nsxt_with_servers.yaml**: Static IP-based pool members
- **nsxt_with_sg.yaml**: Dynamic pool membership via NSX Security Groups
- VRF context support for multi-tenancy
- IPAM network integration
- Tier-1 gateway configuration

### SSL & DNS Automation

#### `ssl_and_dns.yaml`
Automated SSL certificate and DNS record creation:
- Dynamic SSL certificate configuration
- DNS A-record creation with TTL configuration
- Conditional SSL enablement
- Application profile selection (HTTP/HTTPS)

#### `ssl_dns_tenant.yaml`
Multi-tenant version with:
- Tenant-specific resource isolation
- Separate secure/insecure virtual service resources
- Pre-configured SSL certificate references

### Event-Driven Automation

#### Event Subscription: SSL Certificate Generation
Located in `event subscription for generating an SSL certificate/`
- **Purpose**: Automatically request SSL certificates when virtual services are deployed
- **Trigger**: Virtual service creation events
- **Actions**: 
  - API call to certificate management profile
  - RSA 2048-bit key generation
  - Automatic certificate binding to virtual service

#### Event Subscription: Content Switching
Located in `add a content switch rule for a new standalone pool/`
- **Purpose**: Add content switching rules to existing virtual services
- **Trigger**: New pool deployment
- **Actions**:
  - Create new pool with optional NSX Security Group integration
  - PATCH existing HTTP policy with new switching rule
  - Path-based routing configuration

### Custom Forms

The `.yml` files with `layout:` sections provide custom Aria Automation forms with:
- Dynamic field visibility based on user selections
- Integration with Avi Controller APIs for dropdown population
- Health monitor selection
- Custom health check configuration

## VCF-A Blueprints (Kubernetes-Native)

### Layer 4 Load Balancing (`L4.yml`)

Deploys a Layer 4 load balancer using VirtualMachineService:
- Two Ubuntu VMs with Apache web servers
- LoadBalancer type service for direct IP allocation
- Supervisor namespace integration
- Cloud-init bootstrap for automated configuration

### Layer 7 Load Balancing

#### `L7_nossl.yml`
HTTP-only ingress configuration:
- Kubernetes Ingress resource
- ClusterIP service backend
- Host-based routing
- No TLS termination

#### `L7_ssl.yml`
HTTPS ingress with pre-existing certificates:
- TLS section with secret reference
- Manual certificate management
- Secure HTTPS termination

#### `L7_ssl_vault_annotations.yml`
Automated certificate management with cert-manager:
- Integration with HashiCorp Vault PKI
- Cert-manager annotations for automatic certificate issuance
- Certificate rotation handled by cert-manager
- Vault issuer configuration

### External DNS Integration

Located in `external-dns/externaldns.yml`:
- Kubernetes External DNS deployment
- PowerDNS provider configuration
- Automatic DNS record creation for services/ingresses
- Domain filtering for specific zones

## Common Patterns

### Input Parameters

Most blueprints support:
- `target_port` / `port`: Backend server port
- `secure_port`: HTTPS port (typically 443)
- `app_prefix`: Naming prefix for resources
- `ssl_enable`: Toggle SSL termination
- `fqdn` / `fqdn_name`: DNS record configuration

### Resource Types

**Aria Automation:**
- `Idem.AVILB.APPLICATIONS.VS_VIP`: Virtual IP allocation
- `Idem.AVILB.APPLICATIONS.VIRTUAL_SERVICE`: Virtual service configuration
- `Idem.AVILB.APPLICATIONS.POOL`: Server pool management
- `Cloud.Machine`: VM provisioning

**VCF-A:**
- `CCI.Supervisor.Namespace`: Kubernetes namespace reference
- `CCI.Supervisor.Resource`: Generic Kubernetes resource wrapper
- Native Kubernetes resources (Ingress, Service, VirtualMachine, etc.)

## Security Features

### SSL/TLS Configuration
- System-Standard SSL profiles
- Custom certificate references
- Automated certificate generation via ABX actions
- Cert-manager integration for Kubernetes

### Health Monitoring
- System health monitors (HTTP, HTTPS)
- Custom health check paths and methods
- Configurable health check intervals

### Network Security
- NSX Security Group integration for dynamic pool membership
- VRF context isolation for multi-tenancy
- Tier-1 gateway routing

## Prerequisites

### For Aria Automation Blueprints:
- VMware Aria Automation with cloud zones configured
- NSX Advanced Load Balancer (Avi) controller
- NSX-T or vCenter cloud configured in Avi Controller
- IPAM/IPAM profiles configured
- Network segments configured
- (Optional) Certificate management profile for automated cert generation
- (Optional) DNS profile for automatic DNS registration

### For VCF-A Blueprints:
- VMware Cloud Foundation - Automation
- Supervisor cluster enabled
- Namespace with appropriate permissions
- VM images published to content library
- (Optional) cert-manager installed for automated certificate management
- (Optional) External DNS deployment for automatic DNS records
- (Optional) HashiCorp Vault for PKI integration

## Customization Required

**⚠️ IMPORTANT: Sensitive information has been replaced with placeholders. Update before deployment:**

### Aria Automation Files:
- **Controller URLs**: Replace `<CONTROLLER_FQDN>` with your Avi Controller FQDN
- **Credentials**: Replace `<USERNAME>` and `<PASSWORD>` with appropriate credentials
- **Network References**: Update network API paths to match your environment
- **Certificate References**: Update certificate UUID/name references
- **IPAM Subnets**: Configure appropriate IPAM network references
- **Tenant Names**: Update tenant names to match your configuration
- **Domain Names**: Replace `<DOMAIN>` with your DNS domain

### VCF-A Files:
- **Namespace Names**: Update to your supervisor namespace
- **Image Names**: Replace `vmi-*` with your VM image IDs
- **Storage Classes**: Update storage policy names
- **Hostnames/Domains**: Replace `<DOMAIN>` with your DNS domain
- **PowerDNS Configuration**: Update server URLs and API keys
- **Certificate Secrets**: Reference appropriate TLS secret names

## Usage Examples

### Deploy a Simple HTTP Virtual Service (Aria Automation)

1. Import `nsxt_with_servers.yaml` into Aria Automation
2. Configure inputs:
   - Port: 80
   - Servers: ["192.168.1.10", "192.168.1.11"]
   - SSL Enable: false
3. Deploy

### Deploy HTTPS Virtual Service with Auto-Cert (Aria Automation)

1. Import `ssl_and_dns.yaml`
2. Set up event subscription using `abx_action_request_cert.py`
3. Configure inputs:
   - SSL Enable: true
   - FQDN: true
   - FQDN Name: myapp
4. Deploy (certificate automatically generated)

### Deploy L7 Ingress with Vault Certificates (VCF-A)

1. Ensure cert-manager and Vault issuer are configured
2. Import `L7_ssl_vault_annotations.yml`
3. Configure inputs:
   - App Prefix: myapp
   - Target Port: 80
4. Deploy (certificate automatically issued by Vault)

## ABX Actions (Aria Automation Extensibility)

### Certificate Request Action
- **File**: `abx_action_request_cert.py`
- **Purpose**: Automatically request SSL certificates from Avi Controller
- **API Calls**: 
  - Login to controller
  - Create SSL key and certificate
  - Update virtual service with certificate reference

### HTTP Policy Patch Action
- **File**: `abx_action_patch_httppolicy.py`
- **Purpose**: Add content switching rules to existing HTTP policies
- **API Calls**:
  - Query virtual service
  - Query HTTP policy set
  - Query new pool
  - PATCH policy with new rule

## Integration Points

### Avi Controller API
All Aria Automation blueprints interact with Avi Controller via:
- REST API endpoints (`/api/virtualservice`, `/api/pool`, etc.)
- Reference-based resource linking
- Tenant-aware API calls

### NSX-T Integration
- Security group-based pool membership
- Tier-1 gateway routing
- VRF context for network isolation

### DNS Integration
- Infoblox IPAM (referenced in some blueprints)
- PowerDNS (VCF-A external-dns)
- Avi DNS service

### Certificate Management
- Certificate management profiles (Aria Automation)
- Cert-manager with Vault PKI backend (VCF-A)

## Best Practices

1. **Use Security Groups**: Prefer NSX Security Groups over static IPs for dynamic environments
2. **Enable Health Monitoring**: Always configure appropriate health monitors
3. **Use DNS Automation**: Leverage DNS integration for automatic record management
4. **Certificate Automation**: Use ABX actions or cert-manager for certificate lifecycle management
5. **Multi-Tenancy**: Utilize tenant references for resource isolation
6. **Naming Conventions**: Use consistent naming with deployment name variables
7. **Validation**: Test blueprints in development environment before production use

## Troubleshooting

### Aria Automation
- Check ABX action logs for API call failures
- Verify cloud zone configuration and credentials
- Ensure network references are valid
- Validate Avi Controller connectivity

### VCF-A
- Check supervisor namespace permissions
- Verify VM image availability
- Review pod logs for cert-manager issues
- Validate external-dns deployment logs

## Support & Documentation

- **NSX ALB Documentation**: [VMware Docs](https://docs.vmware.com/en/VMware-NSX-Advanced-Load-Balancer/)
- **Aria Automation**: [VMware Docs](https://docs.vmware.com/en/VMware-Aria-Automation/)
- **VCF-A**: [VMware Cloud Foundation Docs](https://docs.vmware.com/en/VMware-Cloud-Foundation/)

## Notes

- All blueprints have been sanitized and require configuration before use
- Comments in files indicate where sensitive information was replaced
- Test thoroughly in non-production environment before production deployment
- Keep credentials secure and use appropriate secret management solutions
