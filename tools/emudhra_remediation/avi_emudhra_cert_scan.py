#!/usr/bin/env python3
############################################################################
# ========================================================================
# Copyright (c) 2026 Broadcom Inc. and/or its subsidiaries. All Rights Reserved. Broadcom Confidential.
# ========================================================================
###
"""
Avi eMudhra compromised-intermediate certificate exposure scanner.

Connects to the Avi Controller REST API over HTTPS (session login, controller
certificate verified) and reads SSLKeyAndCertificate, PKIProfile, VirtualService
and Pool objects one page at a time, then reports every affected object per
category. It only reads.

  1. SSLKeyAndCertificate: certificates matching the embedded eMudhra manifest
     and their children. The chain is taken
     from the ca_certs references and also derived from the certificates (issuer
     name and key identifier), so a stale or missing reference does not hide a
     compromised chain. A certificate whose Authority Key Identifier names a
     compromised intermediate is also reported when that CA is not stored in Avi.
     A stored issuer of a compromised intermediate (an emSign root in the
     manifest) is reported too, with the role ISSUER_OF_COMPROMISED. Its other
     children are not reported: the issuer itself is not compromised.
  2. PKIProfile: profiles whose ca_certs contain a certificate from the manifest
     or from step 1.
  3. VirtualService: services using a certificate from step 1, or whose application
     profile (also a per-service override) validates client certificates with a
     PKI profile from step 2 (HTTP and TCP/L4 application profiles).
  4. Pool: pools using a PKI profile from step 2 or a client certificate from step 1.
  5. Portal-Cert / Secure-Channel-Cert: the certificates configured in
     SystemConfiguration for the portal (up to 2) and the secure channel, checked
     against step 1. The JSON report lists each one with its status.

Trust-chain impact is reported separately under "trust_chain_impact". It covers
certificates that chain to a root being removed from vendor trust stores (the
roots are not compromised). Clients that validate against those stores may stop
trusting such certificates, so they may need reissuing. It applies only to
certificates presented to clients: SSLKeyAndCertificate, the VirtualServices
presenting them and the portal certificate. PKIProfiles, Pools and the secure
channel certificate use trust anchors Avi controls, so they are not affected. A
PKIProfile holding a removed root is listed as informational only.

Usage:
  export AVI_PASSWORD=...        (or type it at the prompt)
  python3 avi_emudhra_cert_scan.py --controller 10.0.0.5 --username admin \\
      --ca-cert /path/to/controller-ca.pem
  python3 avi_emudhra_cert_scan.py --controller ctrl.example.com --tenant finance
  python3 avi_emudhra_cert_scan.py --controller ctrl.example.com --all-tenants
  python3 avi_emudhra_cert_scan.py --controller ... --json-out /tmp/report.json

Connection:
  --controller HOST    controller address or name (or AVI_CONTROLLER)
  --username NAME      API user (default admin, or AVI_USERNAME)
  password             AVI_PASSWORD, --password-stdin, or a prompt; never an argument
  --tenant NAME        tenant to scan (default admin); --all-tenants scans every tenant
  --ca-cert FILE       CA that signed the controller certificate, to verify the
                       server (default: the system trust store). A directory works too.
  --insecure           skip the server certificate check (not recommended)
  --api-version V      X-Avi-Version (default: read from the controller)
  --page-size N        objects per request (default 50);  --timeout SECONDS

The console shows the counts and an action table: one row per certificate or
PKI profile to fix, with the priority, the next action and how many virtual
services, pools and portal settings depend on it.
  --priority P1,P2     show only these priorities
  --only-tenant NAME   show only the items of one tenant (all-tenant scans)
  --all                show every row (default: the first 20)
  --detail NAME        list every object that depends on the matching item
  --csv FILE           write one row per fix and affected object
  --output summary     counts only;  --output json  prints the JSON report
  --from-json FILE     render a saved JSON report without scanning
  --explain            print the background and how to read the result; no scan
Priorities: P1 replace or remove now, P2 review, P3 not in use (confirm, then
retire). Trust-chain items are not compromised; they are shown separately.

The JSON report is self-describing: "legend" explains the roles and priorities,
and "action_items" lists each item to fix with its next action, how to verify
it and the objects that depend on it.

Errors (unreadable certificates, scan or report failures) are written to the
log file; nothing else is logged. The file is created only if an error occurs.
The password is never logged or written to the report.

Exit code: 0 = nothing found, 1 = affected (compromised) objects found, 2 = error.
Trust-chain findings alone do not change the exit code.
"""

import argparse
import base64
import csv
import getpass
import hashlib
import http.cookiejar
import json
import logging
import os
import shutil
import ssl
import sys
import textwrap
import types
import urllib.error
import urllib.parse
import urllib.request
import warnings
from collections import defaultdict
from datetime import datetime, timezone

warnings.filterwarnings("ignore")

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization
except ImportError:
    sys.stderr.write(
        "ERROR: Missing dependency 'cryptography'. Install it with:\n"
        "  python3 -m pip install cryptography\n"
    )
    sys.exit(2)

MANIFEST_VERSION = "2026-10-27.1"

# An eMudhra intermediate and its Sectigo cross-certificate share the same SPKI.
EMUDHRA_COMPROMISED_CERTS = [
    # eMudhra-issued TLS intermediates
    {
        "name": "EM EV TLS CA - G3B (eMudhra BV)",
        "ccadb_id": "A012304",
        "variant": "Original intermediate",
        "usage": "TLS / EV",
        "cert_sha256": "E7568FE6E12331F4FD7DE61DA4C7559D0F8EB192A218D4741A3BA75184333838",
        "spki_sha256": "E0254C7FCDC265E2F0F8A428DABB75AB4AE039B4872D62F5EE57F0877D5A8A41",
        "serial": "c7c41efe92d825f05eae841a4a82c1",
    },
    {
        "name": "EM OV TLS CA - G3B (eMudhra BV)",
        "ccadb_id": "A012308",
        "variant": "Original intermediate",
        "usage": "TLS / OV",
        "cert_sha256": "98B896625C0C230ADEEC3EB2CF6AAD5001ECF9156A68644E82374CE5833BC25B",
        "spki_sha256": "43BFFA19D6EF651451F6841E019931E96F6F2EAEFF28AB4B6F1CE4576DE2717B",
        "serial": "6cada367fb1c100088120ea202d568",
    },
    {
        "name": "EM DV TLS CA - G3B (eMudhra BV)",
        "ccadb_id": "A012302",
        "variant": "Original intermediate",
        "usage": "TLS / DV",
        "cert_sha256": "42C4ACCD12C4F59597925E1A08A7A90102608543809308D50EC427E118BA1493",
        "spki_sha256": "EBED6475C2C2D80FCB199F3FE8DD6E6B3CE60B77EB15D4E42C3DEC0C6F5B5105",
        "serial": "a4aee678f23362b4c0e460b772f214",
    },
    {
        "name": "EM EV TLS CA - G3C (eMudhra Inc)",
        "ccadb_id": "A012296",
        "variant": "Original intermediate",
        "usage": "TLS / EV",
        "cert_sha256": "432EC25F0D28DE9006D97BF752F17BBB2CD41F669933FCB072D9A1148D0261F3",
        "spki_sha256": "5C0660A2B164910D8FF589C18E14552E9E0EC237DCEFE2CB736D41A4811F81A0",
        "serial": "8009928a64107601af05fa2f19f109",
    },
    {
        "name": "EM OV TLS CA - G3C (eMudhra Inc)",
        "ccadb_id": "A012300",
        "variant": "Original intermediate",
        "usage": "TLS / OV",
        "cert_sha256": "CB6E15165AC802E9B3F993F16C25D41F4E81C21EBDE71AE1B012AC00BF9C7C3F",
        "spki_sha256": "63ECEFEE431D49523BC1136C4E72D0206A477086CAF606CD5CF025686C109CF8",
        "serial": "296926c227a3a1526392b19482a504",
    },
    {
        "name": "EM DV TLS CA - G3C (eMudhra Inc)",
        "ccadb_id": "A012294",
        "variant": "Original intermediate",
        "usage": "TLS / DV",
        "cert_sha256": "0164D7CEAE5BB909C272AF151FF44B1177AE9B47D9424B94F1D9558C30934D19",
        "spki_sha256": "49DD353DC2B919A3770645117D0E60C16115E7D1BC259EEFE734B00EA434FE5F",
        "serial": "588b2e3c2bb8cda13e1a1209254321",
    },

    # eMudhra-issued TLS direct issuer (signed by emSign ECC Root CA - G3)
    {
        "name": "emSign Root TLS CA - G3 (eMudhra Technologies Limited)",
        "ccadb_id": "A011858",
        "variant": "eMudhra-issued; signed by emSign ECC Root CA - G3",
        "usage": "Issuer of compromised TLS intermediates",
        "kind": "direct_issuer",
        "flag_children": False,
        "cert_sha256": "3094025792039A68AF6E553686410BDAB7C0D4A36B9084CBA64202E35D6EBBDD",
        "spki_sha256": "C619E4780ED8E0ABEDA24AD732567DE4383A7EA941338F6D1A7D1B49AC792FE9",
        "serial": "961A3EFB1359576ED04005B4684A5B",
    },

    # eMudhra-issued code-signing intermediates
    {
        "name": "EM OV CS CA - G3B (eMudhra BV)",
        "ccadb_id": "A012306",
        "variant": "Original intermediate",
        "usage": "Code signing",
        "cert_sha256": "9E39DE2881273ACC225A149C72BA3E0F51424963669AB633EE1DC7DF5DB067B4",
        "spki_sha256": "EC4FFA1AD0AC88081314B7AAFFEF6A91F97CD57291BB5BA686C5415F5EB4F6B6",
        "serial": "7818933f8f85b4619a2b35fba83d0a",
    },
    {
        "name": "EM OV CS CA - G3C (eMudhra Inc)",
        "ccadb_id": "A012298",
        "variant": "Original intermediate",
        "usage": "Code signing",
        "cert_sha256": "4B2460A466F95FD40113BCDCCA2CEB29B3B093921DE45474DA7DF48874C630B1",
        "spki_sha256": "92C063D67E8F14DB71D288E11266FFDAF69CBF115F7BAB14F3BC2F68D25E0E30",
        "serial": "544b7f922c31ae220a4a922916f6e6",
    },


    # Sectigo / AAA Certificate Services cross-signed TLS intermediates
    {
        "name": "EM EV TLS CA - G3B (Sectigo cross-certificate)",
        "ccadb_id": "A012333",
        "variant": "Sectigo cross-certificate",
        "usage": "TLS / EV",
        "cert_sha256": "579480AEA166290BD3C643589E795FC0D0E54E86505D180F1DFF99EFD3199512",
        "spki_sha256": "E0254C7FCDC265E2F0F8A428DABB75AB4AE039B4872D62F5EE57F0877D5A8A41",
        "serial": "d8f8685e4f2bd9d82402a85a1c1eb731",
    },
    {
        "name": "EM OV TLS CA - G3B (Sectigo cross-certificate)",
        "ccadb_id": "A012354",
        "variant": "Sectigo cross-certificate",
        "usage": "TLS / OV",
        "cert_sha256": "5F1DED4DD590AF74631290CF073B122A2AAC6A1FA479778A0BD43579BD832699",
        "spki_sha256": "43BFFA19D6EF651451F6841E019931E96F6F2EAEFF28AB4B6F1CE4576DE2717B",
        "serial": "e94223bde92f914e5ab9acabfdac3710",
    },
    {
        "name": "EM DV TLS CA - G3B (Sectigo cross-certificate)",
        "ccadb_id": "A012347",
        "variant": "Sectigo cross-certificate",
        "usage": "TLS / DV",
        "cert_sha256": "45A883F349AEDFD5F3A649B5498FFB121712BA8B448F3F2A91DBC5A766FCDDBE",
        "spki_sha256": "EBED6475C2C2D80FCB199F3FE8DD6E6B3CE60B77EB15D4E42C3DEC0C6F5B5105",
        "serial": "a024fdf4ba665c785ce4a020483858b7",
    },
    {
        "name": "EM EV TLS CA - G3C (Sectigo cross-certificate)",
        "ccadb_id": "A012334",
        "variant": "Sectigo cross-certificate",
        "usage": "TLS / EV",
        "cert_sha256": "FD9D5C2DBBD4995AB69B8D50C439D9527B00529199C2FD01B2174EB58F07021F",
        "spki_sha256": "5C0660A2B164910D8FF589C18E14552E9E0EC237DCEFE2CB736D41A4811F81A0",
        "serial": "05f078752dece7a1bb8595d303167171",
    },
    {
        "name": "EM OV TLS CA - G3C (Sectigo cross-certificate)",
        "ccadb_id": "A012343",
        "variant": "Sectigo cross-certificate",
        "usage": "TLS / OV",
        "cert_sha256": "7485B51C0ED192878FA1D2F948FB529AE1842CC5086C4B67F7BE5B2039DE9489",
        "spki_sha256": "63ECEFEE431D49523BC1136C4E72D0206A477086CAF606CD5CF025686C109CF8",
        "serial": "8d5a4811939ef447d77111cdd9849ae9",
    },
    {
        "name": "EM DV TLS CA - G3C (Sectigo cross-certificate)",
        "ccadb_id": "A012342",
        "variant": "Sectigo cross-certificate",
        "usage": "TLS / DV",
        "cert_sha256": "62B7F9868263F72F6911FC78CEAF72C1979158B7368BF648683BB2AA39B02E72",
        "spki_sha256": "49DD353DC2B919A3770645117D0E60C16115E7D1BC259EEFE734B00EA434FE5F",
        "serial": "91f347f1a5b7d39962b95e0ee4e299d1",
    },


    # Sectigo / AAA Certificate Services cross-signed code-signing intermediates
    {
        "name": "EM OV CS CA - G3B (Sectigo cross-certificate)",
        "ccadb_id": "A012352",
        "variant": "Sectigo cross-certificate",
        "usage": "Code signing",
        "cert_sha256": "A496E23AC0CAB8155FC9B117B97EAE368EFCBB9041AEC8804D5A308D2D01C2D8",
        "spki_sha256": "EC4FFA1AD0AC88081314B7AAFFEF6A91F97CD57291BB5BA686C5415F5EB4F6B6",
        "serial": "41e32b73ac185d6ce0d7480bacf84e69",
    },
    {
        "name": "EM OV CS CA - G3C (Sectigo cross-certificate)",
        "ccadb_id": "A012350",
        "variant": "Sectigo cross-certificate",
        "usage": "Code signing",
        "cert_sha256": "84112972B8E59D14560AE7E7119654474AAD119990CF3722BFC1E3B91615E1FD",
        "spki_sha256": "92C063D67E8F14DB71D288E11266FFDAF69CBF115F7BAB14F3BC2F68D25E0E30",
        "serial": "d6a5ef613b390f32ef9cdf349f772841",
    },

    {
        "name": "emSign ECC Root CA - G3 (eMudhra Technologies Limited)",
        "ccadb_id": None,
        "variant": "Root CA",
        "usage": "Root / trust-chain impact",
        "kind": "trust_chain_removal",
        "flag_children": True,
        "trust_store_actions": [
            {"vendor": "Mozilla (NSS 3.131.1)", "effective": "2026-10-20"},
            {"vendor": "Chrome Root Store", "effective": "2026-10-27"},
        ],
        "cert_sha256": "86A1ECBA089C4A8D3BBE2734C612BA341D813E043CF9E8A862CD5C57A36BBE6B",
        "spki_sha256": "8D417DB2DD8BF5E3084D1E3F196D583849D81BDD4C00C70B9D39369E96B8C782",
        "serial": "3cf607a968700eda8b84",
    },
    {
        "name": "AAA Certificate Services (Comodo CA Limited)",
        "ccadb_id": None,
        "variant": "Root CA",
        "usage": "Root / trust-chain impact",
        "kind": "trust_chain_removal",
        "flag_children": False,
        "cert_sha256": "D7A7A0FB5D7E2731D771E9484EBCDEF71D5F0C3E0A2948782BC83EE0EA699EF4",
        "spki_sha256": "BD153ED7B0434F6886B17BCE8BBE84ED340C7132D702A8F4FA318F756ECBD6F3",
        "serial": "01",
    },
    {
        "name": "emSign Root TLS CA - G3 (eMudhra Technologies Limited)",
        "ccadb_id": None,
        "variant": "Direct issuer CA",
        "usage": "Issuer of compromised TLS intermediates",
        "kind": "direct_issuer",
        "flag_children": False,
        "cert_sha256": "7DD78D5F4F13459A83DFF9ABBBA62EDBAF6F2D102BF257FD712F4D9F2746ED8D",
        "spki_sha256": "C619E4780ED8E0ABEDA24AD732567DE4383A7EA941338F6D1A7D1B49AC792FE9",
        "serial": "0e760672f143459fc8fe0ab0bc05e394",
    },
    {
        "name": "emSign Root CS CA - G3 (eMudhra Technologies Limited)",
        "ccadb_id": None,
        "variant": "Direct issuer CA",
        "usage": "Issuer of compromised code-signing intermediates",
        "kind": "direct_issuer",
        "flag_children": False,
        "cert_sha256": "F2EDAAFF3D9B701FB4D14C9F285F8C0BAD90FC3BCC1FA07D47F4718EDABA34A5",
        "spki_sha256": "0A6C2B2CA5B364207954171987AC9D2178561569D8205457E77CA90C32EDE282",
        "serial": "018fcec927c116f59c997edc0ccd2e2b",
    },
]

KIND_COMPROMISED = "compromised"
KIND_ROOT = "trust_chain_removal"
KIND_ISSUER = "direct_issuer"

# Authority Key Identifier in a child equals the Subject Key Identifier of its
# issuer. These identifiers let the scan find children when the CA object itself
# is not stored on Avi. The compromised intermediates are listed, and the roots
# being removed from vendor trust stores (KIND_ROOT), which are not compromised
# and are reported separately as trust-chain impact.
SIGNER_SKI = {
    # Trust-chain compatibility findings, not compromised-key findings.
    # emSign ECC Root CA - G3 has been removed from several platform trust stores.
    # Certificates chaining through this root may fail validation on affected clients.
    # Flag these roots separately to help customers assess potential reissuance needs.
    "e13aab217cf1e34d54aed472b7fd8b5942209054": ("emSign Root TLS CA - G3", KIND_ROOT),
    "7c5d028413d4cc8a9b81ce171c2e291e9c486342": ("emSign ECC Root CA - G3", KIND_ROOT),
    "e21e2fe71c19390e554b62c120245735248a2514": ("EM DV TLS CA - G3B", KIND_COMPROMISED),
    "ae7e105c3c2996c1a847270559f1e03dd4e50af3": ("EM DV TLS CA - G3C", KIND_COMPROMISED),
    "3edc20d9894698877b873fd88147b25c15d84706": ("EM EV TLS CA - G3B", KIND_COMPROMISED),
    "a6255e80a94db7f3967c1bc791df92bcee4beb5f": ("EM EV TLS CA - G3C", KIND_COMPROMISED),
    "9bd86551afe7e72c37ad08ee6919d9bf3784ae0a": ("EM OV TLS CA - G3B", KIND_COMPROMISED),
    "34eaea0cebc90adaf9d0c5e2ed9b78c9879e1b6c": ("EM OV TLS CA - G3C", KIND_COMPROMISED),
    "79fae8eccfdb0d758da458d69fb6eddc7c49dee6": ("EM OV CS CA - G3B", KIND_COMPROMISED),
    "ee6f73298d6fbfa7b31bc39534f61556447866b7": ("EM OV CS CA - G3C", KIND_COMPROMISED),
}

BY_CERT_SHA = {entry["cert_sha256"].lower(): entry for entry in EMUDHRA_COMPROMISED_CERTS}
BY_SPKI_SHA = {}
for entry in EMUDHRA_COMPROMISED_CERTS:
    if entry["spki_sha256"]:
        BY_SPKI_SHA.setdefault(entry["spki_sha256"].lower(), []).append(entry)

DEFAULT_TENANT = "admin"
ALL_TENANTS = "*"
API_PAGE_SIZE = 50
API_TIMEOUT = 60
DEFAULT_REPORT = "avi_emudhra_cert_exposure_report.json"
DEFAULT_LOG = "avi_emudhra_cert_scan.log"
PEM_BEGIN = b"-----BEGIN CERTIFICATE-----"
PEM_END = b"-----END CERTIFICATE-----"

MATCH_CERT = "KNOWN_COMPROMISED_CERTIFICATE"
MATCH_KEY = "KNOWN_COMPROMISED_PUBLIC_KEY"
MATCH_AVI_CERT = "MATCHES_AFFECTED_AVI_CERTIFICATE"
MATCH_SIGNER = "SIGNED_BY_AFFECTED_KEY"

STATUS_AFFECTED = "AFFECTED"
STATUS_OK = "NOT_AFFECTED"
STATUS_UNKNOWN = "NOT_SCANNED"

ROLE_COMPROMISED = "COMPROMISED"
ROLE_CHILD = "CHILD_OF_COMPROMISED"
ROLE_ROOT = "ROOT_REMOVED_FROM_TRUST_STORES"
ROLE_UNDER_ROOT = "CHAINS_TO_REMOVED_ROOT"
ROLE_ISSUER = "ISSUER_OF_COMPROMISED"
ROLE_ORDER = [ROLE_COMPROMISED, ROLE_CHILD, ROLE_ROOT, ROLE_UNDER_ROOT, ROLE_ISSUER]

TRUST_CHAIN_IMPACT = "trust_store_removal"
TRUST_CHAIN_NOTE = (
    "These certificates are not compromised. They chain to a root that vendors are "
    "removing from their trust stores, so clients that validate against those stores "
    "may stop trusting them.")
TRUST_CHAIN_REMEDIATION = (
    "Reissue the certificate from a CA hierarchy that remains in the vendor trust stores.")


def in_family(kind, trust_chain):
    """True if a manifest kind belongs to the family being reported: the roots being
    removed from trust stores (trust_chain) or the compromised keys and their issuers."""
    return (kind == KIND_ROOT) == trust_chain

MODEL_CATEGORIES = ["SSLKeyAndCertificate", "PKIProfile", "VirtualService", "Pool"]
SYSTEM_CATEGORIES = {
    "Portal-Cert": "portal_certificates",
    "Secure-Channel-Cert": "secure_channel_certificate",
}
CATEGORIES = MODEL_CATEGORIES + list(SYSTEM_CATEGORIES)

SCANNED = {}

# Only errors are logged. Without setup_logging() the records are dropped.
log = logging.getLogger("avi_emudhra_cert_scan")
log.addHandler(logging.NullHandler())


def setup_logging(path):
    """Log ERROR records to path. The file is created on the first error only."""
    handler = logging.FileHandler(path, delay=True, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.ERROR)


# Object access

def iter_batches(model, batch_size=API_PAGE_SIZE):
    """Yield lists of at most batch_size objects, one REST API page at a time."""
    for batch in model.iter_pages(batch_size):
        SCANNED[model.__name__] = SCANNED.get(model.__name__, 0) + len(batch)
        yield batch


def object_data(obj):
    """Return the object's data as a dict, without private key material.
    References appear as *_uuid / *_uuids."""
    data = dict(obj.protobuf() or {})
    for sensitive in ("key", "key_passphrase"):
        data.pop(sensitive, None)
    return data


def tenant_name(obj):
    try:
        tenant = obj.tenant_ref
    except Exception:
        return None
    return getattr(tenant, "name", None) if tenant else None


# Avi REST API access
#
# The scan reads objects through "models" that provide iter_pages() (and first() for
# the singleton SystemConfiguration), implemented over the REST API by the classes below.

# model name -> (REST path, fields to request or None for everything). Certificates
# are fetched without their private key.
API_MODELS = {
    "SSLKeyAndCertificate": ("sslkeyandcertificate", "name,uuid,tenant_ref,certificate,ca_certs"),
    "PKIProfile": ("pkiprofile", None),
    "ApplicationProfile": ("applicationprofile", None),
    "VirtualService": ("virtualservice", None),
    "Pool": ("pool", None),
    "PoolGroup": ("poolgroup", None),
    "SystemConfiguration": ("systemconfiguration", None),
}
PRIVATE_KEY_FIELDS = ("key", "key_passphrase")
MAX_PAGES = 100000


class ApiError(Exception):
    """A failure talking to the controller. The message never contains credentials."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect: the session cookie and credentials stay on one host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ApiError("the controller redirected {} to {}; redirects are not followed"
                       .format(req.full_url.split("?")[0], newurl.split("?")[0]))


def normalize_controller(value):
    """Return host[:port] from a host, host:port or https://host[:port] argument."""
    text = (value or "").strip()
    if "://" in text:
        parsed = urllib.parse.urlsplit(text)
        if parsed.scheme != "https":
            raise ValueError("the controller must be reached over https")
        if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            raise ValueError("give the controller as a host name or address, without a path")
        text = parsed.netloc
    if not text or "/" in text or "@" in text or " " in text:
        raise ValueError("invalid controller '{}'".format(value))
    return text


def ref_uuid(ref):
    """The uuid at the end of a REST reference (URL, optionally followed by #name)."""
    return ref.split("#", 1)[0].split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]


def ref_name(ref):
    return ref.split("#", 1)[1] if isinstance(ref, str) and "#" in ref else None


def normalize_refs(value):
    """Turn REST references (x_ref, x_refs) into the x_uuid, x_uuids form the scan reads."""
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if key.endswith("_refs") and isinstance(item, list):
                out[key[:-5] + "_uuids"] = [ref_uuid(i) for i in item if isinstance(i, str)]
            elif key.endswith("_ref") and isinstance(item, str):
                out[key[:-4] + "_uuid"] = ref_uuid(item)
            else:
                out[key] = normalize_refs(item)
        return out
    if isinstance(value, list):
        return [normalize_refs(i) for i in value]
    return value


class AviApi:
    """Minimal Avi Controller REST client: session login over verified HTTPS."""

    def __init__(self, controller, username, password, tenant=DEFAULT_TENANT, ca_cert=None,
                 insecure=False, api_version=None, timeout=API_TIMEOUT):
        self.host = normalize_controller(controller)
        self.base = "https://" + self.host
        self.username, self.password = username, password
        self.tenant, self.api_version, self.timeout = tenant, api_version, timeout
        self.tls = "disabled" if insecure else ("ca-cert" if ca_cert else "system-trust-store")
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=self._tls_context(ca_cert, insecure)),
            urllib.request.HTTPCookieProcessor(self.jar), NoRedirect)

    @staticmethod
    def _tls_context(ca_cert, insecure):
        if insecure:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context
        if ca_cert and not os.path.exists(ca_cert):
            raise ApiError("CA certificate '{}' does not exist".format(ca_cert))
        try:
            if ca_cert and os.path.isdir(ca_cert):
                return ssl.create_default_context(capath=ca_cert)
            return ssl.create_default_context(cafile=ca_cert)
        except (ssl.SSLError, OSError) as exc:
            raise ApiError("cannot load CA certificate '{}': {}".format(ca_cert, exc))

    def _csrf_token(self):
        return next((c.value for c in self.jar if c.name == "csrftoken"), None)

    def request(self, method, path, params=None, body=None, tenant=None, retry=True):
        url = self.base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        headers = {"Accept": "application/json", "Referer": self.base}
        tenant = self.tenant if tenant is None else tenant
        if tenant:
            headers["X-Avi-Tenant"] = tenant
        if self.api_version:
            headers["X-Avi-Version"] = self.api_version
        if self._csrf_token():
            headers["X-CSRFToken"] = self._csrf_token()
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 401 and retry and path != "/login":
                self.login()
                return self.request(method, path, params, body, tenant, retry=False)
            detail = exc.read(300).decode("utf-8", "replace").strip()
            raise ApiError("{} {} returned HTTP {}{}".format(
                method, path, exc.code, ": " + detail if detail else ""))
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, getattr(ssl, "SSLCertVerificationError", ssl.SSLError)):
                raise ApiError(
                    "the TLS certificate of {} could not be verified ({}). Pass the CA that "
                    "signed it with --ca-cert FILE. --insecure skips the check; avoid it."
                    .format(self.host, exc.reason))
            raise ApiError("cannot reach {}: {}".format(self.host, exc.reason))
        except (OSError, ValueError) as exc:
            raise ApiError("request to {} failed: {}".format(self.host, exc))
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            raise ApiError("{} {} did not return JSON".format(method, path))

    def connect(self):
        """Pick the API version (unless given) and log in."""
        if not self.api_version:
            try:
                info = self.request("GET", "/api/initial-data", tenant="", retry=False)
                self.api_version = (info.get("version") or {}).get("Version") or None
            except ApiError as exc:
                if "could not be verified" in str(exc) or "cannot reach" in str(exc):
                    raise
        self.login()

    def login(self):
        try:
            self.request("POST", "/login", body={"username": self.username,
                                                 "password": self.password}, tenant="", retry=False)
        except ApiError as exc:
            if "HTTP 401" in str(exc) or "HTTP 403" in str(exc):
                raise ApiError("login to {} failed: wrong user name or password, or the "
                               "account cannot use the API".format(self.host))
            raise
        if not self._csrf_token():
            raise ApiError("login to {} did not return a session".format(self.host))

    def close(self):
        try:
            self.request("POST", "/logout", body={}, tenant="", retry=False)
        except Exception:
            pass

    def iter_pages(self, path, page_size, fields=None, tenant=None):
        """Yield the objects of a collection one page at a time. Stops when a page
        brings nothing new, so a controller that ignores 'page' cannot loop forever."""
        seen = set()
        for page in range(1, MAX_PAGES):
            params = {"page": page, "page_size": page_size, "include_name": "true"}
            if fields:
                params["fields"] = fields
            response = self.request("GET", "/api/" + path, params, tenant=tenant)
            results = response.get("results") or []
            fresh = [r for r in results if r.get("uuid") not in seen]
            if results and not fresh:
                log.error("%s: page %d repeated earlier objects; stopping", path, page)
            if not fresh:
                return
            seen.update(r.get("uuid") for r in fresh)
            yield fresh
            if not response.get("next"):
                return


class ApiObject:
    """A REST object: uuid, name, tenant and its data with references normalised."""

    def __init__(self, raw, tenant=None, drop=()):
        raw = {k: v for k, v in raw.items() if k not in drop}
        self.uuid, self.name = raw.get("uuid"), raw.get("name")
        tenant = ref_name(raw.get("tenant_ref")) or tenant
        self.tenant_ref = types.SimpleNamespace(name=tenant) if tenant else None
        self._data = normalize_refs(raw)

    def protobuf(self):
        return self._data


class ApiModel:
    def __init__(self, api, name, path, fields):
        self.__name__ = name
        self.api, self.path, self.fields = api, path, fields
        self.drop = PRIVATE_KEY_FIELDS if name == "SSLKeyAndCertificate" else ()
        self.tenant = None if api.tenant == ALL_TENANTS else api.tenant

    def iter_pages(self, batch_size):
        for page in self.api.iter_pages(self.path, batch_size, self.fields):
            yield [ApiObject(raw, self.tenant, self.drop) for raw in page]

    def first(self):
        """The singleton object (SystemConfiguration); it always lives in admin."""
        response = self.api.request("GET", "/api/" + self.path, {"include_name": "true"},
                                    tenant=DEFAULT_TENANT)
        item = (response.get("results") or [None])[0] if "results" in response else response
        return ApiObject(item, DEFAULT_TENANT) if item else None


def setup_api(api):
    """Return the models for the scan, read over the REST API."""
    return {name: ApiModel(api, name, path, fields) for name, (path, fields) in API_MODELS.items()}


# Certificate / reference helpers

def sha256_hex(data):
    return hashlib.sha256(data).hexdigest().lower()


def parse_certificates(text):
    """Return every certificate in a PEM string (one per BEGIN/END block)."""
    if not text:
        return []
    data = text.encode("utf-8") if isinstance(text, str) else text
    if PEM_BEGIN not in data:
        try:
            data = base64.b64decode(data)
        except ValueError:
            return []
    certs = []
    position = 0
    while True:
        start = data.find(PEM_BEGIN, position)
        end = data.find(PEM_END, start) if start >= 0 else -1
        if end < 0:
            return certs
        position = end + len(PEM_END)
        certs.append(x509.load_pem_x509_certificate(data[start:position]))


def certificate_fingerprints(cert):
    """Return (SHA-256 of DER certificate, SHA-256 of DER SPKI)."""
    spki = cert.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return sha256_hex(cert.public_bytes(serialization.Encoding.DER)), sha256_hex(spki)


def certificate_identity(cert):
    """Return the names and key identifiers used to link a certificate to its issuer."""
    def extension(cls):
        try:
            return cert.extensions.get_extension_for_class(cls).value
        except Exception:
            return None

    ski = extension(x509.SubjectKeyIdentifier)
    aki = extension(x509.AuthorityKeyIdentifier)
    return {
        "subject_dn": cert.subject.rfc4514_string(),
        "issuer_dn": cert.issuer.rfc4514_string(),
        "ski": ski.digest.hex() if ski else None,
        "aki": aki.key_identifier.hex() if aki and aki.key_identifier else None,
    }


def known_signer(identity):
    """Return the known issuer and its kind from this certificate's AKI, if any."""
    aki = identity.get("aki")
    if aki and aki != identity.get("ski"):
        return SIGNER_SKI.get(aki)
    return None


def match_known(cert_sha, spki_sha):
    """Match fingerprints against the manifest: (match_type, entry) or None."""
    if cert_sha in BY_CERT_SHA:
        return MATCH_CERT, BY_CERT_SHA[cert_sha]
    if spki_sha in BY_SPKI_SHA:
        return MATCH_KEY, BY_SPKI_SHA[spki_sha][0]
    return None


def reference(entry):
    ref = {"name": entry["name"], "ccadb_id": entry["ccadb_id"],
           "variant": entry["variant"], "usage": entry["usage"],
           "kind": entry.get("kind", KIND_COMPROMISED)}
    if entry.get("trust_store_actions"):
        ref["trust_store_actions"] = entry["trust_store_actions"]
    return ref


def ref_uuids(data, field):
    """Return the uuids stored under <field>_uuid / <field>_uuids in a dict."""
    if not isinstance(data, dict):
        return []
    value = data.get("{}_uuids".format(field)) or data.get("{}_uuid".format(field)) or []
    return list(dict.fromkeys([value] if isinstance(value, str) else value))


# Step 1: SSLKeyAndCertificate

def collect_ssl_certificates(model, batch_size=API_PAGE_SIZE):
    """Fingerprint every SSLKeyAndCertificate, one API page at a time.

    Returns ({uuid: record}, number of certificates that could not be parsed).
    """
    records = {}
    failed = 0
    for batch in iter_batches(model, batch_size):
        for obj in batch:
            data = object_data(obj)
            parse_failed = False
            try:
                certs = parse_certificates((data.get("certificate") or {}).get("certificate"))
                bundle = [certificate_fingerprints(cert) for cert in certs]
            except Exception:
                log.exception("SSLKeyAndCertificate %s (%s): certificate could not be parsed",
                              obj.name, obj.uuid)
                parse_failed = True
                certs, bundle = [], []
            if not bundle:
                if not parse_failed:
                    log.error("SSLKeyAndCertificate %s (%s): no readable certificate",
                              obj.name, obj.uuid)
                failed += 1
                continue
            fps = bundle[0]
            bundled = [(sha, known) for sha, known in
                       ((fp[0], match_known(*fp)) for fp in bundle[1:]) if known]
            identities = [certificate_identity(cert) for cert in certs]
            parents = list(dict.fromkeys(
                ca["ca_uuid"] for ca in data.get("ca_certs") or [] if ca.get("ca_uuid")))
            records[obj.uuid] = {
                "uuid": obj.uuid,
                "name": obj.name,
                "tenant": tenant_name(obj),
                "cert_sha256": fps[0],
                "spki_sha256": fps[1],
                "parents": parents,
                "match": match_known(*fps),
                "signed_by": known_signer(identities[0]),
                "bundled_matches": bundled,
                "bundled_signers": [s for s in
                                    (known_signer(identity) for identity in identities[1:]) if s],
            }
            records[obj.uuid].update(identities[0])
    link_issuers(records)
    return records, failed


def link_issuers(records):
    """Add the issuing certificate of every certificate to its parents.

    The ca_certs references stored on the controller are only as current as the
    last time the chain was recomputed, so the chain is also derived from the
    certificates themselves: the issuer name must equal the subject name of the
    candidate and, when both carry one, the authority key identifier must equal
    the subject key identifier. Self-signed certificates have no issuer here.
    """
    by_subject = {}
    by_ski = {}
    for uuid, rec in records.items():
        by_subject.setdefault(rec["subject_dn"], []).append(uuid)
        if rec["ski"]:
            by_ski.setdefault(rec["ski"], []).append(uuid)
    for uuid, rec in records.items():
        if rec["issuer_dn"] == rec["subject_dn"]:
            continue
        candidates = set(by_subject.get(rec["issuer_dn"], []))
        if rec["aki"]:
            candidates.update(by_ski.get(rec["aki"], []))
        for candidate in candidates:
            other = records[candidate]
            if candidate == uuid or candidate in rec["parents"]:
                continue
            if rec["aki"] and other["ski"] and rec["aki"] != other["ski"]:
                continue
            if rec["issuer_dn"] != other["subject_dn"] and rec["aki"] != other["ski"]:
                continue
            rec["parents"].append(candidate)


def walk(start, neighbours, records):
    """Return every certificate reachable from start through neighbours()."""
    seen = set()
    stack = list(start)
    while stack:
        uuid = stack.pop()
        if uuid in seen or uuid not in records:
            continue
        seen.add(uuid)
        stack.extend(neighbours(uuid))
    return seen


def resolve_family(records, trust_chain=False):
    """Return {uuid: {"roles": [...], "via": [uuids]}} for affected certificates.

    A certificate is affected if it matches the manifest (COMPROMISED,
    ISSUER_OF_COMPROMISED for the issuer of a compromised intermediate), is a
    descendant of a compromised entry (CHILD_OF_COMPROMISED), is signed by a
    compromised intermediate identified from its Authority Key Identifier, or has
    a manifest certificate bundled in its own PEM, even when that issuer is not
    stored in Avi. Children follow the parent references in reverse and are
    resolved recursively. An ISSUER_OF_COMPROMISED certificate is reported
    itself, but its other children are not. "via" lists the certificates the
    role was derived from.

    With trust_chain=True only the roots being removed from vendor trust stores
    count: ROOT_REMOVED_FROM_TRUST_STORES for the root itself and
    CHAINS_TO_REMOVED_ROOT for what chains to it. These are not compromised, so
    they are resolved apart from the compromised entries.
    """
    children = {}
    for uuid, rec in records.items():
        for parent in rec["parents"]:
            children.setdefault(parent, []).append(uuid)

    related = {}

    def add(uuid, role, origin):
        entry = related.setdefault(uuid, {"roles": [], "via": []})
        if role not in entry["roles"]:
            entry["roles"].append(role)
        if origin not in entry["via"]:
            entry["via"].append(origin)

    def add_descendants(uuid, role, origin):
        for child in walk(children.get(uuid, []), lambda u: children.get(u, []), records):
            add(child, role, origin)

    def add_exposed(uuid, kind, flag_children=True):
        """uuid is signed by, or carries, a compromised key or a removed root."""
        if not in_family(kind, trust_chain):
            return
        role = ROLE_CHILD if kind == KIND_COMPROMISED else ROLE_UNDER_ROOT
        if kind == KIND_COMPROMISED or flag_children:
            add(uuid, role, uuid)
            add_descendants(uuid, role, uuid)

    for uuid, rec in records.items():
        if rec["match"] and in_family(rec["match"][1].get("kind", KIND_COMPROMISED), trust_chain):
            known = rec["match"][1]
            kind = known.get("kind", KIND_COMPROMISED)
            if kind == KIND_COMPROMISED:
                add(uuid, ROLE_COMPROMISED, uuid)
                add_descendants(uuid, ROLE_CHILD, uuid)
            elif kind == KIND_ROOT:
                add(uuid, ROLE_ROOT, uuid)
                if known.get("flag_children"):
                    add_descendants(uuid, ROLE_UNDER_ROOT, uuid)
            else:
                add(uuid, ROLE_ISSUER, uuid)
        for signer in [rec["signed_by"]] + rec["bundled_signers"]:
            if signer:
                add_exposed(uuid, signer[1])
        for _, bundled in rec["bundled_matches"]:
            add_exposed(uuid, bundled[1].get("kind", KIND_COMPROMISED),
                        bundled[1].get("flag_children"))
    for entry in related.values():
        entry["roles"].sort(key=ROLE_ORDER.index)
    return related


def without_compromised(trust_related, related):
    """Drop the compromised certificates from the trust-chain set.

    The compromised intermediates are signed by emSign Root TLS CA - G3, so they
    also chain to a removed root. They have to be replaced anyway, so they are
    reported as compromised only, never as "not compromised" trust-chain impact."""
    compromised = {ROLE_COMPROMISED, ROLE_CHILD}
    return {uuid: info for uuid, info in trust_related.items()
            if not compromised & set(related.get(uuid, {}).get("roles", ()))}


def exposure_details(uuid, records, info, trust_chain=False):
    """Return why a certificate is in the family: the manifest entry it matches,
    the known key that signed it, and the certificates its role was derived from."""
    rec = records[uuid]
    details = {}
    if rec["match"] and in_family(rec["match"][1].get("kind", KIND_COMPROMISED), trust_chain):
        details["match_type"] = rec["match"][0]
        details["matched_reference"] = reference(rec["match"][1])
    if rec["signed_by"] and in_family(rec["signed_by"][1], trust_chain):
        details["signed_by_known_key"] = rec["signed_by"][0]
    details["related_to_removed_root" if trust_chain else "related_to_compromised"] = [
        {"uuid": u, "name": records[u]["name"]} for u in info["via"] if u != uuid
    ]
    return details


def ssl_summary(uuid, records, related, trust_chain=False):
    """Short certificate entry for the objects that use it, with the compromised
    key (or removed root) it is tied to."""
    summary = {"uuid": uuid, "name": records[uuid]["name"], "roles": related[uuid]["roles"]}
    summary.update(exposure_details(uuid, records, related[uuid], trust_chain))
    return summary


def pki_summary(entry):
    """Short PKIProfile entry for the objects that use it: the CA certificates in
    the profile that matched, without the fingerprints."""
    hidden = ("certificate_sha256", "spki_sha256")
    return {"uuid": entry["uuid"], "name": entry["name"],
            "ca_certs": [{k: v for k, v in hit.items() if k not in hidden}
                         for hit in entry["ca_certs"]]}


def build_certificate_entries(records, related, trust_chain=False):
    """Report entries for the certificates in related.

    With trust_chain=True the entries describe trust-store removal, not
    compromise: they carry the impact type and remediation, and name the removed
    root they relate to in related_to_removed_root."""
    entries = []
    for uuid, info in related.items():
        rec = records[uuid]
        entry = {
            "uuid": uuid,
            "name": rec["name"],
            "tenant": rec["tenant"],
            "roles": info["roles"],
            "certificate_sha256": rec["cert_sha256"],
            "spki_sha256": rec["spki_sha256"],
        }
        if trust_chain:
            entry["compromised"] = False
            entry["impact_type"] = TRUST_CHAIN_IMPACT
            entry["remediation"] = TRUST_CHAIN_REMEDIATION
        entry.update(exposure_details(uuid, records, info, trust_chain))
        entry["parents"] = [
            {"uuid": u, "name": records[u]["name"]} for u in rec["parents"] if u in records
        ]
        entries.append(entry)
    entries.sort(key=lambda e: (ROLE_ORDER.index(e["roles"][0]), e["name"] or "", e["uuid"]))
    return entries


# Step 2: PKIProfile

def pki_hit(index, cert, fps, family, by_cert, by_spki, records, trust_chain):
    """Return the hit for one PKIProfile CA certificate, or None.

    family is the {uuid: ...} set of stored certificates for the kind of finding
    (compromised, or trust_chain for removed roots), by_cert / by_spki index it."""
    known = match_known(*fps)
    if known and not in_family(known[1].get("kind", KIND_COMPROMISED), trust_chain):
        known = None
    signer = known_signer(certificate_identity(cert))
    if signer and not in_family(signer[1], trust_chain):
        signer = None
    avi_uuid = by_cert.get(fps[0]) or by_spki.get(fps[1])
    if not known and not avi_uuid and not signer:
        return None
    hit = {
        "ca_certs_index": index,
        "match_type": known[0] if known else (MATCH_AVI_CERT if avi_uuid else MATCH_SIGNER),
        "certificate_sha256": fps[0],
        "spki_sha256": fps[1],
    }
    if known:
        hit["matched_reference"] = reference(known[1])
    if avi_uuid:
        hit["avi_certificate"] = ssl_summary(avi_uuid, records, family, trust_chain)
    if signer:
        hit["signed_by_known_key"] = signer[0]
    return hit


def collect_pki_profiles(model, records, related, trust_related, batch_size=API_PAGE_SIZE):
    """Return (affected profiles, informational profiles, unreadable CA count).

    The affected profiles are {uuid: entry} of PKIProfiles whose ca_certs hold an
    affected certificate or one signed by a known affected key. The informational
    profiles hold a root being removed from vendor trust stores (or a certificate
    under it). That does not affect Avi, which validates against the CAs listed in
    the profile, so they are reported only to show the hierarchy is in use."""
    families = [(related, False), (trust_related, True)]
    indexes = [({records[u]["cert_sha256"]: u for u in family},
                {records[u]["spki_sha256"]: u for u in family}) for family, _ in families]

    found = ({}, {})
    unreadable = 0
    for batch in iter_batches(model, batch_size):
        for obj in batch:
            hits = ([], [])
            for index, ca in enumerate(object_data(obj).get("ca_certs") or [], start=1):
                try:
                    certs = parse_certificates((ca or {}).get("certificate"))
                except Exception:
                    log.exception("PKIProfile %s (%s): ca_certs[%d] could not be parsed",
                                  obj.name, obj.uuid, index)
                    certs = []
                if not certs:
                    log.error("PKIProfile %s (%s): ca_certs[%d] has no readable certificate",
                              obj.name, obj.uuid, index)
                    unreadable += 1
                    continue
                fps = certificate_fingerprints(certs[0])
                for (family, trust_chain), (by_cert, by_spki), bucket in zip(
                        families, indexes, hits):
                    hit = pki_hit(index, certs[0], fps, family, by_cert, by_spki, records,
                                  trust_chain)
                    if hit:
                        bucket.append(hit)
            for bucket, target in zip(hits, found):
                if bucket:
                    target[obj.uuid] = {
                        "uuid": obj.uuid,
                        "name": obj.name,
                        "tenant": tenant_name(obj),
                        "ca_certs": bucket,
                    }
    return found[0], found[1], unreadable


# Step 3: ApplicationProfile (client certificate validation) and VirtualService

CLIENT_VALIDATION_PROFILES = ("http_profile", "tcp_app_profile")


def collect_application_profiles(model, affected_pki, batch_size=API_PAGE_SIZE):
    """Return {uuid: entry} of ApplicationProfiles validating client certificates
    with an affected PKIProfile (HTTP: http_profile, TCP/L4: tcp_app_profile)."""
    affected = {}
    for batch in iter_batches(model, batch_size):
        for obj in batch:
            data = object_data(obj)
            validation = []
            for profile_type in CLIENT_VALIDATION_PROFILES:
                profile = data.get(profile_type) or {}
                for pki_uuid in ref_uuids(profile, "pki_profile"):
                    if pki_uuid in affected_pki:
                        validation.append({
                            "profile_type": profile_type,
                            "ssl_client_certificate_mode": profile.get("ssl_client_certificate_mode"),
                            "pki_profile": pki_summary(affected_pki[pki_uuid]),
                        })
            if validation:
                affected[obj.uuid] = {"uuid": obj.uuid, "name": obj.name,
                                      "client_validation": validation}
    return affected


def collect_virtual_services(model, records, related, trust_related, affected_profiles,
                             affected_pools, affected_pool_groups, batch_size=API_PAGE_SIZE):
    """Return ({uuid: entry}, {uuid: entry}) of VirtualServices.

    The first holds the services that present an affected certificate, validate
    client certificates through an affected application profile, or send traffic
    to an affected pool (directly or through a pool group). The second holds the
    services presenting a certificate that chains to a root being removed from
    vendor trust stores. Only the presented certificate counts there: Avi's own
    validation of clients and servers does not use those trust stores."""
    affected, trust_affected = {}, {}
    for batch in iter_batches(model, batch_size):
        for obj in batch:
            data = object_data(obj)
            presented = ref_uuids(data, "ssl_key_and_certificate")
            certs = [u for u in presented if u in related]
            trust_certs = [u for u in presented if u in trust_related]
            if trust_certs:
                trust_affected[obj.uuid] = {
                    "uuid": obj.uuid, "name": obj.name, "tenant": tenant_name(obj),
                    "certificates": [ssl_summary(u, records, trust_related, trust_chain=True)
                                     for u in trust_certs],
                }
            used_profiles = [("application_profile", u)
                             for u in ref_uuids(data, "application_profile")]
            used_pools = [("pool", u) for u in ref_uuids(data, "pool")]
            used_pools.extend(("sp_pool", u) for u in ref_uuids(data, "sp_pool"))
            used_groups = [("pool_group", u) for u in ref_uuids(data, "pool_group")]
            for service in data.get("services") or []:
                used_profiles.extend(("service_override_%s" % service.get("port"), u)
                                     for u in ref_uuids(service, "override_application_profile"))
            for selector in data.get("service_pool_select") or []:
                used_as = "service_pool_select_%s" % selector.get("service_port")
                used_pools.extend((used_as, u) for u in ref_uuids(selector, "service_pool"))
                used_groups.extend((used_as, u)
                                   for u in ref_uuids(selector, "service_pool_group"))
            profiles = [dict(affected_profiles[u], used_as=used_as)
                        for used_as, u in used_profiles if u in affected_profiles]
            pools = [dict(affected_pools[u], used_as=used_as)
                     for used_as, u in used_pools if u in affected_pools]
            pool_groups = [dict(affected_pool_groups[u], used_as=used_as)
                           for used_as, u in used_groups if u in affected_pool_groups]
            if not certs and not profiles and not pools and not pool_groups:
                continue
            entry = {"uuid": obj.uuid, "name": obj.name, "tenant": tenant_name(obj)}
            if certs:
                entry["certificates"] = [ssl_summary(u, records, related) for u in certs]
            if profiles:
                entry["application_profiles"] = profiles
            if pools:
                entry["pools"] = pools
            if pool_groups:
                entry["pool_groups"] = pool_groups
            affected[obj.uuid] = entry
    return affected, trust_affected


# Step 4: Pool

def collect_pools(model, records, related, affected_pki, batch_size=API_PAGE_SIZE):
    """Return {uuid: entry} of Pools using an affected PKIProfile or client certificate."""
    affected = {}
    for batch in iter_batches(model, batch_size):
        for obj in batch:
            data = object_data(obj)
            pki = [u for u in ref_uuids(data, "pki_profile") if u in affected_pki]
            certs = [u for u in ref_uuids(data, "ssl_key_and_certificate") if u in related]
            if not pki and not certs:
                continue
            entry = {"uuid": obj.uuid, "name": obj.name, "tenant": tenant_name(obj)}
            if pki:
                entry["pki_profiles"] = [pki_summary(affected_pki[u]) for u in pki]
            if certs:
                entry["client_certificates"] = [ssl_summary(u, records, related) for u in certs]
            affected[obj.uuid] = entry
    return affected


def collect_pool_groups(model, affected_pools, batch_size=API_PAGE_SIZE):
    """Return {uuid: entry} of PoolGroups with an affected Pool as a member."""
    affected = {}
    for batch in iter_batches(model, batch_size):
        for obj in batch:
            members = [u for member in object_data(obj).get("members") or []
                       for u in ref_uuids(member, "pool") if u in affected_pools]
            if members:
                affected[obj.uuid] = {
                    "uuid": obj.uuid, "name": obj.name,
                    "pools": [{"uuid": u, "name": affected_pools[u]["name"]}
                              for u in dict.fromkeys(members)],
                }
    return affected


# Step 5: SystemConfiguration (portal and secure channel certificates)

def describe_system_certificates(uuids, records, related, trust_related=()):
    """Return the status of each configured certificate.

    AFFECTED if the certificate is in the affected set from step 1, NOT_AFFECTED
    otherwise, NOT_SCANNED if the certificate object could not be read. A
    certificate in trust_related also carries its trust-chain roles, which do not
    change the status.
    """
    entries = []
    for uuid in uuids:
        if uuid not in records:
            log.error("SystemConfiguration: configured certificate %s was not scanned", uuid)
            entries.append({"uuid": uuid, "name": None, "status": STATUS_UNKNOWN})
            continue
        entry = {
            "uuid": uuid,
            "name": records[uuid]["name"],
            "status": STATUS_AFFECTED if uuid in related else STATUS_OK,
        }
        if uuid in related:
            entry["roles"] = related[uuid]["roles"]
            entry.update(exposure_details(uuid, records, related[uuid]))
        if uuid in trust_related:
            entry["trust_chain_roles"] = trust_related[uuid]["roles"]
        entries.append(entry)
    return entries


def collect_system_certificates(model, records, related, trust_related):
    """Return the certificates used by the controller portal and the secure channel.

    The portal can hold up to 2 certificates, the secure channel 1. An empty
    list means the system default certificates are in use. Trust-chain impact is
    checked for the portal only: browsers and API clients validate it, while the
    secure channel certificate is validated by the Service Engines against the
    Controller's own root CA.
    """
    config = model.first()
    data = object_data(config) if config else {}
    portal = ref_uuids(data.get("portal_configuration"), "sslkeyandcertificate")
    secure_channel = ref_uuids(data.get("secure_channel_configuration"),
                               "sslkeyandcertificate")
    return {
        "portal_certificates": {
            "using_system_default": not portal,
            "certificates": describe_system_certificates(portal, records, related,
                                                         trust_related),
        },
        "secure_channel_certificate": {
            "using_system_default": not secure_channel,
            "certificates": describe_system_certificates(secure_channel, records, related),
        },
    }


# Scan and report

def scan(models, batch_size=API_PAGE_SIZE, source=None):
    """Run all steps and return the report as a dict (JSON serialisable).

    source describes where the data came from (controller, tenant, TLS check)."""
    SCANNED.clear()
    records, failed = collect_ssl_certificates(models["SSLKeyAndCertificate"], batch_size)
    related = resolve_family(records)
    trust_related = without_compromised(resolve_family(records, trust_chain=True), related)
    pki, pki_info, pki_unreadable = collect_pki_profiles(
        models["PKIProfile"], records, related, trust_related, batch_size
    )
    application_profiles = collect_application_profiles(models["ApplicationProfile"], pki,
                                                        batch_size)
    pools = collect_pools(models["Pool"], records, related, pki, batch_size)
    pool_groups = collect_pool_groups(models["PoolGroup"], pools, batch_size)
    virtual_services, trust_virtual_services = collect_virtual_services(
        models["VirtualService"], records, related, trust_related, application_profiles,
        pools, pool_groups, batch_size
    )
    system = collect_system_certificates(models["SystemConfiguration"], records, related,
                                         trust_related)
    system_unreadable = sum(
        cert["status"] == STATUS_UNKNOWN
        for key in SYSTEM_CATEGORIES.values()
        for cert in system[key]["certificates"]
    )

    def by_name(entries):
        return sorted(entries, key=lambda e: (e["name"] or "", e["uuid"]))

    affected = {
        "SSLKeyAndCertificate": build_certificate_entries(records, related),
        "PKIProfile": by_name(pki.values()),
        "VirtualService": by_name(virtual_services.values()),
        "Pool": by_name(pools.values()),
    }
    summary = {
        name: {"scanned": SCANNED.get(name, 0), "affected": len(affected[name])}
        for name in MODEL_CATEGORIES
    }
    for name, key in SYSTEM_CATEGORIES.items():
        configured = system[key]["certificates"]
        affected[name] = [c for c in configured if c["status"] == STATUS_AFFECTED]
        summary[name] = {"scanned": len(configured), "affected": len(affected[name])}
    trust_chain = {
        "description": TRUST_CHAIN_NOTE,
        "remediation": TRUST_CHAIN_REMEDIATION,
        "SSLKeyAndCertificate": build_certificate_entries(records, trust_related,
                                                          trust_chain=True),
        "VirtualService": by_name(trust_virtual_services.values()),
        "Portal-Cert": [c for c in system["portal_certificates"]["certificates"]
                        if "trust_chain_roles" in c],
        "informational": {
            "note": "These PKIProfiles hold a root being removed from vendor trust stores. "
                    "Avi validates against the CAs in the profile, so they are not affected.",
            "PKIProfile": by_name(pki_info.values()),
        },
    }
    trust_chain["summary"] = {
        name: len(trust_chain[name])
        for name in ("SSLKeyAndCertificate", "VirtualService", "Portal-Cert")
    }
    trust_chain["summary"]["PKIProfile (informational)"] = len(pki_info)
    report = {
        "title": "eMudhra Certificate Exposure Scan",
        "product": "Broadcom VMware Avi",
        "report_type": "Security Assessment Report | Read-only Scan",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifest_version": MANIFEST_VERSION,
        "manifest_entries": len(EMUDHRA_COMPROMISED_CERTS),
        "source": source or {"mode": "unknown"},
        "legend": report_legend(),
        "summary": summary,
        "system_configuration": system,
        "affected": affected,
        "trust_chain_impact": trust_chain,
        "unparsed_certificates": failed,
        "unparsed_pki_certificates": pki_unreadable,
        "unscanned_system_certificates": system_unreadable,
    }
    # action_items follows the summary so the first thing in the file is what to fix.
    items = action_items(report)
    return {key: value for k, v in report.items()
            for key, value in ((k, v),) + ((("action_items", items),) if k == "summary" else ())}


def report_output(report):
    """The report as written to JSON. The raw system_configuration section is left
    out; the portal and secure channel results remain under summary, affected and
    trust_chain_impact."""
    return {k: v for k, v in report.items() if k != "system_configuration"}


def write_report(report, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report_output(report), handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def load_report(path):
    """Read a JSON report written by an earlier run (for --from-json)."""
    with open(path, encoding="utf-8") as handle:
        report = json.load(handle)
    if not isinstance(report, dict) or not {"summary", "affected", "trust_chain_impact"} <= set(report):
        raise ValueError("{} is not an eMudhra scan report".format(path))
    return report


def print_source(source):
    """Say what was scanned. A single-tenant scan does not cover other tenants."""
    if not source or source.get("mode") != "api":
        return
    print(" Controller: {} | Tenant: {} | API {}".format(
        source["controller"], "all" if source["tenant"] == ALL_TENANTS else source["tenant"],
        source.get("api_version") or "default"))
    if source.get("tls_verification") == "disabled":
        print(" WARNING: the controller TLS certificate was NOT verified.")
    if source["tenant"] != ALL_TENANTS:
        print(" Only tenant '{}' was scanned. Objects in other tenants, and references to\n"
              " them, are not covered; use --all-tenants for a complete scan.".format(source["tenant"]))
    print("-" * 60)


def print_banner():
    rule = "=" * 60
    print(rule)
    print(" Broadcom VMware Avi")
    print(" eMudhra Certificate Exposure Scan")
    print(" Security Assessment Report | Read-only Scan")
    print(rule)


def print_section(title, subtitle):
    print("\n" + title)
    print("-" * 60)
    print(subtitle)
    print()


def print_report(report):
    """Print the short console summary; full detail goes to the JSON file.

    Section 1 concludes on compromised exposure. Section 2 lists the potential
    trust-chain compatibility impact, which is not a compromise."""
    print_banner()
    print_source(report.get("source"))

    print_section("1. COMPROMISED CERTIFICATE EXPOSURE",
                  "Certificates from the eight compromised eMudhra intermediate keys,\n"
                  "their children, and the objects that use them.")
    print("{:<22}{:>9}{:>10}".format("Category", "Scanned", "Affected"))
    for name in CATEGORIES:
        counts = report["summary"][name]
        print("{:<22}{:>9}{:>10}".format(name, counts["scanned"], counts["affected"]))
    affected = sum(counts["affected"] for counts in report["summary"].values())
    if affected:
        print("\nConclusion: AFFECTED. {} object(s) use a compromised eMudhra certificate "
              "or a certificate issued under one. Replace them.".format(affected))
    else:
        print("\nConclusion: NOT AFFECTED. No compromised eMudhra certificate was found.")

    trust = report["trust_chain_impact"]["summary"]
    print_section("2. POTENTIAL TRUST-CHAIN COMPATIBILITY IMPACT (not compromised)",
                  "Certificates chaining to an eMudhra root that vendors are removing from\n"
                  "their trust stores. They may stop validating on affected clients.")
    print("{:<22}{:>9}{:>10}".format("Category", "Scanned", "Impacted"))
    for name, count in trust.items():
        if name.startswith("PKIProfile"):
            continue
        print("{:<22}{:>9}{:>10}".format(name, report["summary"][name]["scanned"], count))
    impacted = trust["SSLKeyAndCertificate"]
    informational = trust["PKIProfile (informational)"]
    if informational:
        print("\nInformational: {} PKIProfile(s) hold a removed root. Avi validates against "
              "the CAs in the profile, so they are not impacted.".format(informational))
    if impacted:
        actions = ["{} {}".format(a["vendor"], a["effective"])
                   for entry in EMUDHRA_COMPROMISED_CERTS
                   for a in entry.get("trust_store_actions", [])]
        if actions:
            print("\nTrust store actions: " + "; ".join(actions))
        print("\nConclusion: REVIEW. {} certificate(s), used by {} virtual service(s), may need "
              "reissuing from a CA that remains in the vendor trust stores."
              .format(impacted, trust["VirtualService"]))
    else:
        print("\nConclusion: NO IMPACT. No certificate chains to a root being removed.")

    unparsed_ssl = report["unparsed_certificates"]
    unparsed_pki = report["unparsed_pki_certificates"]
    unscanned_system = report["unscanned_system_certificates"]
    if unparsed_ssl or unparsed_pki or unscanned_system:
        print("\nWARNING: scan is incomplete: {} SSL certificate(s), {} PKI CA "
              "certificate(s) could not be read; {} configured system certificate(s) "
              "could not be scanned.".format(unparsed_ssl, unparsed_pki, unscanned_system))


# Action table: one row per certificate or PKIProfile to fix

PRIORITIES = ("P1", "P2", "P3")
TABLE_ROWS = 20          # rows shown per section unless --all
GROUP_AFTER = 5          # collapse more than this many same-kind findings into one row
NAME_LIST_MAX = 3        # list the dependent objects by name up to this many
TENANT_ROLLUP_MIN = 6    # show the per-tenant counts from this many tenants on

SECTION_COMPROMISED = "compromised"
SECTION_TRUST = "trust"

FINDING_TEXT = {
    ROLE_COMPROMISED: "Compromised eMudhra intermediate",
    ROLE_CHILD: "Issued under a compromised eMudhra CA",
    ROLE_ISSUER: "Issuer of a compromised CA (not itself compromised)",
    ROLE_ROOT: "Root being removed from vendor trust stores",
    ROLE_UNDER_ROOT: "Chains to a root being removed from trust stores",
}
ACTION_REPLACE = "Replace with a certificate from an unaffected key and CA"
ACTION_RETIRE = "Confirm it is unused, then delete it; otherwise replace it"
ACTION_REVIEW = "No direct action. Review only"
ACTION_PKI = "Remove the CA entry; keep the other trust anchors"
ACTION_PKI_CROSS = ("Remove the cross-signed entry; keep the AAA root if other chains need "
                    "it. If you cannot remove it now, enable CRL checking")
ACTION_PKI_RETIRE = "Remove the CA entry, or delete the profile if unused"
UNUSED = "not in use"

VERIFY_CERT = ("Check the certificate presented in the TLS handshake and confirm clients "
               "connect. Rerun the script")
VERIFY_PKI = ("Rerun the script and confirm the entry is gone. Test the client-certificate "
              "validation (VS) or backend validation (Pool) that uses the profile")
VERIFY_REVIEW = "Rerun the script after changes to the related certificates"
VERIFY_UNUSED = "Confirm nothing depends on it, then rerun the script"
VERIFY_TRUST = "Confirm the trust path on the affected clients and that required TLS flows work"

ROLE_MEANING = {
    ROLE_COMPROMISED: "Matches one of the eight known compromised intermediates, or its "
                      "Sectigo cross-signed copy (same key).",
    ROLE_CHILD: "Issued by a compromised intermediate, so anyone with the leaked key can "
                "forge certificates that chain to the same CA.",
    ROLE_ISSUER: "Signed a compromised intermediate. The issuer itself is not compromised "
                 "and its other children are not reported.",
    ROLE_ROOT: "A root that vendors are removing from their trust stores. Not compromised; "
               "certificates that chain to it may need reissuing.",
    ROLE_UNDER_ROOT: "Chains to a root being removed, by the stored chain, issuer name or "
                     "Authority Key Identifier. Not compromised; clients may stop trusting it.",
}
PRIORITY_MEANING = {
    "P1": "Act now. The certificate or PKIProfile is in use by a VirtualService, Pool, "
          "portal or secure channel. For trust-chain items P1 means reissue to avoid "
          "client validation failures, not a compromise.",
    "P2": "Review. Related to the incident but not itself compromised; no direct action.",
    "P3": "Not in use. Confirm nothing depends on it, then delete it; if something does, "
          "treat it as P1.",
}


def pool_targets(pool):
    """Uuids of the certificates and PKIProfiles that make a Pool affected."""
    return ({p["uuid"] for p in pool.get("pki_profiles", [])}
            | {c["uuid"] for c in pool.get("client_certificates", [])})


def vs_targets(vs, pools):
    """Uuids of the certificates and PKIProfiles that make a VirtualService affected."""
    targets = {c["uuid"] for c in vs.get("certificates", [])}
    for profile in vs.get("application_profiles", []):
        targets.update(v["pki_profile"]["uuid"] for v in profile["client_validation"])
    used = list(vs.get("pools", []))
    for group in vs.get("pool_groups", []):
        used.extend(group["pools"])
    for pool in used:
        targets |= pool_targets(pools.get(pool["uuid"], pool))
    return targets


def dependents(entries_by_kind):
    """Return {target uuid: {(type, uuid): object}} from (type, entries, targets)."""
    users = defaultdict(dict)
    for kind, entries, targets_of in entries_by_kind:
        for entry in entries:
            obj = {"type": kind, "uuid": entry["uuid"], "name": entry.get("name") or entry["uuid"],
                   "tenant": entry.get("tenant")}
            for target in targets_of(entry):
                users[target][(kind, entry["uuid"])] = obj
    return users


def issuer_label(entry):
    """The compromised CA a certificate is tied to, for grouping."""
    return (entry.get("signed_by_known_key")
            or (entry.get("matched_reference") or {}).get("name")
            or next((r["name"] for r in entry.get("related_to_compromised", []) if r.get("name")), "")
            or "")


def make_finding(section, kind, entry, pri, text, action, verify, users, via=""):
    return {"section": section, "type": kind, "uuid": entry["uuid"], "name": entry["name"] or entry["uuid"],
            "tenant": entry.get("tenant"), "pri": pri, "finding": text, "action": action,
            "verify": verify, "via": via, "users": sorted(users, key=lambda u: (u["type"], u["name"], u["uuid"]))}


def certificate_finding(section, entry, users):
    role = entry["roles"][0]
    text = FINDING_TEXT.get(role, role)
    if section == SECTION_TRUST:
        pri, action, verify = ("P1" if users else "P3"), TRUST_CHAIN_REMEDIATION, VERIFY_TRUST
    elif role == ROLE_ISSUER:
        pri, action, verify = "P2", ACTION_REVIEW, VERIFY_REVIEW
    else:
        pri, action, verify = ("P1", ACTION_REPLACE, VERIFY_CERT) if users else (
            "P3", ACTION_RETIRE, VERIFY_UNUSED)
    if pri == "P3":
        text += " ({})".format(UNUSED)
        verify = VERIFY_UNUSED
    return make_finding(section, "Certificate", entry, pri, text, action, verify, users,
                        issuer_label(entry))


def profile_hit_kinds(profile):
    """Return (has compromised hit, has cross-signed hit) for a PKIProfile."""
    compromised = cross = False
    for hit in profile["ca_certs"]:
        ref = hit.get("matched_reference") or {}
        avi_roles = (hit.get("avi_certificate") or {}).get("roles") or []
        issuer_only = (ref.get("kind") == KIND_ISSUER if ref
                       else bool(avi_roles) and avi_roles[0] == ROLE_ISSUER)
        if not issuer_only:
            compromised = True
            cross = cross or "cross" in (ref.get("variant") or "").lower()
    return compromised, cross


def profile_finding(profile, users):
    compromised, cross = profile_hit_kinds(profile)
    if not compromised:
        return make_finding(SECTION_COMPROMISED, "PKIProfile", profile, "P2",
                            "Trusts the issuer of a compromised CA (not itself compromised)",
                            ACTION_REVIEW, VERIFY_REVIEW, users)
    text = "Trusts a Sectigo cross-signed compromised CA" if cross else "Trusts a compromised eMudhra CA"
    if users:
        return make_finding(SECTION_COMPROMISED, "PKIProfile", profile, "P1", text,
                            ACTION_PKI_CROSS if cross else ACTION_PKI, VERIFY_PKI, users)
    return make_finding(SECTION_COMPROMISED, "PKIProfile", profile, "P3",
                        "{} ({})".format(text, UNUSED), ACTION_PKI_RETIRE, VERIFY_UNUSED, users)


def build_findings(report):
    """One finding per certificate or PKIProfile to fix, with the objects that depend on it."""
    affected, trust = report["affected"], report["trust_chain_impact"]
    pools = {p["uuid"]: p for p in affected["Pool"]}
    users = dependents([
        ("VS", affected["VirtualService"], lambda e: vs_targets(e, pools)),
        ("Pool", affected["Pool"], pool_targets),
        ("Portal", affected["Portal-Cert"], lambda e: {e["uuid"]}),
        ("Secure channel", affected["Secure-Channel-Cert"], lambda e: {e["uuid"]}),
    ])
    trust_users = dependents([
        ("VS", trust["VirtualService"],
         lambda e: {c["uuid"] for c in e["certificates"]}),
        ("Portal", trust["Portal-Cert"], lambda e: {e["uuid"]}),
    ])
    findings = [certificate_finding(SECTION_COMPROMISED, e, list(users[e["uuid"]].values()))
                for e in affected["SSLKeyAndCertificate"]]
    findings += [profile_finding(e, list(users[e["uuid"]].values())) for e in affected["PKIProfile"]]
    findings += [certificate_finding(SECTION_TRUST, e, list(trust_users[e["uuid"]].values()))
                 for e in trust["SSLKeyAndCertificate"]]
    return findings


def action_items(report):
    """The findings as stored in the JSON report: what to fix, what to do, how to verify
    it, and every object that depends on it."""
    items = sorted(build_findings(report),
                   key=lambda f: (PRIORITIES.index(f["pri"]), f["section"], f["name"], f["uuid"]))
    return [{"priority": f["pri"], "section": f["section"], "fix_type": f["type"],
             "name": f["name"], "uuid": f["uuid"], "tenant": f["tenant"],
             "finding": f["finding"], "next_action": f["action"], "verify": f["verify"],
             "affected_objects": [{k: u[k] for k in ("type", "name", "uuid", "tenant")}
                                  for u in f["users"]]} for f in items]


def report_legend():
    return {
        "roles": ROLE_MEANING,
        "priorities": PRIORITY_MEANING,
        "sections": {
            SECTION_COMPROMISED: "affected: certificates from the compromised eMudhra keys, "
                                 "their children, and the objects that use them.",
            SECTION_TRUST: "trust_chain_impact: not compromised; certificates that chain to a "
                           "root being removed from vendor trust stores.",
        },
        "guide": "Run the script with --explain for the background and how to read this report.",
    }


EXPLAIN = """\
eMudhra certificate compromise: what this scan does

THE ISSUE
  The private keys of eight eMudhra intermediate CAs (6 TLS, 2 code signing)
  were compromised through weak key generation. Anyone holding a key can issue
  certificates that chain to that CA. Each intermediate also exists as a Sectigo
  cross-signed certificate with the same public key, chained to AAA Certificate
  Services, so there is a second trust path.

WHAT IT CHECKS (read-only)
  SSLKeyAndCertificate, PKIProfile, VirtualService, Pool, and the portal and
  secure channel certificates. A certificate is matched by:
    - its SHA-256 fingerprint (the exact certificate);
    - its public key hash, SPKI SHA-256 (catches the Sectigo cross-signed copy);
    - Authority/Subject Key Identifier (finds children when the CA is not stored).
  Checking for the root alone is not enough: an affected intermediate can be
  configured directly, the cross-signed copy gives another path, and the same
  certificate can matter for inbound (VS) or outbound (Pool) TLS.
  AAA Certificate Services is not compromised. It is a possible path to the
  cross-signed copy. Keeping it is not a finding by itself.

HOW IT CONNECTS
  The scan logs in to the controller REST API over HTTPS and only reads. The
  controller certificate is verified (--ca-cert FILE, or the system trust store).
  One tenant is scanned: admin unless --tenant NAME is given; --all-tenants scans
  every tenant. Objects in other tenants, and references to them, are not seen by
  a single-tenant scan.

HOW TO READ THE RESULT
  Section 1 (compromised) needs action. Section 2 (trust-chain) is not a
  compromise: those certificates chain to a root that vendors are removing, so
  clients may stop trusting them and they may need reissuing.
{roles}
PRIORITIES
{priorities}

WHAT TO DO
  Replace or remove the P1 items, rerun the script, confirm the item is gone.
  Do not remove a root such as AAA only because it is listed; other chains may
  need it.
  Use --detail NAME to see everything that depends on one item.
  Each action item in the JSON report (action_items) carries its next action and
  how to verify it.
"""


def explain_text():
    roles = "\n".join("  {}\n    {}".format(role, textwrap.fill(
        ROLE_MEANING[role], 74, subsequent_indent="    ")) for role in ROLE_ORDER)
    priorities = "\n".join("  {}  {}".format(p, textwrap.fill(
        PRIORITY_MEANING[p], 72, subsequent_indent="      ")) for p in PRIORITIES)
    return EXPLAIN.format(roles="\nROLES (the roles field in the report)\n" + roles + "\n",
                          priorities=priorities)


def filter_findings(findings, priorities=None, tenant=None):
    """Apply --priority and --tenant. With a tenant, keep the findings the tenant owns
    or depends on, and count only that tenant's dependent objects."""
    result = []
    for finding in findings:
        if priorities and finding["pri"] not in priorities:
            continue
        if tenant:
            users = [u for u in finding["users"] if u["tenant"] == tenant]
            if finding["tenant"] != tenant and not users:
                continue
            finding = dict(finding, users=users)
        result.append(finding)
    return result


def group_findings(findings):
    """Return the table rows. Findings of the same kind and issuer collapse into one
    row when there are many; unused (P3) findings collapse into one row per section
    and type."""
    groups = {}
    for f in findings:
        key = ((f["section"], f["type"], "P3") if f["pri"] == "P3"
               else (f["section"], f["type"], f["pri"], f["finding"], f["via"]))
        groups.setdefault(key, []).append(f)
    rows = []
    for key, members in groups.items():
        if len(members) <= (1 if key[2] == "P3" else GROUP_AFTER):
            rows.extend(dict(m, count=1, members=[m]) for m in members)
            continue
        first = members[0]
        merged = {u["uuid"] + u["type"]: u for m in members for u in m["users"]}
        same = lambda field: len({m[field] for m in members}) == 1
        plural = "certificates" if first["type"] == "Certificate" else "PKIProfiles"
        name = "{} {}".format(len(members), plural)
        if first["via"] and same("via") and first["pri"] != "P3":
            name += " under " + first["via"]
        rows.append(dict(first, name=name, tenant=None, count=len(members), members=members,
                         users=list(merged.values()),
                         finding=first["finding"] if same("finding") else "Affected ({})".format(UNUSED),
                         action=first["action"] if same("action") else ACTION_RETIRE,
                         verify=first["verify"] if same("verify") else VERIFY_UNUSED))
    rows.sort(key=lambda r: (PRIORITIES.index(r["pri"]), -len(r["users"]), r["name"], r["uuid"]))
    return rows


def impact_text(users):
    """Dependent objects: names when there are few, counts when there are many."""
    parts = []
    for kind, plural in (("VS", "VS"), ("Pool", "Pools")):
        items = [u["name"] for u in users if u["type"] == kind]
        if items:
            parts.append("{}: {}".format(kind, ", ".join(items)) if len(items) <= NAME_LIST_MAX
                         else "{} {}".format(len(items), plural))
    parts.extend(kind.lower() for kind in ("Portal", "Secure channel")
                 if any(u["type"] == kind for u in users))
    return "; ".join(parts) or "-"


def object_name(row):
    return "{} ({})".format(row["name"], row["tenant"]) if row["tenant"] else row["name"]


def render_table(headers, lines, width):
    """Print a table that fits width: the widest columns shrink and their text wraps."""
    widths = [max(len(h), *(len(c) for c in col)) for h, col in zip(headers, zip(*lines))]
    gap = 2
    while sum(widths) + gap * (len(widths) - 1) > width and max(widths) > 14:
        widths[widths.index(max(widths))] -= 1
    out = ["  ".join(h.ljust(w) for h, w in zip(headers, widths)).rstrip(),
           "  ".join("-" * w for w in widths)]
    for line in lines:
        cells = [textwrap.wrap(c, w) or [""] for c, w in zip(line, widths)]
        for i in range(max(len(c) for c in cells)):
            out.append("  ".join((c[i] if i < len(c) else "").ljust(w)
                                 for c, w in zip(cells, widths)).rstrip())
    print("\n".join(out))


def print_rows(rows, show_all, width):
    shown = rows if show_all else rows[:TABLE_ROWS]
    render_table(("Pri", "Type", "Fix this", "Finding", "Impact", "Next action"),
                 [(r["pri"], r["type"], object_name(r), r["finding"], impact_text(r["users"]),
                   r["action"]) for r in shown], width)
    if len(rows) > len(shown):
        print("... {} more row(s). Use --all, --priority P1, --csv FILE or the JSON report."
              .format(len(rows) - len(shown)))


def print_tenant_rollup(findings, width):
    counts = defaultdict(set)
    for f in findings:
        if f["tenant"]:
            counts[f["tenant"]].add((f["type"], f["uuid"]))
        for u in f["users"]:
            if u["tenant"]:
                counts[u["tenant"]].add((u["type"], u["uuid"]))
    if len(counts) < TENANT_ROLLUP_MIN:
        return
    ranked = sorted(counts.items(), key=lambda item: (-len(item[1]), item[0]))
    print("\nAffected objects per tenant (top 10 of {}; use --tenant NAME)".format(len(ranked)))
    render_table(("Tenant", "Objects"), [(t, str(len(o))) for t, o in ranked[:10]], width)


def print_action_table(report, priorities=None, tenant=None, show_all=False, width=None):
    width = width or shutil.get_terminal_size((100, 24)).columns
    findings = filter_findings(build_findings(report), priorities, tenant)
    sections = {s: [f for f in findings if f["section"] == s]
                for s in (SECTION_COMPROMISED, SECTION_TRUST)}

    compromised = sections[SECTION_COMPROMISED]
    objects = {(u["type"], u["uuid"]) for f in compromised for u in f["users"]}
    counts = ", ".join("{}: {}".format(p, sum(f["pri"] == p for f in compromised))
                       for p in PRIORITIES if any(f["pri"] == p for f in compromised))
    print_section("ACTION REQUIRED", "Fix the items below. Each row is one certificate or "
                  "PKIProfile; Impact shows what depends on it.")
    if compromised:
        print("{} item(s) to fix, {} dependent object(s)   ({})\n".format(
            len(compromised), len(objects), counts))
        print_rows(group_findings(compromised), show_all, width)
        print_tenant_rollup(compromised, width)
    else:
        print("None.")

    trust = sections[SECTION_TRUST]
    if trust:
        print_section("TRUST-CHAIN REVIEW (not compromised)",
                      "May stop validating on clients that drop the removed roots.")
        print_rows(group_findings(trust), show_all, width)
    print("\nUse --detail NAME to list every object that depends on one item.")


def print_detail(report, needle):
    """List every dependent object of the findings whose name or uuid matches needle."""
    matches = [f for f in build_findings(report)
               if needle.lower() in f["name"].lower() or needle.lower() in f["uuid"].lower()]
    if not matches:
        print("No affected certificate or PKIProfile matches '{}'.".format(needle))
        return 0
    for f in sorted(matches, key=lambda f: (PRIORITIES.index(f["pri"]), f["name"])):
        print("\n{} {} {}".format(f["pri"], f["type"], object_name(f)))
        print("  uuid:    {}".format(f["uuid"]))
        print("  finding: {}".format(f["finding"]))
        print("  action:  {}".format(f["action"]))
        print("  verify:  {}".format(f["verify"]))
        if not f["users"]:
            print("  used by: nothing")
        for u in f["users"]:
            print("  used by: {:<15}{}".format(u["type"], object_name(u)))
    return len(matches)


def write_csv(report, path):
    """One row per fix and dependent object (a fix with no dependents gets one row)."""
    with open(path, "w", encoding="utf-8", newline="") as handle:
        out = csv.writer(handle)
        out.writerow(["priority", "section", "fix_type", "fix_name", "fix_uuid", "fix_tenant",
                      "finding", "next_action", "verify", "affected_type", "affected_name",
                      "affected_uuid", "affected_tenant"])
        findings = build_findings(report)
        findings.sort(key=lambda f: (PRIORITIES.index(f["pri"]), f["section"], f["name"], f["uuid"]))
        for f in findings:
            head = [f["pri"], f["section"], f["type"], f["name"], f["uuid"], f["tenant"] or "",
                    f["finding"], f["action"], f["verify"]]
            for u in f["users"] or [{"type": "", "name": "", "uuid": "", "tenant": None}]:
                out.writerow(head + [u["type"], u["name"], u["uuid"], u["tenant"] or ""])


def priority_list(value):
    items = [item.strip().upper() for item in value.split(",") if item.strip()]
    bad = [item for item in items if item not in PRIORITIES]
    if bad or not items:
        raise argparse.ArgumentTypeError("use a comma separated list of {}".format(", ".join(PRIORITIES)))
    return set(items)


def read_password(args):
    """The API password from AVI_PASSWORD, stdin or a prompt; never from an argument."""
    if os.environ.get("AVI_PASSWORD"):
        return os.environ["AVI_PASSWORD"]
    if args.password_stdin:
        return sys.stdin.readline().rstrip("\r\n")
    if sys.stdin.isatty():
        return getpass.getpass("Password for {}: ".format(args.username))
    raise ApiError("no password: set AVI_PASSWORD or use --password-stdin")


def connect_models(args):
    """Return (models, api, source) for the chosen way of reading the configuration."""
    tenant = ALL_TENANTS if args.all_tenants else args.tenant
    api = AviApi(args.controller, args.username, read_password(args), tenant=tenant,
                 ca_cert=args.ca_cert, insecure=args.insecure, api_version=args.api_version,
                 timeout=args.timeout)
    if args.insecure:
        print("WARNING: TLS certificate verification is disabled.", file=sys.stderr)
    api.connect()
    source = {"mode": "api", "controller": api.host, "tenant": tenant,
              "api_version": api.api_version, "tls_verification": api.tls}
    return setup_api(api), api, source


def build_parser():
    parser = argparse.ArgumentParser(
        description="Find eMudhra compromised intermediate CA exposure in an Avi configuration "
                    "through the controller REST API.",
        epilog="The password is read from AVI_PASSWORD, --password-stdin or a prompt.")
    conn = parser.add_argument_group("connection")
    conn.add_argument("--controller", default=os.environ.get("AVI_CONTROLLER"), metavar="HOST",
                      help="Avi Controller address or name (or AVI_CONTROLLER).")
    conn.add_argument("--username", default=os.environ.get("AVI_USERNAME", "admin"),
                      help="API user (default: admin, or AVI_USERNAME).")
    conn.add_argument("--password-stdin", action="store_true",
                      help="Read the password from the first line of stdin.")
    conn.add_argument("--tenant", default=DEFAULT_TENANT, metavar="NAME",
                      help="Tenant to scan (default: {}).".format(DEFAULT_TENANT))
    conn.add_argument("--all-tenants", action="store_true", help="Scan every tenant.")
    conn.add_argument("--ca-cert", metavar="FILE",
                      help="CA certificate (file or directory) used to verify the controller's "
                           "TLS certificate. Default: the system trust store.")
    conn.add_argument("--insecure", action="store_true",
                      help="Do not verify the controller's TLS certificate (not recommended).")
    conn.add_argument("--api-version", metavar="VERSION",
                      help="X-Avi-Version to send (default: read from the controller).")
    conn.add_argument("--page-size", type=int, default=API_PAGE_SIZE, metavar="N",
                      help="Objects per API request (default: {}).".format(API_PAGE_SIZE))
    conn.add_argument("--timeout", type=int, default=API_TIMEOUT, metavar="SECONDS",
                      help="Per-request timeout (default: {}).".format(API_TIMEOUT))
    parser.add_argument(
        "--json-out",
        default=DEFAULT_REPORT,
        help="Detailed JSON report path (default: {}).".format(DEFAULT_REPORT),
    )
    parser.add_argument(
        "--log-file",
        default=DEFAULT_LOG,
        help="Error log path, created only if an error occurs (default: {}).".format(DEFAULT_LOG),
    )
    parser.add_argument(
        "--output", choices=("table", "summary", "json"), default="table",
        help="Console output: counts and the action table (default), counts only, or the "
             "JSON report on stdout.")
    parser.add_argument("--no-json", action="store_true", help="Do not write the JSON report.")
    parser.add_argument("--priority", type=priority_list, metavar="P1,P2",
                        help="Show only these priorities in the action table.")
    parser.add_argument("--only-tenant", metavar="NAME",
                        help="Show only the items of this tenant (useful after --all-tenants).")
    parser.add_argument("--all", action="store_true",
                        help="Show every row of the action table (default: the first {})."
                        .format(TABLE_ROWS))
    parser.add_argument("--detail", metavar="NAME",
                        help="List every object that depends on the certificate or PKIProfile "
                             "whose name or uuid contains NAME, then exit.")
    parser.add_argument("--csv", metavar="FILE",
                        help="Write one row per fix and affected object to FILE.")
    parser.add_argument("--from-json", metavar="FILE",
                        help="Render a saved JSON report instead of scanning.")
    parser.add_argument("--explain", action="store_true",
                        help="Print the background, what the scan checks and how to read the "
                             "result, then exit. Does not scan.")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.explain:
        print(explain_text())
        return 0
    if args.all_tenants and args.tenant != DEFAULT_TENANT:
        parser.error("use either --tenant NAME or --all-tenants")
    if args.ca_cert and args.insecure:
        parser.error("use either --ca-cert or --insecure")
    if args.page_size < 1:
        parser.error("--page-size must be at least 1")
    if not (args.from_json or args.controller):
        parser.error("give --controller HOST (or --from-json FILE)")
    setup_logging(args.log_file)

    if args.from_json:
        try:
            report = load_report(args.from_json)
        except (IOError, OSError, ValueError) as exc:
            print("ERROR: could not read report: {}".format(exc), file=sys.stderr)
            return 2
    else:
        api = None
        try:
            models, api, source = connect_models(args)
            report = scan(models, args.page_size, source)
        except Exception as exc:
            log.exception("scan failed")
            print("ERROR: scan failed: {} (see {})".format(exc, os.path.abspath(args.log_file)),
                  file=sys.stderr)
            return 2
        finally:
            if api:
                api.close()
    status = 1 if any(report["affected"][name] for name in CATEGORIES) else 0

    notes = sys.stderr if args.output == "json" else sys.stdout
    try:
        if args.detail:
            print_detail(report, args.detail)
        elif args.output == "json":
            json.dump(report_output(report), sys.stdout, indent=2, ensure_ascii=False)
            print()
        else:
            print_report(report)
            if args.output == "table":
                print_action_table(report, args.priority, args.only_tenant, args.all)
        if args.csv:
            write_csv(report, args.csv)
            print("\nCSV: {}".format(os.path.abspath(args.csv)), file=notes)
    except (IOError, OSError) as exc:
        log.exception("could not write %s", args.csv)
        print("ERROR: could not write CSV: {}".format(exc), file=sys.stderr)
        return 2

    if not args.from_json and not args.no_json:
        try:
            write_report(report, args.json_out)
        except (IOError, OSError) as exc:
            log.exception("could not write report %s", args.json_out)
            print("ERROR: could not write report: {}".format(exc), file=sys.stderr)
            return 2
        print("\nDetailed report: {}".format(os.path.abspath(args.json_out)), file=notes)
    return status


if __name__ == "__main__":
    sys.exit(main())
