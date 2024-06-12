# Certificate management profile scripts


## vault_cert_management.py

This is a Certificate Management Profile script for Hashicorp Vault acting as a Certificate Authority (PKI Secrets Engine).

The Certificate Management Profile should be configured with the following parameters:

*vault_addr*:\
**REQUIRED**\
Base URL for the Vault API.

Example: https://vault_server.contoso.com:8200

*vault_path*:\
**REQUIRED**\
API path for the **sign** API endpoint for the specific PKI secrets engine and role.

Example: /v1/pki_int/sign/contoso-com-role

*vault_token*:\
**REQUIRED**\
An API token with sufficient access to call the signing API.

Note: It is strongly recommended to mark this parameter as "sensitive".

The following optional parameters may be specified:

*vault_namespace*:\
**OPTIONAL**\
The Vault namespace under which to make the signing API call. If not specified, the default namespace will be used.

*verify_endpoint*:\
**OPTIONAL**\
The CA certificate chain (in PEM format) that should be used to verify trust for the SSL connection to the Vault API endpoint. If this parameter is not provided, SSL verification for the API calls to Vault will be disabled.

*api_timeout*:\
**OPTIONAL**\
The timeout that should be applied to the call to the Vault API endpoint. A default timeout of **20 seconds** will be used if this parameter is not specified.

![Alt Certificate Management Profile Example](/docs/img/cert_mgmt_prof.png)


## LetsEncrypt certificate management profile scripts

# letsencrypt_mgmt_profile.py
A cert management profile script that will utilize an HTTP listener for the LE challenges

# letsencrypt_mgmt_profile_with_dns.py
A cert management profile script that will publish DNS records to Avi DNS for LE challenges

# letsencrypt_mgmt_profile_infoblox_dns.py
A cert management profile script that will publish DNS records to Infoblox for LE challenges

## Sectigo certificate management profile script
