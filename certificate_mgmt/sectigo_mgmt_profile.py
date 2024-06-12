'''
This is to be used as a certificate management profile in Avi Networks. This will integrate with the public CA Sectigo.
This is the username/password version.
Parameters -
    user                - Sectigo user name.
    password            - Sectigo password.
    orgid               - Sectigo org id.
    customeruri         - Sectigo customer URI.
    certtype            - Certificate type. Default type 3.
    term                - Certificate term. Default 365.
    comments            - Comments for order.
'''

import json, time, requests, re, logging, os, sys, subprocess
from tempfile import NamedTemporaryFile
from avi.infrastructure.avi_logging import get_root_logger

log = get_root_logger(__name__, '/opt/avi/log/sectigo.log', logging.DEBUG)

def get_crt(csr, user, password, orgid, certtype, term, comments, customeruri, csrfile):

    # helper function - run external commands
    def _cmd(cmd_list, stdin=None, cmd_input=None, err_msg="Command Line Error"):
        proc = subprocess.Popen(cmd_list, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(cmd_input)
        if proc.returncode != 0:
            raise IOError("{0}\n{1}".format(err_msg, err))
        return out

    def _generate_certificate(csr, user, password, orgid, certtype, term, comments, customeruri, sannames):
        payload = {
            "orgId": orgid,
            "subjAltNames": sannames,
            "csr": csr,
            "certType": certtype,
            "term": term,
            "comments": comments
            }
        headers = {
            "Content-Type": "application/json",
            "login": user,
            "password": password,
            "customerUri": customeruri
            }
        log.info("Generating certificate...!")
        r = requests.post ("https://cert-manager.com/api/ssl/v1/enroll/", json=payload, headers=headers)
        if r.status_code >= 300:
            err_msg = "Failed to generate certificate. Response status - {}, text - {}".format(r.status_code, r.text)
            raise Exception(err_msg)
        log.info("Certificate Generated..." + r.text)
        return json.loads(r.text)

    def _get_certificate(user, password, customeruri, sslid, formattype):
        headers = {
            "login": user,
            "password": password,
            "customerUri": customeruri
            }
        log.info("Downloading certificate")
        r = requests.get ("https://cert-manager.com/api/ssl/v1/collect/" + str(sslid) + "/" + formattype, headers=headers)
        if r.status_code >= 300:
            err_msg = "Failed to download certificate. Response status - {}, text - {}".format(r.status_code, r.text)
            raise Exception(err_msg)
        log.info("Certificate downloaded..." + r.text)
        return r.text

    # find domains
    log.info("Parsing CSR...")
    out = _cmd(["openssl", "req", "-in", csrfile, "-noout", "-text"], err_msg="Error loading {0}".format(csrfile))
    domains = set([])
    common_name = re.search(r"Subject:.*? CN\s?=\s?([^\s,;/]+)", out.decode('utf8'))
    if common_name is not None:
        domains.add(common_name.group(1))
    subject_alt_names = re.search(r"X509v3 Subject Alternative Name: (?:critical)?\n +([^\n]+)\n", out.decode('utf8'), re.MULTILINE|re.DOTALL)
    if subject_alt_names is not None:
        for san in subject_alt_names.group(1).split(", "):
            if san.startswith("DNS:"):
                domains.add(san[4:])
    domains = ",".join(domains)
    log.info("Found domains: {0}".format(domains))

    crt_id = _generate_certificate(csr, user, password, orgid, certtype, term, comments, customeruri, domains)
    time.sleep(15)
    cert = _get_certificate(user, password, customeruri, crt_id["sslId"], "x509CO")
    while "BEGIN CERTIFICATE" not in cert:
        log.info("Not found yet" + cert)
        time.sleep(15)
        cert = get_certificate(user, password, customeruri, crt_id["sslId"], "x509CO")
    return cert

def certificate_request(csr, common_name, kwargs):
    user = kwargs.get("user", None)
    password = kwargs.get("password", None)
    customeruri = kwargs.get("customeruri", None)
    orgid = kwargs.get("orgid", None)
    certtype = kwargs.get("certtype", "3")
    term = kwargs.get("term", "365")
    comments = kwargs.get("comments", "")

    csr_temp_file = NamedTemporaryFile(mode='w',delete=False)
    csr_temp_file.close()
    with open(csr_temp_file.name, 'w') as f:
        f.write(csr)

    if not user:
        raise Exception("Missing user argument.")
    if not password:
        raise Exception("Missing password argument.")
    if not orgid:
        raise Exception("Missing orgid argument.")
    if not customeruri:
        raise Exception("Missing customeruri argument.")

    exception_occured = None
    signed_crt = None
    try:
        signed_crt = get_crt(csr, user, password, orgid, certtype, term, comments, customeruri, csr_temp_file.name)
    except:
        exception_occured = sys.exc_info()
    finally:
        os.remove(csr_temp_file.name)

    if not signed_crt:
        log.error(exception_occured)
        raise exception_occured
    log.info(signed_crt)
    return signed_crt