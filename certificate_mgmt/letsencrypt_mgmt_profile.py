'''
###
# Name: letsencrypt_mgmt_profile.py
# Version: 0.9.7
# License: MIT
#
# Description -
#     This is a python script used for automatically requesting and renewing certificates
#     from and via Let's Encrypt.
#
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
#     2. This REQUIRES a L7 Virtual Service (HTTP/S) due to the requirement
#        of HTTP-Policy-Sets.
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
#
# Useful links -
#     Ratelimiting - https://letsencrypt.org/docs/rate-limits/
#
# Source -
#     https://github.com/avinetworks/devops/blob/master/cert_mgmt/letsencrypt_mgmt_profile.py
#
# Authors/Credits -
#     acme-tiny, modified for Avi Controller <https://github.com/diafygi/acme-tiny>
#     Nikhil Kumar Yadav <kumaryadavni@vmware.com>
#     Patrik Kernstock <pkernstock@vmware.com>
###
'''

import base64, binascii, hashlib, os, json, re, ssl, subprocess, time, urllib.parse
from urllib.request import urlopen, Request
from tempfile import NamedTemporaryFile

from avi.sdk.avi_api import ApiSession

VERSION = "0.9.7"

DEFAULT_CA = "https://acme-v02.api.letsencrypt.org" # DEPRECATED! USE DEFAULT_DIRECTORY_URL INSTEAD
DEFAULT_DIRECTORY_URL = "https://acme-v02.api.letsencrypt.org/directory"
DEFAULT_STAGING_DIRECTORY_URL = "https://acme-staging-v02.api.letsencrypt.org/directory"
ACCOUNT_KEY_PATH = "/tmp/letsencrypt.key"

def get_crt(user, password, tenant, api_version, csr, CA=DEFAULT_CA, disable_check=False,
            overwrite_vs=None, directory_url=DEFAULT_DIRECTORY_URL, contact=None, debug=False):
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

        # find the http-01 challenge and write the challenge file
        challenge = [c for c in authorization['challenges'] if c['type'] == "http-01"][0]
        token = re.sub(r"[^A-Za-z0-9_\-]", "_", challenge['token'])
        keyauthorization = "{0}.{1}".format(token, thumbprint)

        wellknown_url = "http://{0}/.well-known/acme-challenge/{1}".format(domain, token)
        if debug:
            print ("DEBUG: Validation URL is: {}".format(wellknown_url))

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

        # Check if the vs is serving on port 80
        serving_on_port_80 = False
        service_on_port_80_data = None
        for service in rsp["results"][0]["services"]:
            if service["port"] == 80 and not service["enable_ssl"]:
                serving_on_port_80 = True
                if debug:
                    print ("DEBUG: VS serving on port 80")
                break

        # Update VS
        httpPolicyName = (domain + "-LetsEncryptHTTPpolicy")
        # Check if HTTP policy exists.
        # Can happen in rare cases, when e.g. script fails or removal failed for whatever reasons.
        # To prevent this from failing forever, we clean it up at this stage.
        hpRsp = _do_request_avi("httppolicyset/?name={}".format(httpPolicyName), "GET").json()
        if hpRsp['count'] > 0:
            hp_uuid = hpRsp['results'][0]['uuid']
            print("Stranded httpPolicySet {} found. Deleting...".format(hp_uuid))
            patch_data = {
                "delete": {
                    "http_policies": [{
                        "http_policy_set_ref": "/api/httppolicyset/{}".format(hp_uuid),
                        "index": 1000001
                    }]
                }
            }

            # Remove httpPolicySet from VS
            if vhMode:  # if VH, we set the rule on the parent. Without SNI (so HTTP) it will go to the parent.
                _do_request_avi("virtualservice/{}".format(vs_uuid_parent), "PATCH", patch_data)
                print("Removed httpPolicySet from parent-VS {}".format(vs_uuid_parent))
            else:
                _do_request_avi("virtualservice/{}".format(vs_uuid), "PATCH", patch_data)
                print("Removed httpPolicySet from VS {}".format(vs_uuid))

            _do_request_avi("httppolicyset/{}".format(hp_uuid), "DELETE")

        # Create HTTP policy
        httppolicy_data = {
            "name": httpPolicyName,
            "http_security_policy": {
                "rules": [{
                    "name": "Rule 1",
                    "index": 1,
                    "enable": True,
                    "match": {
                        "path": {
                            "match_criteria": "CONTAINS",
                            "match_case": "SENSITIVE",
                            "match_str": [
                                ".well-known/acme-challenge/{}".format(token)
                            ]
                        }
                    },
                    "action": {
                        "action": "HTTP_SECURITY_ACTION_SEND_RESPONSE",
                        "status_code": "HTTP_LOCAL_RESPONSE_STATUS_CODE_200",
                        "file": {
                            "content_type": "text/plain",
                            "file_content": keyauthorization
                        }
                    }
                }]
            },
            "is_internal_policy": False
        }

        httppolicy_uuid = None
        try:
            # Create httpPolicySet
            rsp = _do_request_avi("httppolicyset", "POST", data=httppolicy_data).json()
            httppolicy_uuid = rsp["uuid"]
            print ("Created httpPolicy with uuid {}".format(httppolicy_uuid))

            patch_data = {
                "add" : {
                    "http_policies": [{
                        "http_policy_set_ref": "/api/httppolicyset/{}".format(httppolicy_uuid),
                        "index": 1000001
                    }]
                }
            }
            if not serving_on_port_80:
                # Add port to virtualservice
                print ("Adding port 80 to VS")
                service_on_port_80_data = {
                    "enable_http2": False,
                    "enable_ssl": False,
                    "port": 80,
                    "port_range_end": 80
                }
                patch_data["add"]["services"] = [service_on_port_80_data]

            # Adding httpPolicySet to VS
            if vhMode: # if VH, we set the rule on the parent. Without SNI (so HTTP) it will go to the parent.
                _do_request_avi("virtualservice/{}".format(vs_uuid_parent), "PATCH", patch_data)
                print ("Added httpPolicySet to parent-VS {}".format(vs_uuid_parent))
            else:
                _do_request_avi("virtualservice/{}".format(vs_uuid), "PATCH", patch_data)
                print ("Added httpPolicySet to VS {}".format(vs_uuid))

            # check that the file is in place
            if not disable_check:
                print ("Validating token from Avi Controller...")
                try:
                    maxVerifyAttempts = 5 # maximal amount of verification attempts
                    # retrying logic. Otherwise race-condition can occurr between avi controller pushing config and the token validation request
                    for verifyAttempt in range(maxVerifyAttempts):
                        reqToken = _do_request(wellknown_url, verify=False)
                        if reqToken[0] != keyauthorization:
                            print ("Internal token validation failed, {0} of {1} attempts. Retrying in 2 seconds."
                                        .format((verifyAttempt + 1), maxVerifyAttempts))
                            time.sleep(2)
                        else:
                            break
                    else:
                        raise Exception("All {2} internal token verifications failed. Got '{0}' but expected '{1}'."
                                            .format(reqToken[0], keyauthorization, maxVerifyAttempts))
                except Exception as e:
                    raise ValueError("Wrote file, but Avi couldn't verify token at {0}. Exception: {1}".format(wellknown_url, str(e)))
            else:
                print ("Waiting 5 seconds before letting LetsEncrypt validating the challenge as validation disabled. Give controller time to push configs.")
                time.sleep(5) # wait 5 secs if not validating, due to above mentioned race condition

            print ("Challenge completed, notifying LetsEncrypt")
            # say the challenge is done
            _send_signed_request(challenge['url'], {}, "Error submitting challenges: {0}".format(domain))
            authorization = _poll_until_not(auth_url, ["pending"], "Error checking challenge status for {0}".format(domain))
            if authorization['status'] != "valid":
                raise ValueError("Challenge did not pass for {0}: {1}".format(domain, authorization))
            print ("Challenge passed")

        finally:
            print ("Cleaning up...")
            # Update the vs
            if httppolicy_uuid == None:
                print ("Error: Failed removing httpPolicy as UUID not defined.")
            else:
                patch_data = {
                    "delete" : {
                        "http_policies": [{
                            "http_policy_set_ref": "/api/httppolicyset/{}".format(httppolicy_uuid),
                            "index": 1000001
                        }]
                    }
                }
                if not serving_on_port_80:
                    patch_data["delete"]["services"] = [service_on_port_80_data]

                # Remove httpPolicySet from VS
                if vhMode: # if VH, we set the rule on the parent. Without SNI (so HTTP) it will go to the parent.
                    _do_request_avi("virtualservice/{}".format(vs_uuid_parent), "PATCH", patch_data)
                    print ("Removed httpPolicySet from parent-VS {}".format(vs_uuid_parent))
                else:
                    _do_request_avi("virtualservice/{}".format(vs_uuid), "PATCH", patch_data)
                    print ("Removed httpPolicySet from VS {}".format(vs_uuid))

                # Remove httpPolicySet
                _do_request_avi("httppolicyset/{}".format(httppolicy_uuid), "DELETE")
                print ("Deleted httpPolicySet")

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
    password = kwargs.get('password', None)
    tenant = kwargs.get('tenant', None)
    dry_run = kwargs.get('dryrun', "false")
    contact = kwargs.get('contact', None)
    api_version = kwargs.get('api_version', '20.1.1')
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
                                directory_url=directory_url, contact=contact, debug=debug)
    finally:
        os.remove(csr_temp_file.name)

    print (signed_crt)
    return signed_crt
