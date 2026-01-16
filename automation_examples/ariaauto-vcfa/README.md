# Aria Automation & VCF-A Load Balancer Automation Blueprints

This repository contains automation blueprints for deploying and managing VMware Avi Load Balancer (ALB) resources using VMware Aria Automation and VMware Cloud Foundation - Automation (VCF-A).

## Overview

These blueprints demonstrate Infrastructure as Code (IaC) patterns for automated load balancer provisioning across different VMware platforms using VMware Avi Load Balancer:

- **Aria Automation (aria_auto/)**: Blueprints for deploying Avi load balancers in vCenter and NSX-T environments (Aria Automation 8.18.1patch3)
- **VCF-A (vcf-a/)**: Blueprints for deploying load balancers in VMware Cloud Foundation - Automation using Kubernetes ingress patterns (All Apps orgs in VCF-A 9)

> **Note**: VMware Avi Load Balancer was formerly known as NSX Advanced Load Balancer (NSX-ALB) or Avi Vantage. You may see references to "NSX-ALB in API endpoints, resource types, and legacy documentation.

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
- Apache web server VMs (Ubuntu 18.04) - provisioned and configured via cloud-init in the blueprint
- Avi Virtual Service
- Pool configuration with health monitors
- Optional SSL termination
- WAF policy application
- Automated web server setup

**What does cloud-init do?**
The cloud-init configuration in this blueprint:
- Provisions Ubuntu VMs through Aria Automation
- Installs Apache web server and PHP packages
- Creates user accounts with passwords
- Configures SSH access
- Sets hostname
- Customizes the default web page

This handles the **backend server** setup. The AviController (which must be pre-configured as a prerequisite) handles the **load balancer** configuration.

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

### Event-Driven Automation (ABX Actions)

**What is ABX?**
ABX (Action Based eXtensibility) is VMware Aria Automation's serverless function platform that allows you to run Python, Node.js, or PowerShell scripts in response to events. Think of it as "serverless functions for automation" - you write code that executes automatically when specific events occur (like deploying a virtual service).

#### Event Subscription: SSL Certificate Generation
Located in `event subscription for generating an SSL certificate/`
- **Purpose**: Automatically request SSL certificates when virtual services are deployed
- **Trigger**: Virtual service creation events (Aria Automation deployment events)
- **Technology**: Python ABX action that calls Avi Controller REST API
- **Actions**: 
  - Authenticates to Avi Controller
  - Creates SSL certificate request via API (`/api/sslkeyandcertificate`)
    - Prompts the controller to generate an RSA 2048-bit key
    - Submits the certificate signing request to the external CA
    - CA will respond with a signed certificate
    - Controller will add this to the Avi certificate store
  - Binds certificate to virtual service automatically

#### Event Subscription: Content Switching
Located in `add a content switch rule for a new standalone pool/`
- **Purpose**: Add content switching rules to existing virtual services
- **Trigger**: New pool deployment events
- **Technology**: Python ABX action that patches HTTP policies
- **Actions**:
  - Queries virtual service and existing HTTP policy
  - Creates new pool with optional NSX Security Group integration
  - PATCH existing HTTP policy with new switching rule
  - Configures path-based routing dynamically

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

## Virtual Service Features

### SSL/TLS Configuration
- System-Standard SSL profiles
- Custom certificate references
- Automated certificate generation via ABX actions
- Cert-manager integration for Kubernetes

### Health Monitoring
- System health monitors (HTTP, HTTPS)
- Custom health check paths and methods
- Configurable health check intervals

### NSX Cloud-specific parameters
- NSX Security Group integration for dynamic pool membership
- VRF context isolation for multi-tenancy
- Tier-1 gateway routing

## Prerequisites

### For Aria Automation Blueprints:
- VMware Aria Automation (version 8.18.1patch3 or later) with cloud zones configured
- VMware Avi Load Balancer Controller deployed and licensed
- **NSX-T or vCenter cloud configured in Avi Controller** (see "How to Configure Clouds" below)
- IPAM/DNS profiles configured in Avi Controller
- Network segments/port groups available and accessible
- (Optional) Certificate management profile for automated cert generation
- (Optional) DNS profile for automatic DNS registration
- (Optional) ABX service enabled for event-driven automation

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
- **Controller URLs**: Replace `<CONTROLLER_FQDN>` with your Avi Controller FQDN (e.g., `avi.example.com`)
- **Credentials**: Replace `<USERNAME>` and `<PASSWORD>` with appropriate credentials
- **Network References**: Update network API paths to match your environment (see "How to Find Network References" below)
- **Certificate References**: Update certificate UUID/name references
- **IPAM Subnets**: Configure appropriate IPAM network references
- **Tenant Names**: Update tenant names to match your configuration (default is typically `admin`)
- **Domain Names**: Replace `<DOMAIN>` with your DNS domain

### How to Find Network References

Network references in Avi follow this format: `/api/network?name=<network-name>` or `/api/network/<network-uuid>`

**Method 1: Avi Controller UI**
1. Log into your Avi Controller web interface
2. Navigate to **Infrastructure > Networks**
3. Find your desired network (e.g., VIP network, server network)
4. Note the network name
5. Use format: `/api/network?name=<network-name>`

**Method 2: Avi Controller API**
```bash
# Get all networks
curl -k -X GET https://<CONTROLLER_FQDN>/api/network \
  -H "X-Avi-Tenant: admin" \
  -u admin:<password>

# Response includes network details with URLs like:
# "url": "https://controller/api/network/network-xxxxx-xxxx-xxxx"
# "name": "VMNetwork-PortGroup"
```

**Method 3: Check Existing Virtual Services**
1. Go to **Applications > Virtual Services**
2. Edit an existing virtual service
3. Look at the VIP network configuration
4. Copy the network reference format

**Example Network References:**
- vCenter: `/api/network?name=VM-Network` (port group name)
- NSX-T: `/api/network?name=vxw-dvs-34-virtualwire-256-sid-2230254-wdc-02-vc23-avi-mgmt-2` (segment name)
- By UUID: `/api/network/network-f8e5b5e5-4c3e-4b1a-9c8e-5d6f7e8f9a0b` (Avi network object UUID)

### How to Configure Clouds in Avi Controller

Before using these blueprints, you must configure clouds in Avi Controller:

**For vCenter Cloud:**
1. Navigate to **Infrastructure > Clouds**
2. Click **Create > VMware vCenter/vSphere ESX**
3. Provide vCenter credentials and connection details
4. Configure management network and data networks
5. Set up IPAM/DNS profiles

**For NSX-T Cloud:**
1. Navigate to **Infrastructure > Clouds**
2. Click **Create > NSX-T**
3. Provide NSX-T Manager credentials
4. Select Transport Zone and Tier-1 gateway
5. Configure overlay segment settings
6. Set up IPAM/DNS profiles

**Documentation:**
- [Avi vCenter Cloud Configuration](https://techdocs.broadcom.com/us/en/vmware-security-load-balancing/avi-load-balancer/avi-load-balancer/30-2/vmware-avi-load-balancer-installation-guide/installing-nsx-alb-in-vmware-vsphere-environments.html)
- [Avi NSX-T Cloud Configuration](https://techdocs.broadcom.com/us/en/vmware-security-load-balancing/avi-load-balancer/avi-load-balancer/30-2/vmware-avi-load-balancer-installation-guide/installing-nsx-alb-in-vmware-nsx-t-environments.html)

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
- REST API endpoints (`/api/virtualservice`, `/api/pool`, `/api/vsvip`, etc.)
- Reference-based resource linking (using URLs or query parameters)
- Tenant-aware API calls (X-Avi-Tenant header)
- Session-based authentication with CSRF tokens

**API Authentication Flow (ABX Actions):**
1. POST to `/login` with username/password
2. Receive session cookie and API version
3. Include `X-Avi-Tenant`, `X-Avi-Version`, `X-CSRFToken` headers in subsequent calls
4. Make API calls to create/modify resources

### NSX-T Integration
- Security group-based pool membership
- Tier-1 gateway routing
- VRF context for network isolation

### DNS Integration
- Infoblox IPAM (referenced in some blueprints)
- PowerDNS (vSphere Supervisor external-dns)
- Avi DNS service (built-in virtual service for DNS)
- External DNS providers via IPAM profiles

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
- Check ABX action logs in Aria Automation (**Extensibility > Actions > Action Runs**)
- Verify cloud zone configuration and credentials
- Ensure network references are valid (query `/api/network` endpoint)
- Validate Avi Controller connectivity (check firewall rules, DNS resolution)
- Review deployment logs in Aria Automation
- Test API authentication manually using curl/Postman
- Verify account references match cloud zone configuration

### VCF-A
- Check supervisor namespace permissions
- Verify VM image availability
- Review pod logs for cert-manager issues
- Validate external-dns deployment logs

## Support & Documentation

- **Avi Documentation**: [Broadcom TechDocs - VMware Avi Load Balancer](https://techdocs.broadcom.com/us/en/vmware-security-load-balancing/avi-load-balancer.html)
- **Aria Automation**: [Broadcom TechDocs - Aria Automation](https://techdocs.broadcom.com/us/en/vmware-cis/aria/aria-automation/8-18/getting-started-with-aria-auto-on-prem-8-18.html)
- **VCF-A**: [Broadcom TechDocs - VMware Cloud Foundation](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-cloud-applications.html)
- **Avi API Reference**: Available at `https://<your-controller>/api/` (interactive Swagger documentation)
- **Aria Automation ABX**: [ABX Actions Documentation](https://techdocs.broadcom.com/us/en/vmware-cis/aria/aria-automation/8-18/assembler-on-prem-using-and-managing-master-map-8-18/maphead-designing-your-deployments/maphead-extensibility-in-cloud-assembly.html)

## Glossary

- **Avi**: VMware Avi Load Balancer (formerly NSX Advanced Load Balancer / Avi Vantage)
- **ABX**: Action Based eXtensibility - serverless functions in Aria Automation
- **VIP**: Virtual IP address assigned to a virtual service
- **Pool**: Group of backend servers that handle traffic
- **Virtual Service**: Load balancer configuration combining VIP, pool, and policies
- **Cloud**: Avi integration with infrastructure (vCenter, NSX-T, etc.)
- **Service Engine**: Data plane component that processes traffic
- **IPAM**: IP Address Management profile for automatic IP allocation
- **VRF**: Virtual Routing and Forwarding context for network isolation
- **Tier-1 Gateway**: NSX-T logical router for north-south traffic

## Notes

- All blueprints have been sanitized and require configuration before use
- Comments in files indicate where sensitive information was replaced
- Test thoroughly in non-production environment before production deployment
- Keep credentials secure and use appropriate secret management solutions
