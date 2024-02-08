'''
###
# Name: letsencrypt_mgmt_profile_infoblox_dns.py
# Version: 0.1.1
# License: MIT
#
# Description -
#     This is a python script used for automatically requesting and renewing certificates
#     from and via Let's Encrypt using DNS-01 Challenge.
#     To complete dns-01 challenge, a dns txt record needs to be added under the domain name
#     for which certificate has to be issued.
#     There are two functions provided add_dns_text_record(key_digest_64, txt_record_name, kwargs) and
#     remove_dns_text_record(key_digest_64, txt_record_name, kwargs) to add and remove dns txt record with
#     name txt_record_name and value key_digest_64 respectively.
#     Sample code to add and remove dns txt record in infoblox hosted domain is provided.
# Setup -
#     1. This content needs to be imported in the Avi Controller in the settings menu
#        at <<Templates - Security - Certificate Management>>.
#     2. Create at least following script params: user, password (sensitive).
#     3. Go to <<Templates - Security - SSL/TLS Certificates>>, click on <<Create>>
#        and then <<Application Certificate>>.
#     4. Specify a suitable name to identify this certificate in Avi Controller.
#        (Like sub.domain.tld RSA or sub.domain2.tld ECDSA)
#     5. Change <<Type>> to <<CSR>>
#     6. Set <<Common Name>> to the domain to which the certificate should be issued to
#        and select the "Certificate Management" as previously created.
#     7. Save and wait a few seconds for the certificate to be requested and imported.
#
# Note -
#     1. This script can issue RSA and ECDSA certificates, as specified when
#        creating an application certificate (CSR) via UI.
#     2. This REQUIRES a L7 Virtual Service with publicly available fqdn
#
# Parameters -
#     user            - Avi user name (Default: None)
#     password        - Password of the above user (Default: None)
#     tenant          - Avi tenant name (Default: is 'admin')
#     dryrun          - True/False. If True Let's Encrypt's staging server will be used. (Default: False)
#                       Main purpose is not to get ratelimited by LetsEncrypt during testing.
#     contact         - E-mail address sent to letsencrypt for account creation. (Default: None.)
#                       (set this only once until updated, otherwise an update request will be sent every time.)
#     directory_url   - Change ACME server, e.g. for using in-house ACME server. (Default: Let's Encrypt Production)
#     overwrite_vs    - Specify name or UUID of VirtualServer to be used for validation and httpPolicySet. (Default: Not set)
#                       Useful for scenarios where VS cannot be identified by FQDN/hostname, e.g. when it's only listening on IP.
#                       Important Note: Export+Import of Avi configuration CAUSES the UUID to change!
#     letsencrypt_key - Lets Encrypt Account Key (Default: None)
#     infoblox_username - Infoblox login user name (required)
#     infoblox_password - Infoblox login password (required)
#     infoblox_host     - Infoblox host ip (required)
#     infoblox_wapi_version - Infoblox WAPI version (Default: 2.0)
#     infoblox_dns_view - Infoblox DNS View (Default: default)
#     infoblox_verify_ssl - Infoblox API https server certificate verify(default: False)
#
# Useful links -
#     Ratelimiting - https://letsencrypt.org/docs/rate-limits/
#
# Source -
#     https://github.com/avinetworks/devops/blob/master/cert_mgmt/letsencrypt_mgmt_profile.py
#
# Authors/Credits -
#     acme-tiny, modified for Avi Controller <https://github.com/diafygi/acme-tiny>
#     acme-tiny-dns <https://github.com/Trim/acme-dns-tiny>
#     Nikhil Kumar Yadav <kumaryadavni@vmware.com>, Patrik Kernstock <pkernstock@vmware.com> for <https://github.com/avinetworks/devops/blob/master/cert_mgmt/letsencrypt_mgmt_profile.py>
#     Priya Koshta <pkoshta@vmware.com>
###
'''

import base64, binascii, hashlib, os, json, re, ssl, subprocess, time, urllib.parse
from urllib.request import urlopen, Request
from tempfile import NamedTemporaryFile
import requests
import copy
from avi.sdk.avi_api import ApiSession

VERSION = "0.1.1"

DEFAULT_CA = "https://acme-v02.api.letsencrypt.org" # DEPRECATED! USE DEFAULT_DIRECTORY_URL INSTEAD
DEFAULT_DIRECTORY_URL = "https://acme-v02.api.letsencrypt.org/directory"
DEFAULT_STAGING_DIRECTORY_URL = "https://acme-staging-v02.api.letsencrypt.org/directory"
ACCOUNT_KEY_PATH = "/tmp/letsencrypt.key"

IB_AUTHCOOKIE = None

def post_infoblox(**kwargs):
    global IB_AUTHCOOKIE
    if IB_AUTHCOOKIE:
        kwargs['cookies']=IB_AUTHCOOKIE
        kwargs.pop("auth",None)
    r = requests.post(**kwargs)
    if not IB_AUTHCOOKIE:
        #import pdb; pdb.set_trace();
        IB_AUTHCOOKIE = {'ibapauth':r.cookies['ibapauth']}
        print(IB_AUTHCOOKIE)
    return r

def logout_infoblox(**kwargs):
    global IB_AUTHCOOKIE
    r=post_infoblox(**kwargs)
    IB_AUTHCOOKIE=None
    return r


def get_crt(user, password, tenant, api_version, csr, CA=DEFAULT_CA, disable_check=False,
            overwrite_vs=None, directory_url=DEFAULT_DIRECTORY_URL, contact=None, debug=False, kwargs=None):
    directory, acct_headers, alg, jwk = None, None, None, None # global variables

    # helper functions - base64 encode for jose spec
    def _b64(b):
        return base64.urlsafe_b64encode(b).decode('utf8').replace("=", "")

    # helper function - run external commands
    def _cmd(cmd_list, stdin=None, cmd_input=None, err_msg="Command Line Error"):
        proc = subprocess.Popen(cmd_list, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(cmd_input)
        if proc.returncode != 0:
            raise IOError("{0}\n{1}".format(err_msg, err))
        return out

    # helper function - make request and automatically parse json response
    def _do_request(url, data=None, err_msg="Error", depth=0, verify=True):
        try:
            ctx = ssl.create_default_context()
            if not verify:
                # disable certificate verify
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            # open request.
            resp = urlopen(Request(url, data=data, headers={"Content-Type": "application/jose+json", "User-Agent": "acme-tiny"}), context=ctx)
            resp_data, code, headers = resp.read().decode("utf8"), resp.getcode(), resp.headers
        except IOError as e:
            resp_data = e.read().decode("utf8") if hasattr(e, "read") else str(e)
            code, headers = getattr(e, "code", None), {}
        try:
            resp_data = json.loads(resp_data) # try to parse json results
        except ValueError:
            pass # ignore json parsing errors
        if depth < 100 and code == 400 and resp_data['type'] == "urn:ietf:params:acme:error:badNonce":
            raise IndexError(resp_data) # allow 100 retrys for bad nonces
        if code not in [200, 201, 204]:
            raise ValueError("{0}:\nUrl: {1}\nData: {2}\nResponse Code: {3}\nResponse: {4}".format(err_msg, url, data, code, resp_data))
        return resp_data, code, headers

    # helper function - make signed requests
    def _send_signed_request(url, payload, err_msg, depth=0):
        payload64 = "" if payload is None else _b64(json.dumps(payload).encode('utf8'))
        new_nonce = _do_request(directory['newNonce'])[2]['Replay-Nonce']
        protected = {"url": url, "alg": alg, "nonce": new_nonce}
        protected.update({"jwk": jwk} if acct_headers is None else {"kid": acct_headers['Location']})
        protected64 = _b64(json.dumps(protected).encode('utf8'))
        protected_input = "{0}.{1}".format(protected64, payload64).encode('utf8')
        out = _cmd(["openssl", "dgst", "-sha256", "-sign", ACCOUNT_KEY_PATH], stdin=subprocess.PIPE, cmd_input=protected_input, err_msg="OpenSSL Error")
        data = json.dumps({"protected": protected64, "payload": payload64, "signature": _b64(out)})
        try:
            return _do_request(url, data=data.encode('utf8'), err_msg=err_msg, depth=depth)
        except IndexError: # retry bad nonces (they raise IndexError)
            return _send_signed_request(url, payload, err_msg, depth=(depth + 1))

    # helper function - poll until complete
    def _poll_until_not(url, pending_statuses, err_msg):
        result, t0 = None, time.time()
        while result is None or result['status'] in pending_statuses:
            assert (time.time() - t0 < 3600), "Polling timeout" # 1 hour timeout
            time.sleep(0 if result is None else 2)
            result, _, _ = _send_signed_request(url, None, err_msg)
        return result

    apiHost = os.environ.get('DOCKER_GATEWAY', 'localhost')
    if debug:
        print ("DEBUG: API Host is '{}'".format(apiHost))
    session = ApiSession(apiHost, user, password, tenant=tenant, api_version=api_version)

    def _do_request_avi(url, method, data=None, error_msg="Error"):
        if debug:
            print ("DEBUG: API request to url '{}'".format(url))
        rsp = None
        if method == "GET":
            rsp = session.get(url)
        elif method == "POST":
            rsp = session.post(url, data=data)
        elif method == "PATCH":
            rsp = session.patch(url, data=data)
        elif method == "PUT":
            rsp = session.put(url, data=data)
        elif method == "DELETE":
            rsp = session.delete(url)
        else:
            raise Exception("Unsupported API method")
        if rsp.status_code >= 300:
            err = error_msg + " url - {}. Method - {}. Response status - {}. Response - {}".format(url, method, rsp.status_code, rsp.json())
            raise Exception(err)
        return rsp

    def post_logout(infoblox_host, infoblox_user, infoblox_password, infoblox_wapi_version, infoblox_verify_ssl):
        try:
            logout_url = 'https://' + infoblox_host + \
                         '/wapi/v' + infoblox_wapi_version + '/logout'
            auth = (infoblox_user, infoblox_password)
            r = logout_infoblox(
                url=logout_url, auth=auth, verify=infoblox_verify_ssl, timeout=30)
            if r.status_code == 200:
                print("success req[%s]", logout_url)
                return
            r_json = r.json()
            if 'text' in r_json:
                print("error req[%s] rsp[%s]", logout_url, r_json['text'])
        except Exception as e:
            raise Exception("exception req[%s] rsp[%s]", logout_url, str(e))

    def add_dns_text_record(key_digest_64, txt_record_name, kwargs):
        # Create dns txt record with fqdn txt_record_name and value key_digest_64
        infoblox_host = kwargs.get('infoblox_host', None)
        infoblox_wapi_version = kwargs.get('infoblox_wapi_version', '2.0')
        infoblox_username = kwargs.get('infoblox_username', None)
        infoblox_password = kwargs.get('infoblox_password', None)
        infoblox_dns_view = kwargs.get('infoblox_dns_view', 'default')
        infoblox_verify_ssl = kwargs.get('infoblox_verify_ssl', False)
        txt_record_name = txt_record_name.rstrip(".")

        rest_url = 'https://' + infoblox_host + '/wapi/v' + \
                   infoblox_wapi_version + '/record:txt'
        payload = '{"text": "' + key_digest_64 + '","name": "' + \
                  txt_record_name + '","view": "' + \
                  infoblox_dns_view + '"}'
        try:
            r = post_infoblox(url=rest_url, auth=(infoblox_username, infoblox_password),
                              verify=infoblox_verify_ssl, data=payload, timeout=300)
            #post_logout(infoblox_host, infoblox_username, infoblox_password, infoblox_wapi_version, infoblox_verify_ssl)
            r_json = r.json()
            if r.status_code == 200 or r.status_code == 201:
                print("Added dns text record")
            else:
                if 'text' in r_json:
                    raise Exception("Return unexpected error code while adding dns txt record to vs {}", r.status_code)
                else:
                    r.raise_for_status()
        except Exception as e:
            raise Exception("Error adding dns txt record to vs {}", e)

    def remove_dns_text_record(key_digest_64, txt_record_name, kwargs):
        # Add your custom code here to remove dns txt record under your domain name with name
        # txt_record_name and value key_digest_64

        """ Implements IBA REST API call to delete IBA TXT record
                :param fqdn: hostname in FQDN
                """
        txt_record_name = txt_record_name.rstrip(".")
        infoblox_host = kwargs.get('infoblox_host', None)
        infoblox_wapi_version = kwargs.get('infoblox_wapi_version', '2.0')
        infoblox_username = kwargs.get('infoblox_username', None)
        infoblox_password = kwargs.get('infoblox_password', None)
        infoblox_dns_view = kwargs.get('infoblox_dns_view', 'default')
        infoblox_verify_ssl = kwargs.get('infoblox_verify_ssl', False)

        rest_url = 'https://' + infoblox_host + '/wapi/v' + infoblox_wapi_version + \
                   '/record:txt?name=' + txt_record_name + '&view=' + infoblox_dns_view
        try:
            r = requests.get(url=rest_url, auth=(infoblox_username, infoblox_password),
                             verify=infoblox_verify_ssl, timeout=300)
            post_logout(infoblox_host, infoblox_username, infoblox_password, infoblox_wapi_version, infoblox_verify_ssl)
            r_json = r.json()
            if r.status_code == 200:
                if len(r_json) > 0:
                    host_ref = r_json[0]['_ref']
                    if host_ref and re.match("record:txt\/[^:]+:([^\/]+)\/", host_ref).group(1) == txt_record_name:
                        rest_url = 'https://' + infoblox_host + '/wapi/v' + \
                                   infoblox_wapi_version + '/' + host_ref
                        r = requests.delete(url=rest_url, auth=(infoblox_username, infoblox_password),
                                            verify=infoblox_verify_ssl, timeout=300)
                        if r.status_code == 200:
                            return
                        else:
                            if 'text' in r_json:
                                raise Exception(r_json['text'])
                            else:
                                r.raise_for_status()
                    else:
                        raise Exception(
                            "Received unexpected host reference: " + host_ref)
                else:
                    raise Exception(
                        "No requested host found: " + txt_record_name)
                print("Deleted dns text record")
            else:
                if 'text' in r_json:
                    raise Exception(r_json['text'])
                else:
                    r.raise_for_status()
        except ValueError:
            raise Exception(r)
        except Exception as e:
            raise Exception("Error deleting dns txt record from vs {}",e)

    if os.path.exists(ACCOUNT_KEY_PATH):
        if debug:
            print ("DEBUG: Reusing account key.")
    else:
        print ("Account key not found. Generating account key...")
        out = _cmd(["openssl", "genrsa", "4096"], err_msg="OpenSSL Error")
        with open(ACCOUNT_KEY_PATH, 'w') as f:
            f.write(out.decode("utf-8"))

    # Check if we need to overwrite the VS UUID if it was specified
    # We request the info here once, instead in the loop for each SAN entry below.
    if overwrite_vs != None:
        if debug:
            print ("DEBUG: overwrite_vs is set to '{}'".format(overwrite_vs))
        if overwrite_vs.lower().startswith('virtualservice-'):
            search_term = "uuid={}".format(overwrite_vs.lower())
        else:
            search_term = "name={}".format(urllib.parse.quote(overwrite_vs, safe=''))

        overwrite_vs = _do_request_avi("virtualservice/?{}".format(search_term), "GET").json()
        if overwrite_vs['count'] == 0:
            raise Exception("Could not find a VS with search {}".format(search_term))

    # parse account key to get public key
    print ("Parsing account key...")
    out = _cmd(["openssl", "rsa", "-in", ACCOUNT_KEY_PATH, "-noout", "-text"], err_msg="OpenSSL Error")
    pub_pattern = r"modulus:[\s]+?00:([a-f0-9\:\s]+?)\npublicExponent: ([0-9]+)"
    pub_hex, pub_exp = re.search(pub_pattern, out.decode('utf8'), re.MULTILINE|re.DOTALL).groups()
    pub_exp = "{0:x}".format(int(pub_exp))
    pub_exp = "0{0}".format(pub_exp) if len(pub_exp) % 2 else pub_exp
    alg = "RS256"
    jwk = {
        "e": _b64(binascii.unhexlify(pub_exp.encode("utf-8"))),
        "kty": "RSA",
        "n": _b64(binascii.unhexlify(re.sub(r"(\s|:)", "", pub_hex).encode("utf-8"))),
    }
    accountkey_json = json.dumps(jwk, sort_keys=True, separators=(',', ':'))
    thumbprint = _b64(hashlib.sha256(accountkey_json.encode('utf8')).digest())

    # find domains
    print ("Parsing CSR...")
    out = _cmd(["openssl", "req", "-in", csr, "-noout", "-text"], err_msg="Error loading {0}".format(csr))
    domains = set([])
    common_name = re.search(r"Subject:.*? CN\s?=\s?([^\s,;/]+)", out.decode('utf8'))
    if common_name is not None:
        domains.add(common_name.group(1))
    subject_alt_names = re.search(r"X509v3 Subject Alternative Name: (?:critical)?\n +([^\n]+)\n", out.decode('utf8'), re.MULTILINE|re.DOTALL)
    if subject_alt_names is not None:
        for san in subject_alt_names.group(1).split(", "):
            if san.startswith("DNS:"):
                domains.add(san[4:])
    print ("Found domains: {0}".format(", ".join(domains)))

    # get the ACME directory of urls
    print ("Getting directory...")
    directory_url = CA + "/directory" if CA != DEFAULT_CA else directory_url # backwards compatibility with deprecated CA kwarg
    directory, _, _ = _do_request(directory_url, err_msg="Error getting directory")
    print ("Directory found!")

    # create account, update contact details (if any), and set the global key identifier
    print ("Registering account...")
    reg_payload = {"termsOfServiceAgreed": True}
    account, code, acct_headers = _send_signed_request(directory['newAccount'], reg_payload, "Error registering")
    print ("Registered!" if code == 201 else "Already registered!")
    if contact is not None:
        account, _, _ = _send_signed_request(acct_headers['Location'], {"contact": contact}, "Error updating contact details")
        print ("Updated contact details:\n{0}".format("\n".join(account['contact'])))

    # create a new order
    print ("Creating new order...")
    order_payload = {"identifiers": [{"type": "dns", "value": d} for d in domains]}
    order, _, order_headers = _send_signed_request(directory['newOrder'], order_payload, "Error creating new order")
    print ("Order created!")

    # get the authorizations that need to be completed
    for auth_url in order['authorizations']:
        if debug:
            print ("DEBUG: Authorization URL is: {}".format(auth_url))

        authorization, _, _ = _send_signed_request(auth_url, None, "Error getting challenges")
        domain = authorization['identifier']['value']
        print ("Verifying {0}...".format(domain))

        # find the dns-01 challenge and generate the txt_record_name and keydigest64 to be added to record
        challenge = [c for c in authorization['challenges'] if c['type'] == "dns-01"][0]
        token = re.sub(r"[^A-Za-z0-9_\-]", "_", challenge['token'])
        keyauthorization = "{0}.{1}".format(token, thumbprint)
        keydigest64 = _b64(hashlib.sha256(keyauthorization.encode("utf8")).digest())

        txt_record_name = "_acme-challenge.{0}.".format(domain)
        if debug:
            print ("DEBUG: Validation Record is : {}".format(txt_record_name))

        vhMode = False

        # Check if we need to overwrite VirtualService UUID to something specific
        if overwrite_vs == None:

            # Get VSVIPs/VSs, based on FQDN
            rsp = _do_request_avi("vsvip/?search=(fqdn,{})".format(domain), "GET").json()
            if debug:
                print ("DEBUG: Found {} matching VSVIP FQDNs".format(rsp["count"]))
            if rsp["count"] == 0:
                print ("Warning: Could not find a VSVIP with fqdn = {}".format(domain))
                # As a fallback we search for VirtualHosting entries with that domain
                vhMode = True
                search_term = "vh_domain_name.contains={}".format(domain)
            else:
                vsvip_uuid = rsp["results"][0]["uuid"]
                search_term = "vsvip_ref={}".format(vsvip_uuid)

            rsp = _do_request_avi("virtualservice/?{}".format(search_term), "GET").json()
            if debug:
                print ("DEBUG: Found {} matching VSs".format(rsp["count"]))
            if rsp['count'] == 0:
                raise Exception("Could not find a VS with fqdn = {}".format(domain))

            vs_uuid = rsp["results"][0]["uuid"]

        else:
            # Overwriting VS UUID to what user specified.
            # ALL SANs of the CSR must be reachable on the specified VS to succeed.
            rsp = overwrite_vs
            vs_uuid = rsp["results"][0]["uuid"]
            print ("Note: Overwriting VS UUID to {}".format(vs_uuid))

        print ("Found VS {} with fqdn {}".format(vs_uuid, domain))

        # Let's check if VS is enabled, otherwise challenge can never successfully complete.
        if not rsp["results"][0]["enabled"]:
            raise Exception("VS with fqdn {} is not enabled.".format(domain))

        # Special handling for virtualHosting: if child, get services from parent.
        if vhMode and rsp["results"][0]["type"] == "VS_TYPE_VH_CHILD":
            # vh_parent_vs_ref is schema of https://avi.domain.tld/api/virtualservice/virtualservice-UUID, hence picking the last part
            vs_uuid_parent = rsp["results"][0]["vh_parent_vs_ref"].split("/")[-1]
            vhRsp = _do_request_avi("virtualservice/?uuid={}".format(vs_uuid_parent), "GET").json()
            if debug:
                print ("DEBUG: Parent VS of Child-VS is {} and found {} matches".format(vs_uuid_parent, vhRsp['count']))
            if vhRsp['count'] == 0:
                raise Exception("Could not find parent VS {} of child VS UUID = {}".format(vs_uuid_parent, vs_uuid))

            # we just copy it over. more transparent for further logic.
            rsp["results"][0]["services"] = vhRsp["results"][0]["services"]

        try:
            print("Install DNS TXT resource for domain: %s", domain)
            add_dns_text_record(keydigest64, txt_record_name, kwargs)

            print ("Challenge completed, notifying LetsEncrypt")
            # say the challenge is done
            _send_signed_request(challenge['url'], {}, "Error submitting challenges: {0}".format(domain))
            authorization = _poll_until_not(auth_url, ["pending"], "Error checking challenge status for {0}".format(domain))
            if authorization['status'] != "valid":
                raise ValueError("Challenge did not pass for {0}: {1}".format(domain, authorization))
            print ("Challenge passed")

        finally:
            print ("Cleaning up...")

            # Remove dns txt record
            remove_dns_text_record(keydigest64, txt_record_name, kwargs)

    print ("{0} verified!".format(domain))

    # finalize the order with the csr
    print ("Signing certificate...")
    csr_der = _cmd(["openssl", "req", "-in", csr, "-outform", "DER"], err_msg="DER Export Error")
    _send_signed_request(order['finalize'], {"csr": _b64(csr_der)}, "Error finalizing order")

    # poll the order to monitor when it's done
    order = _poll_until_not(order_headers['Location'], ["pending", "processing"], "Error checking order status")
    if order['status'] != "valid":
        raise ValueError("Order failed: {0}".format(order))

    # download the certificate
    certificate_pem, _, _ = _send_signed_request(order['certificate'], None, "Certificate download failed")
    print ("Certificate signed!")

    return certificate_pem

def certificate_request(csr, common_name, kwargs):
    user = kwargs.get('user', None)
    tenant = kwargs.get('tenant', None)
    password = kwargs.get('password', None)
    dry_run = kwargs.get('dryrun', "false")
    contact = kwargs.get('contact', None)
    api_version = kwargs.get('api_version', '22.1.3')
    disable_check = kwargs.get('disable_check', "false")
    debug = kwargs.get('debug', "false")
    directory_url = kwargs.get('directory_url', None)
    overwrite_vs = kwargs.get('overwrite_vs', None)
    letsencrypt_key = kwargs.get('letsencrypt_key', None)

    print ("Running version {}".format(VERSION))

    if debug.lower() == "true":
        debug = True
        print ("Debug enabled.")
    else:
        debug = False

    if dry_run.lower() == "true":
        dry_run = True
    else:
        dry_run = False
    print ("dry_run is: {}".format(str(dry_run)))

    if disable_check.lower() == "true":
        disable_check = True
    else:
        disable_check = False
    print ("disable_check is: {}".format(str(disable_check)))

    if directory_url == None:
        if dry_run:
            directory_url = DEFAULT_STAGING_DIRECTORY_URL
        else:
            directory_url = DEFAULT_DIRECTORY_URL
    print ("directory_url is {}".format(directory_url))

    # If overwrite_vs is specified but empty, set it to None.
    if overwrite_vs == "":
        overwrite_vs = None

    if tenant == None:
        print ("Using default tenant. You might want to define a specific tenant.".format(tenant))

    if contact != None and "@" in contact:
        contact = [ "mailto:{}".format(contact) ] # contact must be array as of ACME RFC
        print ("Contact set to: {}".format(contact))

    if letsencrypt_key != None:
        with open(ACCOUNT_KEY_PATH, 'w') as f:
            f.write(letsencrypt_key)

    # Create CSR temp file.
    csr_temp_file = NamedTemporaryFile(mode='w',delete=False)
    csr_temp_file.close()

    with open(csr_temp_file.name, 'w') as f:
        f.write(csr)

    signed_crt = None
    try:
        signed_crt = get_crt(user, password, tenant, api_version, csr_temp_file.name,
                                disable_check=disable_check, overwrite_vs=overwrite_vs,
                                directory_url=directory_url, contact=contact, debug=debug, kwargs=kwargs)
    finally:
        os.remove(csr_temp_file.name)

    print (signed_crt)
    return signed_crt
