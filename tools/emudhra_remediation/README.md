# Avi eMudhra Certificate Exposure Scanner

The `avi_emudhra_cert_scan.py` script assesses Avi Load Balancer configurations to identify exposure to compromised eMudhra intermediate CA certificates. Additionally, it detects certificates chaining to eMudhra roots currently being phased out of trust stores by major browser and operating system vendors.

To ensure security, the scanner operates exclusively in a **read-only** mode via the Avi Controller REST API. It makes no configuration modifications and never attempts to retrieve private keys.

## Contents

1. [Overview & Detection Scope](#1-overview--detection-scope)
2. [Prerequisites](#2-prerequisites)
3. [Quick Start Guide](#3-quick-start-guide)
4. [Options](#4-options)
5. [Interpreting Scan Results](#5-interpreting-scan-results)
6. [Generated Output Files](#6-generated-output-files)
7. [Recommended Remediation Steps](#7-recommended-remediation-steps)
8. [Scope & Limitations](#8-scope--limitations)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Overview & Detection Scope

Eight eMudhra intermediate CAs (six TLS, two code signing) have compromised private keys. Anyone holding such a key can issue certificates that chain to that CA. Each intermediate also exists as a Sectigo cross-signed certificate with the same public key, which gives a second trust path.

The scan looks at these Avi objects:

1. **SSLKeyAndCertificate**
   Certificates matching the predefined list of affected entries (by public key or fingerprint), along with all certificates issued beneath them. The chain is constructed using saved CA references and extracted directly from the certificates (issuer name and key identifier) to prevent missing or outdated references from obscuring an affected chain.
2. **PKIProfile**
   Profiles whose CA list contains an affected certificate.
3. **VirtualService**
   Virtual services that present an affected certificate, or validate client certificates with an affected PKI profile.
4. **Pool**
   Pools that use an affected PKI profile or an affected client certificate.
5. **Portal and secure channel**
   The certificates configured in System Configuration for the controller portal (up to two) and for the secure channel.

### Trust-chain impact

Trust-chain impact is reported separately. Those certificates are **not** compromised: they chain to a root that vendors are removing from their trust stores, so clients that validate against those stores may stop trusting them and the certificates may need to be reissued.

This applies only to certificates presented to clients (SSLKeyAndCertificate, the virtual services that present them, and the portal certificate). PKI profiles, pools and the secure channel certificate use trust anchors that Avi controls and are not affected; a PKI profile that holds a removed root is listed as informational only.

---

## 2. Prerequisites

Before executing the script, ensure your environment meets the following requirements:

- Python 3.8 or later and the `cryptography` package (3.1 or later):

  ```bash
  python3 -m pip install cryptography
  ```

- A system capable of establishing an HTTPS connection to the controller (typically over TCP port 443). The script does not need to be executed directly on the controller and can run from any network-accessible host.
- An Avi account with **READ** permissions across all target tenants for the following objects: `SSLKeyAndCertificate`, `PKIProfile`, `ApplicationProfile`, `VirtualService`, `Pool`, `PoolGroup` and `SystemConfiguration`. No write permission is needed. If the account cannot read one of them, the scan stops with an error (exit code 2) instead of producing a partial result.
- The CA certificate that signed the controller's HTTPS certificate, if the machine does not already trust it (see `--ca-cert`).

---

## 3. Quick Start Guide

Set the password in the environment (or leave it unset and type it at the prompt):

```bash
export AVI_PASSWORD='...'
```

Scan the `admin` tenant, verifying the controller certificate with your own CA:

```bash
python3 avi_emudhra_cert_scan.py --controller 10.0.0.5 --username admin \
    --ca-cert /path/to/controller-ca.pem
```

Scan one other tenant:

```bash
python3 avi_emudhra_cert_scan.py --controller ctrl.example.com \
    --tenant finance
```

Scan **every** tenant (recommended for comprehensive assessment):

```bash
python3 avi_emudhra_cert_scan.py --controller ctrl.example.com \
    --all-tenants
```

Use the cluster virtual IP or any controller node address as `--controller`. A `host:port` form (for example `ctrl.example.com:8443`) is accepted; a path is not.

Read the password from standard input instead of an environment variable:

```bash
printf '%s\n' "$PASSWORD" | python3 avi_emudhra_cert_scan.py \
    --controller ctrl.example.com --password-stdin
```

If `AVI_PASSWORD` is set, it takes precedence over `--password-stdin`. The password is never accepted as a command-line argument, never logged and never written to a report.

To see the background and how to read the result without scanning:

```bash
python3 avi_emudhra_cert_scan.py --explain
```

---

## 4. Options

| Option | Description | Details |
|--------|-------------|---------|
| `--controller HOST` | Controller address or name (or the `AVI_CONTROLLER` environment variable). | Required unless `--from-json` or `--explain` is used. |
| `--username NAME` | API user. | Default `admin`, or `AVI_USERNAME`. |
| `--password-stdin` | Read the password from the first line of standard input. | - |
| `--tenant NAME` | Tenant to scan. | Default `admin`. |
| `--all-tenants` | Scan every tenant. | Cannot be combined with `--tenant`. |
| `--ca-cert FILE` | CA certificate (a file, or a directory of certificates) used to verify the controller's HTTPS certificate. | Default: the system trust store. |
| `--insecure` | Skip verification of the controller's HTTPS certificate. **NOT RECOMMENDED:** the password and session would be exposed to anyone able to impersonate the controller. | Cannot be combined with `--ca-cert`. |
| `--api-version V` | `X-Avi-Version` to send. | Default: read from the controller. |
| `--page-size N` | Objects fetched per API request. | Default 50. |
| `--timeout SECONDS` | Per-request timeout. | Default 60. |
| `--output table` | Counts plus the action table. | Default. |
| `--output summary` | Counts only. | - |
| `--output json` | Print the JSON report on standard output (messages go to standard error). | - |
| `--priority P1,P2` | Show only these priorities in the action table. | - |
| `--only-tenant NAME` | Show only the items that belong to, or are used by, one tenant. | Useful after `--all-tenants`. |
| `--all` | Show every row of the action table. | Default: the first 20. |
| `--detail NAME` | List every object that depends on the certificate or PKI profile whose name or UUID contains `NAME`, then exit. | - |
| `--csv FILE` | Write one row per fix and affected object. | - |
| `--json-out FILE` | JSON report path. | Default `avi_emudhra_cert_exposure_report.json` in the current directory. |
| `--no-json` | Do not write the JSON report. | - |
| `--log-file FILE` | Error log path. | Default `avi_emudhra_cert_scan.log`. Created only if an error occurs. |
| `--from-json FILE` | Show a report saved by an earlier run instead of scanning. | Works offline and accepts the same display options. |
| `--explain` | Print the background and how to read the result, then exit. Does not scan. | - |

---

## 5. Interpreting Scan Results

The console output has two parts:

1. **COMPROMISED CERTIFICATE EXPOSURE**
   A table with the number of objects scanned and affected in each category (SSLKeyAndCertificate, PKIProfile, VirtualService, Pool, Portal-Cert, Secure-Channel-Cert), followed by a conclusion: `AFFECTED` or `NOT AFFECTED`. This is the part that needs action.
2. **POTENTIAL TRUST-CHAIN COMPATIBILITY IMPACT (not compromised)**
   The same kind of table for certificates that chain to a root being removed from vendor trust stores, followed by `REVIEW` or `NO IMPACT`.

Below the counts, an action table lists one row per certificate or PKI profile to fix, with its priority, the finding, the objects that depend on it, and the next action.

### Priorities

| Priority | Level | Description |
|----------|-------|-------------|
| P1 | Act now | The certificate or PKI profile is in use by a virtual service, pool, portal or secure channel. For trust-chain items, P1 means reissue to avoid client validation failures; it is not a compromise. |
| P2 | Review | Related to the incident but not itself compromised (for example, the issuer of a compromised CA). No direct action. |
| P3 | Not in use | Confirm that nothing depends on it, then delete it. If something does depend on it, treat it as P1. |

### Roles

The `roles` field in the JSON report says why an object was flagged:

| Role | Description |
|------|-------------|
| `COMPROMISED` | Matches one of the eight compromised intermediates, or its Sectigo cross-signed copy (same key). |
| `CHILD_OF_COMPROMISED` | Issued by a compromised intermediate, so anyone with the leaked key can forge certificates that chain to the same CA. |
| `ISSUER_OF_COMPROMISED` | Signed a compromised intermediate. The issuer itself is not compromised and its other children are not reported. |
| `ROOT_REMOVED_FROM_TRUST_STORES` | A root that vendors are removing from their trust stores. Not compromised. |
| `CHAINS_TO_REMOVED_ROOT` | Chains to a root being removed. Not compromised; clients may stop trusting it. |

### Exit code

| Exit Code | Description |
|-----------|-------------|
| 0 | Nothing found. |
| 1 | Affected (compromised) objects were found. |
| 2 | Error: the scan could not complete, or a report could not be read or written. |

Trust-chain findings alone do not change the exit code.

> [!WARNING]
> If the output contains `WARNING: scan is incomplete`, some certificates could not be read. The affected objects are named in the log file; treat the result as incomplete until they are resolved.

---

## 6. Generated Output Files

All files are created in the current directory unless you give a path. They contain the names, UUIDs and tenants of your certificates, PKI profiles, virtual services and pools, and the SHA-256 fingerprints of your certificates. Handle them like any other configuration export and restrict access appropriately. They never contain private keys or passwords.

| Output File | Description |
|-------------|-------------|
| `avi_emudhra_cert_exposure_report.json` | The full report. It starts with a `legend` that explains the roles and priorities, then `summary`, then `action_items`, then the detailed `affected` and `trust_chain_impact` sections. |
| CSV file (`--csv`) | One row per fix and affected object, with the same priority, finding, next action and verification columns as `action_items`. |
| `avi_emudhra_cert_scan.log` | Errors only (unreadable certificates, scan or report failures). Created only if an error occurs. |

Each entry in `action_items` looks like this:

```json
{
  "priority": "P1",
  "section": "compromised",
  "fix_type": "Certificate",
  "name": "cert1",
  "uuid": "c1",
  "tenant": "admin",
  "finding": "Compromised eMudhra intermediate",
  "next_action": "Replace with a certificate from an unaffected key and CA",
  "verify": "Check the certificate presented in the TLS handshake and confirm clients connect. Rerun the script",
  "affected_objects": [
    {"type": "VS", "name": "vs1", "uuid": "v1", "tenant": "admin"}
  ]
}
```

To review a saved report later, or to share it with someone who has no access to the controller:

```bash
python3 avi_emudhra_cert_scan.py \
    --from-json avi_emudhra_cert_exposure_report.json --priority P1 --all
```

---

## 7. Recommended Remediation Steps

| Step | Item | Action |
|------|------|--------|
| 1 | Start with P1 rows | Use `--detail NAME` to list every virtual service, pool and portal setting that depends on an item. |
| 2 | Take action on certificates | Replace the certificate with one issued from an unaffected key and CA, update the objects that use it, and confirm clients connect. |
| 3 | Take action on PKI profiles | Remove the affected CA entry and keep your other trust anchors. For a Sectigo cross-signed entry, keep the AAA Certificate Services root if other chains need it; if you cannot remove the cross-signed entry now, enable CRL checking. A profile that no longer has dependents can be deleted. |
| 4 | P2 items | Need no direct action; review them after the P1 items. |
| 5 | P3 items | Confirm nothing depends on them, then delete them. |
| 6 | Trust-chain items | Reissue the certificate from a CA hierarchy that remains in the vendor trust stores, then confirm that the affected clients can connect. |
| 7 | Verification | Rerun the script and confirm the items are gone. The exit code is 0 when no compromised object remains. |

> [!NOTE]
> AAA Certificate Services is not compromised. It is a possible path to the cross-signed copies, and keeping it is not a finding by itself. Do not remove it only because it is listed; other chains may need it.

---

## 8. Scope & Limitations

- **Tenants.** A scan without `--all-tenants` covers one tenant. Objects in other tenants, and references to them, are not seen. Use `--all-tenants` for a complete scan.
- **Point in time.** The scan reads the configuration as it is while the script runs. If objects are created or deleted during the scan, rerun it. Run it when the configuration is quiet if you need a consistent result.
- **Avi configuration only.** The scan covers the objects listed above. It does not inspect certificates on backend servers, clients or other systems, and it does not connect to virtual services to see which certificate they actually present.
- **Client certificate validation** is checked through HTTP and TCP/L4 application profiles.
- **Read-only.** Nothing is changed. Replacing certificates and editing PKI profiles is done by you in Avi.
- **Built-in list.** The built-in list of affected certificates is fixed at the time the script was written. The report records its version as `manifest_version`.

---

## 9. Troubleshooting

| Error / Issue | Description / Cause | Resolution / Action |
|---------------|---------------------|---------------------|
| `the TLS certificate of ... could not be verified` | The machine does not trust the controller's HTTPS certificate. | Pass the CA that signed it with `--ca-cert FILE`. Avoid `--insecure`. |
| `cannot reach ...` | Wrong address or port, or HTTPS to the controller is blocked. | Test with: `curl -vk https://HOST/` |
| `login to ... failed: wrong user name or password, or the account cannot use the API` | Invalid credentials or missing API permissions. | Check the user name and password, and ensure the account is allowed to use the API. |
| `... returned HTTP 403` | The account cannot read one of the objects in the requested tenant. | Use an account with read access across target objects. |
| `the controller redirected ... redirects are not followed` | Address leads to a redirect (e.g., load balancer or secondary host name). | Use the controller's own address directly. |
| `no password: set AVI_PASSWORD or use --password-stdin` | Script is running non-interactively without a password supplied. | Set `AVI_PASSWORD` or pass via `--password-stdin`. |
| `Missing dependency 'cryptography'` | Required Python package is missing. | Run: `python3 -m pip install cryptography` |
| `scan failed: ... (see avi_emudhra_cert_scan.log)` | An unhandled error occurred during execution. | Check `avi_emudhra_cert_scan.log` for full details. |
| `WARNING: scan is incomplete` | Some certificates could not be read. | Review the log file to identify and resolve unreadable objects. |
| The scan is slow | Large configurations require multiple API requests. | Increase `--page-size` value (default is 50). |
| Persistent issues | Unresolved operational or scan errors. | Contact Broadcom Support with console output and log file (sanitizing sensitive names first). |
