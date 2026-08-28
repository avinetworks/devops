#!/usr/bin/python

import os
import sys
import requests
try:
    from requests.exceptions import JSONDecodeError
except ImportError:
    from simplejson.errors import JSONDecodeError
from tempfile import NamedTemporaryFile

PARAMS_ERROR=1
REMOTE_API_ERROR=2
REQUESTS_ERROR=3
TEMP_FILE_ERROR=4

def get_vault_token_with_approle(vault_addr, role_name, role_id, secret_id, vault_namespace=None, api_timeout=20):
    """
    Authenticate with Vault using AppRole and retrieve a token.
    """
    url = f'{vault_addr}/v1/auth/{role_name}/login'
    headers = {}
    if vault_namespace:
        headers['X-Vault-Namespace'] = vault_namespace

    data = {
        'role_id': role_id,
        'secret_id': secret_id
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=api_timeout)
        if r.status_code >= 400:
            try:
                r_errors = ' | '.join(r.json()['errors'])
            except (JSONDecodeError, KeyError):
                r_errors = r.text
            sys.stderr.write(f'Error during AppRole authentication: {r_errors}')
            sys.exit(REMOTE_API_ERROR)

        return r.json()['auth']['client_token']
    except Exception as e:
        sys.stderr.write(f'Error during AppRole authentication request: {str(e)}')
        sys.exit(REQUESTS_ERROR)

def certificate_request(csr, common_name, args_dict):
    if 'vault_addr' not in args_dict:
        sys.stderr.write('Vault API Root Address (vault_addr) not specified')
        sys.exit(PARAMS_ERROR)

    if 'vault_token' not in args_dict and ('role_id' not in args_dict or 'secret_id' not in args_dict or 'role_name' not in args_dict):
        sys.stderr.write('Vault Token (vault_token), AppRole credentials (role_name, role_id, and secret_id), or role_name not specified')
        sys.exit(PARAMS_ERROR)

    if 'vault_path' not in args_dict:
        sys.stderr.write('Vault Sign API Path (vault_path) not specified')
        sys.exit(PARAMS_ERROR)

    vault_addr = args_dict['vault_addr']
    vault_token = args_dict.get('vault_token', None)
    vault_path = args_dict['vault_path']
    if vault_path.startswith('/'):
        vault_path = vault_path[1:]
    vault_namespace = args_dict.get('vault_namespace', None)
    verify_endpoint = args_dict.get('verify_endpoint', None)
    api_timeout = args_dict.get('api_timeout', 20)

    if 'role_name' in args_dict and 'role_id' in args_dict and 'secret_id' in args_dict:
        role_name = args_dict['role_name']
        role_id = args_dict['role_id']
        secret_id = args_dict['secret_id']
        vault_token = get_vault_token_with_approle(
            vault_addr, role_name, role_id, secret_id, vault_namespace, api_timeout
        )

    headers = {'X-Vault-Token': vault_token}
    if vault_namespace:
        headers['X-Vault-Namespace'] = vault_namespace

    url = f'{vault_addr}/{vault_path}'
    api_data = {
        'common_name': common_name,
        'csr': csr
    }

    ca_file = False

    try:
        if verify_endpoint:
            try:
                with NamedTemporaryFile(delete=False) as tf:
                    ca_file = tf.name
                    sys.stdout.write(f'CA certificate written to {ca_file}')
                    tf.write(bytes(verify_endpoint, 'utf-8'))

            except Exception as e:
                sys.stderr.write(str(e))
                sys.exit(TEMP_FILE_ERROR)

        requests.packages.urllib3.disable_warnings()
        r = requests.post(url, headers=headers, json=api_data,
                        verify=ca_file, timeout=api_timeout)

        if r.status_code >= 400:
            try:
                r_errors = ' | '.join(r.json()['errors'])
            except (JSONDecodeError, KeyError):
                r_errors = r.text

            sys.stderr.write(f'Error from Vault API: {r_errors}')
            sys.exit(REMOTE_API_ERROR)

        try:
            r_data = r.json()
            certificate = r_data['data']['certificate']
        except (JSONDecodeError, KeyError):
            r_data = f'{r.text[:50]} +...' if len(r.text) > 50 else r.text
            sys.stderr.write(f'Vault API returned incorrect response: {r_data}')
            sys.exit(REMOTE_API_ERROR)

    except Exception as e:
        sys.stderr.write(f'Error during request: {str(e)}')
        sys.exit(REQUESTS_ERROR)

    finally:
        if ca_file and os.path.exists(ca_file):
            os.remove(ca_file)

    return certificate
