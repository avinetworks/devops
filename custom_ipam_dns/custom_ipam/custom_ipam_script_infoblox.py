
"""
This script allows the user to communicate with Infoblox IPAM provider.

Required Functions
------------------
1. TestLogin: Function to verify provider credentials, used in the UI during IPAM profile configuration.
2. GetAvailableNetworksAndSubnets: Function to return available networks/subnets from the provider.
3. GetIpamRecord: Function to return the info of the given IPAM record.
4. CreateIpamRecord: Function to create an IPAM record with the provider.
5. DeleteIpamRecord: Funtion to delete a given IPAM record from the provider.
6. UpdateIpamRecord: Function to update a given IPAM record.

Required Exception Classes
--------------------------
1. CustomIpamAuthenticationErrorException: Raised when authentication fails.
2. CustomIpamRecordNotFoundException: Raised when given record not found.
3. CustomIpamNoFreeIpException: Raised when no free IP available in the given subnets/networks.
4. CustomIpamNotImplementedException: Raised when the functionality is not implemented.
5. CustomIpamGeneralException: Raised for other types of exceptions.

Optional
--------
1. _verify_required_fields_in_auth_params: Internal function used to verify that all required auth parameters are provided.
2. _check_and_raise_auth_error: Internal function used to raise an exception if authentication fails.
3. _get_api_paginated: Internal function used to return paginated response for a given url.
"""


# Script supports all standard python libraries and modules that are part of the Avi controller.
import requests
import time
import logging
import copy
import json
from bs4 import BeautifulSoup

class CustomIpamAuthenticationErrorException(Exception):
    """
    Raised when authentication fails.
    """
    pass

class CustomIpamRecordNotFoundException(Exception):
    """
    Raised when given record not found.
    """
    pass

class CustomIpamNoFreeIpException(Exception):
    """
    Raised when no free IP available in the given subnets/networks.
    """
    pass

class CustomIpamNotImplementedException(Exception):
    """
    Raised when the functionality is not implemented.
    """
    pass

class CustomIpamGeneralException(Exception):
    """
    Raised for other types of exceptions.
    """
    pass


def _verify_required_fields_in_auth_params(auth_params):
    missing_req_params = []
    if 'server' not in auth_params and 'server6' not in auth_params:
        missing_req_params.append('server and server6')
    if 'username' not in auth_params:
        missing_req_params.append('username')
    if 'password' not in auth_params:
        missing_req_params.append('password')
    if 'wapi_version' not in auth_params:
        missing_req_params.append('wapi_version')
    if missing_req_params:
        missing_req_params = ', '.join(missing_req_params)
        raise CustomIpamGeneralException("all credentials are not provided, missing parameters[%s]" % missing_req_params)


def _check_and_raise_auth_error(response):
    if response.status_code in [401, 403]:
        text = BeautifulSoup(response.text, 'html.parser').text
        raise CustomIpamAuthenticationErrorException(response.reason, response.status_code, response.url, text)


def _get_api_paginated(auth_params, dest_url, dest_url6, data_key, results_per_page, api_timeout, ip_type):

    """
    Function used to return paginated response for a given dest_url. 
    This function is called from GetAvailableNetworksAndSubnets function.
    Args
    ----
        auth_params: (dict of str: str)
            Parameters required for authentication.
        dest_url: (str)
            IPv4 based URL for which pagination is desired.
        dest_url6: (str)
            IPv6 based URL for which pagination is desired.
        data_key: (str)
            Dictionary key to look for in the results.
        results_per_page: (str)
            self explanatory
        api_timeout : (str)
            self explanatory
        ip_type: (str)
            IP type supported by the network/subnet used in the dest_url. Allowed values: V4_ONLY, V6_ONLY.
    Returns
    -------
        data_vals: (list of dict of str : str)
            each dict has 5 keys: network, v4_subnet, v6_subnet, v4_available_ip_count, v6_available_ip_count
            v4_available_ip_count and v6_available_ip_count are optional, currenty this function returns the first 3 keys. returning counts is TBD.
    Raises
    ------
        CustomIpamGeneralException: if the given request fails.
    """

    logger = logging.getLogger(auth_params.get('logger_name', ''))
    data_vals = []
    network_view = auth_params.get('network_view', 'default')
    if 'server' in auth_params:
        page_url = dest_url + '&_paging=1&_max_results=%d&_return_as_object=1' % results_per_page
    if 'server6' in auth_params:
        page_url6 = dest_url6 + '&_paging=1&_max_results=%d&_return_as_object=1' % results_per_page
    
    if 'server6' in auth_params:
        r6 = requests.get(
            url=page_url6, auth=(auth_params['username'], auth_params['password']), verify=False, timeout=30)
        logger.info("F[_get_api_paginated] req[%s] status_code[%s]" % (page_url6, r6.status_code))
        _check_and_raise_auth_error(r6)
        if r6.status_code == 200:
            resp = r6.json()
            for unit in resp['result']:
                if data_key not in unit:
                    continue
                sub_value = unit[data_key]
                # Since infoblox doesn't return network values, dummy value can be given to nw_id 
                # from here or from UI during IPAM profile configuration.
                nw_id = 'infoblox--' + network_view + '--'
                v4_subnet = v6_subnet = None
                if ip_type == 'V4_ONLY':
                    v4_subnet = sub_value
                    nw_id += v4_subnet.split('/')[0] + '-' + str(v4_subnet.split('/')[1])
                elif ip_type == 'V6_ONLY':
                    v6_subnet = sub_value
                    nw_id += v6_subnet.split('/')[0] + '-' + str(v6_subnet.split('/')[1])
                data_vals.append({'network': nw_id, 'v4_subnet': v4_subnet, 'v6_subnet': v6_subnet})

            next_page_id = resp.get('next_page_id', '')
            page_start_time = time.time()
            elapsed_time = 0
            while next_page_id and elapsed_time < api_timeout:
                page_url6 = dest_url6 + '&_page_id=%s' % next_page_id
                r6 = requests.get(
                    url=page_url6, auth=(auth_params['username'], auth_params['password']), verify=False, timeout=30)
                logger.info("F[_get_api_paginated] req[%s] status_code[%s]" % (page_url6, r6.status_code))
                _check_and_raise_auth_error(r6)
                if r6.status_code != 200:
                    break
                resp = r6.json()
                for unit in resp['result']:
                    if data_key not in unit:
                        continue
                    sub_value = unit[data_key]
                    nw_id = 'infoblox--' + network_view + '--'
                    v4_subnet = v6_subnet = None
                    if ip_type == 'V4_ONLY':
                        v4_subnet = sub_value
                        nw_id += v4_subnet.split('/')[0] + '-' + str(v4_subnet.split('/')[1])
                    elif ip_type == 'V6_ONLY':
                        v6_subnet = sub_value
                        nw_id += v6_subnet.split('/')[0] + '-' + str(v6_subnet.split('/')[1])
                    data_vals.append({'network': nw_id, 'v4_subnet': v4_subnet, 'v6_subnet': v6_subnet})

                next_page_id = resp.get('next_page_id', '')
                elapsed_time = int(time.time() - page_start_time)
            return data_vals
        elif 'server' in auth_params:
            r = requests.get(
                url=page_url, auth=(auth_params['username'], auth_params['password']), verify=False, timeout=30)
            logger.info("F[_get_api_paginated] req[%s] status_code[%s]" % (page_url, r.status_code))
            _check_and_raise_auth_error(r)
            if r.status_code == 200:
                resp = r.json()
                for unit in resp['result']:
                    if data_key not in unit:
                        continue
                    sub_value = unit[data_key]
                    # Since infoblox doesn't return network values, dummy value can be given to nw_id 
                    # from here or from UI during IPAM profile configuration.
                    nw_id = 'infoblox--' + network_view + '--'
                    v4_subnet = v6_subnet = None
                    if ip_type == 'V4_ONLY':
                        v4_subnet = sub_value
                        nw_id += v4_subnet.split('/')[0] + '-' + str(v4_subnet.split('/')[1])
                    elif ip_type == 'V6_ONLY':
                        v6_subnet = sub_value
                        nw_id += v6_subnet.split('/')[0] + '-' + str(v6_subnet.split('/')[1])
                    data_vals.append({'network': nw_id, 'v4_subnet': v4_subnet, 'v6_subnet': v6_subnet})

                next_page_id = resp.get('next_page_id', '')
                page_start_time = time.time()
                elapsed_time = 0
                while next_page_id and elapsed_time < api_timeout:
                    page_url = dest_url + '&_page_id=%s' % next_page_id
                    r = requests.get(
                        url=page_url, auth=(auth_params['username'], auth_params['password']), verify=False, timeout=30)
                    logger.info("F[_get_api_paginated] req[%s] status_code[%s]" % (page_url, r.status_code))
                    _check_and_raise_auth_error(r)
                    if r.status_code != 200:
                        break
                    resp = r.json()
                    for unit in resp['result']:
                        if data_key not in unit:
                            continue
                        sub_value = unit[data_key]
                        nw_id = 'infoblox--' + network_view + '--'
                        v4_subnet = v6_subnet = None
                        if ip_type == 'V4_ONLY':
                            v4_subnet = sub_value
                            nw_id += v4_subnet.split('/')[0] + '-' + str(v4_subnet.split('/')[1])
                        elif ip_type == 'V6_ONLY':
                            v6_subnet = sub_value
                            nw_id += v6_subnet.split('/')[0] + '-' + str(v6_subnet.split('/')[1])
                        data_vals.append({'network': nw_id, 'v4_subnet': v4_subnet, 'v6_subnet': v6_subnet})

                    next_page_id = resp.get('next_page_id', '')
                    elapsed_time = int(time.time() - page_start_time)
                return data_vals
            err_msg = r.status_code + ' : '  + r.text
            logger.error("F[GetAvailableNetworksAndSubnets] req[%s] ip_type[%s] err[%s]" % (page_url, ip_type, err_msg))
            raise CustomIpamGeneralException("F[GetAvailableNetworksAndSubnets] req[%s] ip_type[%s] err[%s]" % (page_url, ip_type, err_msg))
        else:
            err_msg = r6.status_code + ' : '  + r6.text
            logger.error("F[GetAvailableNetworksAndSubnets] req[%s] ip_type[%s] err[%s]" % (page_url6, ip_type, err_msg))
            raise CustomIpamGeneralException("F[GetAvailableNetworksAndSubnets] req[%s] ip_type[%s] err[%s]" % (page_url6, ip_type, err_msg))
    elif 'server' in auth_params:
        r = requests.get(
            url=page_url, auth=(auth_params['username'], auth_params['password']), verify=False, timeout=30)
        logger.info("F[_get_api_paginated] req[%s] status_code[%s]" % (page_url, r.status_code))
        _check_and_raise_auth_error(r)
        if r.status_code == 200:
            resp = r.json()
            for unit in resp['result']:
                if data_key not in unit:
                    continue
                sub_value = unit[data_key]
                # Since infoblox doesn't return network values, dummy value can be given to nw_id 
                # from here or from UI during IPAM profile configuration.
                nw_id = 'infoblox--' + network_view + '--'
                v4_subnet = v6_subnet = None
                if ip_type == 'V4_ONLY':
                    v4_subnet = sub_value
                    nw_id += v4_subnet.split('/')[0] + '-' + str(v4_subnet.split('/')[1])
                elif ip_type == 'V6_ONLY':
                    v6_subnet = sub_value
                    nw_id += v6_subnet.split('/')[0] + '-' + str(v6_subnet.split('/')[1])
                data_vals.append({'network': nw_id, 'v4_subnet': v4_subnet, 'v6_subnet': v6_subnet})

            next_page_id = resp.get('next_page_id', '')
            page_start_time = time.time()
            elapsed_time = 0
            while next_page_id and elapsed_time < api_timeout:
                page_url = dest_url + '&_page_id=%s' % next_page_id
                r = requests.get(
                    url=page_url, auth=(auth_params['username'], auth_params['password']), verify=False, timeout=30)
                logger.info("F[_get_api_paginated] req[%s] status_code[%s]" % (page_url, r.status_code))
                _check_and_raise_auth_error(r)
                if r.status_code != 200:
                    break
                resp = r.json()
                for unit in resp['result']:
                    if data_key not in unit:
                        continue
                    sub_value = unit[data_key]
                    nw_id = 'infoblox--' + network_view + '--'
                    v4_subnet = v6_subnet = None
                    if ip_type == 'V4_ONLY':
                        v4_subnet = sub_value
                        nw_id += v4_subnet.split('/')[0] + '-' + str(v4_subnet.split('/')[1])
                    elif ip_type == 'V6_ONLY':
                        v6_subnet = sub_value
                        nw_id += v6_subnet.split('/')[0] + '-' + str(v6_subnet.split('/')[1])
                    data_vals.append({'network': nw_id, 'v4_subnet': v4_subnet, 'v6_subnet': v6_subnet})

                next_page_id = resp.get('next_page_id', '')
                elapsed_time = int(time.time() - page_start_time)
            return data_vals
        err_msg = r.status_code + ' : '  + r.text
        logger.error("F[GetAvailableNetworksAndSubnets] req[%s] ip_type[%s] err[%s]" % (page_url, ip_type, err_msg))
        raise CustomIpamGeneralException("F[GetAvailableNetworksAndSubnets] req[%s] ip_type[%s] err[%s]" % (page_url, ip_type, err_msg))


def GetIpamRecord(auth_params, record_info):
    """
    Function to return the info of the given IPAM record.
    Args
    ----
        auth_params: (dict of str: str)
            Parameters required for authentication.
        record_info: (dict of str: str)
            id (str): uuid of vsvip.
            fqdns (list of str): list of fqdn from dns_info in vsvip. 
    Returns
    -------
        alloc_info(dict of str: str): 
            Dictionary of following keys
            v4_ip (str): IPv4 of the record
            v4_subnet (str): IPv4 subnet
            v6_ip (str): IPv6 of the record
            v6_subnet (str): IPv6 subnet
            network (str): network id/name
    Raises
    ------
        CustomIpamNotImplementedException: if this function is not implemented.
        CustomIpamGeneralException: if the api request fails.
    """

    raise CustomIpamNotImplementedException("F[GetIpamRecord] not implemented in the script!")


def TestLogin(auth_params):
    """
    Function to validate user credentials. This function is called from IPAM profile 
    configuration UI page.
    Args
    ----
        auth_params: (dict of str: str)
            Parameters required for authentication. These are script parameters provided while 
            creating a Custom IPAM profile.
            Eg: auth_params can have following keys
            server: Server IPv4 address of the custom IPAM provider
            server6: Server IPv6 address of the custom IPAM provider
            username: self explanatory
            password: self explanatory 
            logger_name: logger name   
    Returns
    -------
        Return True on success    
    Raises
    ------
        CustomIpamNotImplementedException: if this function is not implemented.
        CustomIpamAuthenticationErrorException: if authentication fails.
    """
    
    _verify_required_fields_in_auth_params(auth_params)
    logger = logging.getLogger(auth_params.get('logger_name', ''))
    tmp_auth_params = copy.deepcopy(auth_params)
    tmp_auth_params['password'] = '<sensitive>'
    logger.info("Inside F[TestLogin] auth_params[%s]", tmp_auth_params)
    server = auth_params.get('server', None)
    server6 = auth_params.get('server6', None)
    username = auth_params.get('username', None)
    password = auth_params.get('password', None)
    wapi_version = auth_params.get('wapi_version', None)
  
    if not (server or server6) or not username or not password or not wapi_version:
        raise CustomIpamGeneralException("F[TestLogin] all credentials are not provided")
    schema_url = 'https://' + server + '/wapi/' + wapi_version + '/?_schema' if server else None
    schema_url6 = 'https://[' + server6 + ']/wapi/' + wapi_version + '/?_schema' if server6 else None
    auth = (username, password)
    try:
        r = None
        r6 = None
        if server:
            r = requests.get(url=schema_url, auth=auth, verify=False, timeout=30)
            logger.info("F[TestLogin] req[%s] status_code[%s]" % (schema_url, r.status_code))
        if server6:
            r6 = requests.get(url=schema_url6, auth=auth, verify=False, timeout=30)
            logger.info("F[TestLogin] req[%s] status_code[%s]" % (schema_url6, r6.status_code))
        if (not r or r.status_code == 200) and (not r6 or r6.status_code == 200):
            return True
        else:
            if server:
                _check_and_raise_auth_error(r)
            if server6:
                _check_and_raise_auth_error(r6)
    except CustomIpamAuthenticationErrorException as e:
        raise
    except Exception as e:
        raise CustomIpamGeneralException("F[TestLogin] login failed reason[%s]" % str(e))
        

def GetAvailableNetworksAndSubnets(auth_params, ip_type):
    """ 
    Function to retrieve networks/subnets from the provider.
    Called from the IPAM profile configuration to populate usable subnets on the UI.
    Note: Subnets are represented in CIDR format.
    Args
    ----
        auth_params: (dict of str: str)
            Parameters required for authentication.
        ip_type: (str)
            IP type supported by the networks/subnets. Allowed values: V4_ONLY, V6_ONLY and V4_V6.
    Returns
    -------
        subnet_list: (list of dict of str : str)
            network (str): network id/name
            v4_subnet (str): V4 subnet
            v6_subnet (str): V6 subnet
            v4_available_ip_count (str): V4 free ips count of the network/v4_subnet
            v6_available_ip_count (str): V6 free ips count of the network/v6_subnet
        each dict has 5 keys: network, v4_subnet, v6_subnet, v4_available_ip_count, v6_available_ip_count
        v4_available_ip_count and v6_available_ip_count are optional, currenty this function returns the first 3 keys. returning counts is TBD.
    Raises
    ------
        None
    """

    _verify_required_fields_in_auth_params(auth_params)
    logger = logging.getLogger(auth_params.get('logger_name', ''))
    tmp_auth_params = copy.deepcopy(auth_params)
    tmp_auth_params['password'] = '<sensitive>'
    logger.info("Inside F[GetAvailableNetworksAndSubnets] auth_params[%s] ip_type[%s]", tmp_auth_params, ip_type)
    network_view = auth_params.get('network_view', 'default')
    if 'server' in auth_params:
        base_url = 'https://' + auth_params['server'] + '/wapi/' + auth_params['wapi_version']
    if 'server6' in auth_params:
        base_url6 = 'https://[' + auth_params['server6'] + ']/wapi/' + auth_params['wapi_version']
    data_key = 'network'
    results_per_page = 1000
    api_timeout = 600

    subnet_list = []
    if ip_type in ['V4_ONLY', 'V4_V6']:
        rest_url = base_url + '/network?network_view=' + network_view if 'server' in auth_params else None
        rest_url6 = base_url6 + '/network?network_view=' + network_view if 'server6' in auth_params else None
        v4_subnets = _get_api_paginated(auth_params, rest_url, rest_url6, data_key, results_per_page, api_timeout, 'V4_ONLY')
        subnet_list.extend(v4_subnets)
    if ip_type in ['V6_ONLY', 'V4_V6']:
        rest_url = base_url + '/ipv6network?network_view=' + network_view if 'server' in auth_params else None
        rest_url6 = base_url6 + '/ipv6network?network_view=' + network_view if 'server6' in auth_params else None
        v6_subnets = _get_api_paginated(auth_params, rest_url, rest_url6, data_key, results_per_page, api_timeout, 'V6_ONLY')
        subnet_list.extend(v6_subnets)
    return subnet_list


def CreateIpamRecord(auth_params, record_info):
    """
    Implements a Custom Rest API to create an IPAM record.
    Args
    ----
        auth_params: (dict of str: str)
            Parameters required for authentication.
        record_info: (dict of str: str)
            New record information with following keys.
            id (str): uuid of vsvip.
            fqdns (list of str): list of fqdn from dns_info in vsvip.
            preferred_ip (str): the vsvip IPv4 if it's already configured by the user.
            preferred_ip6 (str): the vsvip IPv6 if it's already configured by the user.
            allocation_type (str): IP allocation type. Allowed values: V4_ONLY, V6_ONLY and V4_V6.
            nw_and_subnet_list (list of tuples : str): List of networks and subnets to use for new IPAM
            record IP allocation. Each tuple has 3 values (network, v4_subnet, v6_subnet).
    Returns
    -------
        alloc_info(dict of str: str): 
            Dictionary of following keys
            v4_ip (str): allocated IPv4
            v4_subnet (str): subnet used for IPv4 allocation.
            v6_ip (str): allocated IPv6
            v6_subnet (str): subnet used for IPv6 allocation.
            network (str): network used for IPv4/IPv6 allocation.
    Raises
    ------
        CustomIpamNoFreeIpException: if no free ip available.
        CustomIpamGeneralException: if create record fails for any other reason.
    """

    _verify_required_fields_in_auth_params(auth_params)
    logger = logging.getLogger(auth_params.get('logger_name', ''))
    tmp_auth_params = copy.deepcopy(auth_params)
    tmp_auth_params['password'] = '<sensitive>'
    logger.info("Inside F[CreateIpamRecord] auth_params[%s] record_info[%s]", tmp_auth_params, record_info)
    network_view = auth_params.get('network_view', 'default')
    dns_view = auth_params.get('dns_view', None)
    id = record_info.get('id', None)
    fqdns = record_info.get('fqdns', None)
    allocation_type = record_info.get('allocation_type', None)
    nw_and_subnet_list = record_info.get('nw_and_subnet_list', [])
    preferred_ip = record_info.get('preferred_ip', None)
    preferred_ip6 = record_info.get('preferred_ip6', None)
    name = id
    
    if 'server' in auth_params:
        base_uri = 'https://' + auth_params['server'] + '/wapi/' + auth_params['wapi_version']
        rest_url = base_uri + '/record:host?_return_fields=ipv4addrs,ipv6addrs'
    if 'server6' in auth_params:
        base_uri6 = 'https://[' + auth_params['server6'] + ']/wapi/' + auth_params['wapi_version']
        rest_url6 = base_uri6 + '/record:host?_return_fields=ipv4addrs,ipv6addrs'

    # Step 1: If the preferred_ip/preferred_ip6 is set, call specific rest URL according to the allocation_type.
    # <TODO>

    # Step 2: If the nw_and_subnet_list is empty call GetAvailableNetworksAndSubnets() to use any available
    # subnets or networks from the Custom IPAM provider.
    v4_subnet_list = v6_subnet_list = None
    if len(nw_and_subnet_list) == 0:
        if allocation_type == 'V4_V6':
            raise CustomIpamGeneralException("F[CreateIpamRecord] No V4+V6 networks found in Infoblox IPAM provider!")
        if allocation_type == 'V4_ONLY':
            nw_and_subnet_list = v4_subnet_list = GetAvailableNetworksAndSubnets(auth_params, 'V4_ONLY')
        if allocation_type == 'V6_ONLY':
            nw_and_subnet_list = v6_subnet_list = GetAvailableNetworksAndSubnets(auth_params, 'V6_ONLY')
        if len(nw_and_subnet_list) == 0:
            logger.error("F[CreateIpamRecord] No discovered networks and subnets found in Infoblox IPAM provider!")
            raise CustomIpamGeneralException("F[CreateIpamRecord] No discovered networks and subnets found in Infoblox IPAM provider!")

    # Step 3: Based on the allocation_type, build payload data and call specific rest URL.
    err_msgs = []
    if allocation_type == 'V4_V6':
        for sub in nw_and_subnet_list:
            v4_subnet = sub[1]
            v6_subnet = sub[2]
            if v4_subnet and v6_subnet:
                ipv4addrs = [{"ipv4addr": 'func:nextavailableip:' + v4_subnet + ',' + network_view}]
                ipv6addrs = [{"ipv6addr": 'func:nextavailableip:' + v6_subnet + ',' + network_view}]
                payload = json.dumps({'name': name, 'view': dns_view, 'configure_for_dns':False, 'ipv4addrs': ipv4addrs, 'ipv6addrs': ipv6addrs})
            else:
                continue
            #HA code for ipv6 and ipv4 addresses
            if 'server6' in auth_params:
                r6 = requests.post(url=rest_url6, auth=(auth_params['username'], auth_params['password']),
                            verify=False, data=payload)
                logger.info("F[CreateIpamRecord] req[%s %s] status_code[%s]" % (rest_url6, payload, r6.status_code))
                _check_and_raise_auth_error(r6)
                if r6.status_code in [200, 201]:
                    r6_json = r6.json()
                    alloc_info = {}
                    if 'ipv4addrs' in r6_json and r6_json['ipv4addrs'][0]['ipv4addr']:
                        alloc_info['v4_ip'] = r6_json['ipv4addrs'][0]['ipv4addr']
                        alloc_info['v4_subnet'] = v4_subnet
                    if 'ipv6addrs' in r6_json and r6_json['ipv6addrs'][0]['ipv6addr']:
                        alloc_info['v6_ip'] = r6_json['ipv6addrs'][0]['ipv6addr']
                        alloc_info['v6_subnet'] = v6_subnet
                    return alloc_info
                elif 'server' in  auth_params:
                    r = requests.post(url=rest_url, auth=(auth_params['username'], auth_params['password']),
                                    verify=False, data=payload)
                    logger.info("F[CreateIpamRecord] req[%s %s] status_code[%s]" % (rest_url, payload, r.status_code))
                    _check_and_raise_auth_error(r)
                    if r.status_code in [200,201]:
                        r_json = r.json()
                        alloc_info = {}
                        if 'ipv4addrs' in r_json and r_json['ipv4addrs'][0]['ipv4addr']:
                            alloc_info['v4_ip'] = r_json['ipv4addrs'][0]['ipv4addr']
                            alloc_info['v4_subnet'] = v4_subnet
                        if 'ipv6addrs' in r_json and r_json['ipv6addrs'][0]['ipv6addr']:
                            alloc_info['v6_ip'] = r_json['ipv6addrs'][0]['ipv6addr']
                            alloc_info['v6_subnet'] = v6_subnet
                        return alloc_info
                    else:
                        emsg = "req[%s %s], rsp[%s, %s]" % (rest_url, payload, r.status_code, r.text)
                        err_msgs.append(emsg)
                        continue
                else:
                    emsg = "req[%s %s], rsp[%s, %s]" % (rest_url6, payload, r6.status_code, r6.text)
                    err_msgs.append(emsg)
                    continue
            elif 'server' in auth_params:
                r = requests.post(url=rest_url, auth=(auth_params['username'], auth_params['password']),
                            verify=False, data=payload)
                logger.info("F[CreateIpamRecord] req[%s %s] status_code[%s]" % (rest_url, payload, r.status_code))
                _check_and_raise_auth_error(r)
                if r.status_code in [200,201]:
                    r_json = r.json()
                    alloc_info = {}
                    if 'ipv4addrs' in r_json and r_json['ipv4addrs'][0]['ipv4addr']:
                        alloc_info['v4_ip'] = r_json['ipv4addrs'][0]['ipv4addr']
                        alloc_info['v4_subnet'] = v4_subnet
                    if 'ipv6addrs' in r_json and r_json['ipv6addrs'][0]['ipv6addr']:
                        alloc_info['v6_ip'] = r_json['ipv6addrs'][0]['ipv6addr']
                        alloc_info['v6_subnet'] = v6_subnet
                    return alloc_info
                else:
                    emsg = "req[%s %s], rsp[%s, %s]" % (rest_url, payload, r.status_code, r.text)
                    err_msgs.append(emsg)
                    continue
        if len(err_msgs) == len(nw_and_subnet_list) and all('Cannot find 1 available IP address' in e for e in err_msgs):
            logger.error("F[CreateIpamRecord] No free available IP reason[%s]" % (err_msgs))
            raise CustomIpamNoFreeIpException("F[CreateIpamRecord] No free available IP reason[%s]" % (err_msgs))
        logger.error("F[CreateIpamRecord] Error creating host record[%s] reason[%s]" % (name, err_msgs))
        raise CustomIpamGeneralException("F[CreateIpamRecord] Error creating host record[%s] reason[%s]" % (name, err_msgs))

    else:
        for sub in nw_and_subnet_list:
            if v4_subnet_list or v6_subnet_list:
                v4_subnet = sub.get('v4_subnet','')
                v6_subnet = sub.get('v6_subnet','')
            else:
                v4_subnet = sub[1]
                v6_subnet = sub[2]
            if allocation_type in 'V4_ONLY' and v4_subnet:
                ipv4addrs = [{"ipv4addr": 'func:nextavailableip:' + v4_subnet + ',' + network_view}]
                payload = json.dumps({'name': name, 'view': dns_view, 'configure_for_dns':False, 'ipv4addrs': ipv4addrs})
            elif allocation_type in 'V6_ONLY' and v6_subnet:
                ipv6addrs = [{"ipv6addr": 'func:nextavailableip:' + v6_subnet + ',' + network_view}]
                payload = json.dumps({'name': name, 'view': dns_view, 'configure_for_dns':False, 'ipv6addrs': ipv6addrs})
            else:
                continue        
            #HA code for ipv6 and ipv4 addresses
            if 'server6' in auth_params:
                r6 = requests.post(url=rest_url6, auth=(auth_params['username'], auth_params['password']),
                            verify=False, data=payload)
                logger.info("F[CreateIpamRecord] req[%s %s] status_code[%s]" % (rest_url6, payload, r6.status_code))
                _check_and_raise_auth_error(r6)
                if r6.status_code in [200, 201]:
                    r6_json = r6.json()
                    alloc_info = {}
                    if 'ipv4addrs' in r6_json and r6_json['ipv4addrs'][0]['ipv4addr']:
                        alloc_info['v4_ip'] = r6_json['ipv4addrs'][0]['ipv4addr']
                        alloc_info['v4_subnet'] = v4_subnet
                    if 'ipv6addrs' in r6_json and r6_json['ipv6addrs'][0]['ipv6addr']:
                        alloc_info['v6_ip'] = r6_json['ipv6addrs'][0]['ipv6addr']
                        alloc_info['v6_subnet'] = v6_subnet
                    return alloc_info
                elif 'server' in  auth_params:
                    r = requests.post(url=rest_url, auth=(auth_params['username'], auth_params['password']),
                                    verify=False, data=payload)
                    logger.info("F[CreateIpamRecord] req[%s %s] status_code[%s]" % (rest_url, payload, r.status_code))
                    _check_and_raise_auth_error(r)
                    if r.status_code in [200,201]:
                        r_json = r.json()
                        alloc_info = {}
                        if 'ipv4addrs' in r_json and r_json['ipv4addrs'][0]['ipv4addr']:
                            alloc_info['v4_ip'] = r_json['ipv4addrs'][0]['ipv4addr']
                            alloc_info['v4_subnet'] = v4_subnet
                        if 'ipv6addrs' in r_json and r_json['ipv6addrs'][0]['ipv6addr']:
                            alloc_info['v6_ip'] = r_json['ipv6addrs'][0]['ipv6addr']
                            alloc_info['v6_subnet'] = v6_subnet
                        return alloc_info
                    else:
                        emsg = "req[%s %s], rsp[%s, %s]" % (rest_url, payload, r.status_code, r.text)
                        err_msgs.append(emsg)
                        continue
                else:
                    emsg = "req[%s %s], rsp[%s, %s]" % (rest_url6, payload, r6.status_code, r6.text)
                    err_msgs.append(emsg)
                    continue
            elif 'server' in auth_params:
                r = requests.post(url=rest_url, auth=(auth_params['username'], auth_params['password']),
                            verify=False, data=payload)
                logger.info("F[CreateIpamRecord] req[%s %s] status_code[%s]" % (rest_url, payload, r.status_code))
                _check_and_raise_auth_error(r)
                if r.status_code in [200,201]:
                    r_json = r.json()
                    alloc_info = {}
                    if 'ipv4addrs' in r_json and r_json['ipv4addrs'][0]['ipv4addr']:
                        alloc_info['v4_ip'] = r_json['ipv4addrs'][0]['ipv4addr']
                        alloc_info['v4_subnet'] = v4_subnet
                    if 'ipv6addrs' in r_json and r_json['ipv6addrs'][0]['ipv6addr']:
                        alloc_info['v6_ip'] = r_json['ipv6addrs'][0]['ipv6addr']
                        alloc_info['v6_subnet'] = v6_subnet
                    return alloc_info
                else:
                    emsg = "req[%s %s], rsp[%s, %s]" % (rest_url, payload, r.status_code, r.text)
                    err_msgs.append(emsg)
                    continue
        if len(err_msgs) == len(nw_and_subnet_list) and all('Cannot find 1 available IP address' in e for e in err_msgs):
            logger.error("F[CreateIpamRecord] No free available IP reason[%s]" % (err_msgs))
            raise CustomIpamNoFreeIpException("F[CreateIpamRecord] No free available IP reason[%s]" % (err_msgs))
        logger.error("F[CreateIpamRecord] Error creating host record[%s] reason[%s]" % (name, err_msgs))
        raise CustomIpamGeneralException("F[CreateIpamRecord] Error creating host record[%s] reason[%s]" % (name, err_msgs))
        

def DeleteIpamRecord(auth_params, record_info):
    """
    Implements a Custom Rest API to delete an IPAM record.
    Args
    ----
        auth_params: (dict of str: str)
            Parameters required for authentication.
        record_info: (dict of str: str)
            Record to be deleted. Has following keys.
            id (str): uuid of vsvip.
            fqdns (list of str): list of fqdn from dns_info in vsvip.
    Returns
    -------
        True on successfully deleting the record.
    Raises
    ------
        CustomIpamAuthenticationErrorException: if authentication fails.
        CustomIpamRecordNotFoundException: if the given record not found
        CustomIpamGeneralException: if delete record request fails.
    """

    _verify_required_fields_in_auth_params(auth_params)
    logger = logging.getLogger(auth_params.get('logger_name', ''))
    tmp_auth_params = copy.deepcopy(auth_params)
    tmp_auth_params['password'] = '<sensitive>'
    logger.info("Inside F[DeleteIpamRecord] auth_params[%s] record_info[%s]", tmp_auth_params, record_info)
    id = record_info.get('id', None)
    fqdns = record_info.get('fqdns', None)
    name = id

    # Step 1: Get the reference of the given IPAM record
    if 'server' in auth_params:
        rest_url = 'https://' + auth_params['server'] + '/wapi/' + auth_params['wapi_version'] + \
                '/record:host?name=' + name
    if 'server6' in auth_params:
        rest_url6 = 'https://[' + auth_params['server6'] + ']/wapi/' + auth_params['wapi_version'] + \
                '/record:host?name=' + name
    try:
        #HA code for ipv6 and ipv4 addresses
        if 'server6' in auth_params:
            r6 = requests.get(url=rest_url6, auth=(auth_params['username'], auth_params['password']), 
                            verify=False, timeout=30)
            logger.info("F[DeleteIpamRecord] req[%s] status_code[%s]" % (rest_url6, r6.status_code))
            _check_and_raise_auth_error(r6)
            r6_json = r6.json()
            host_ref = None
            err_msg = "F[DeleteIpamRecord] Record[%s] not found!" % name
            if r6.status_code == 200:
                host_ref = r6_json[0]['_ref'] if len(r6_json) > 0 and r6_json[0]['_ref'] else None
                if not host_ref:
                    logger.error(err_msg)
                    raise CustomIpamRecordNotFoundException(err_msg)
                # Step 2: Delete the record
                url6 = 'https://[' + auth_params['server6'] + ']/wapi/' + \
                    auth_params['wapi_version'] + '/' + host_ref
                r6 = requests.delete(url=url6, auth=(
                    auth_params['username'], auth_params['password']), verify=False)
                logger.info("F[DeleteIpamRecord] req[%s] status_code[%s]" % (url6, r6.status_code))
                _check_and_raise_auth_error(r6)
                r6_json = r6.json()
                if r6.status_code == 200:
                    return True
                else:
                    if 'text' in r6_json:
                        err_msg += r6.status_code + " : " + BeautifulSoup(r6.text, 'html.parser').text
                    logger.error(err_msg)
                    raise CustomIpamRecordNotFoundException(err_msg)
            elif 'server' in  auth_params:
                r = requests.get(url=rest_url, auth=(auth_params['username'], auth_params['password']), 
                            verify=False, timeout=30)
                logger.info("F[DeleteIpamRecord] req[%s] status_code[%s]" % (rest_url, r.status_code))
                _check_and_raise_auth_error(r)
                r_json = r.json()
                host_ref = None
                err_msg = "F[DeleteIpamRecord] Record[%s] not found!" % name
                if r.status_code == 200:
                    host_ref = r_json[0]['_ref'] if len(r_json) > 0 and r_json[0]['_ref'] else None
                    if not host_ref:
                        logger.error(err_msg)
                        raise CustomIpamRecordNotFoundException(err_msg)
                    # Step 2: Delete the record
                    url = 'https://' + auth_params['server'] + '/wapi/' + \
                        auth_params['wapi_version'] + '/' + host_ref
                    r = requests.delete(url=url, auth=(
                        auth_params['username'], auth_params['password']), verify=False)
                    logger.info("F[DeleteIpamRecord] req[%s] status_code[%s]" % (url, r.status_code))
                    _check_and_raise_auth_error(r)
                    r_json = r.json()
                    if r.status_code == 200:
                        return True
                if 'text' in r_json:
                    err_msg += r.status_code + " : " + BeautifulSoup(r.text, 'html.parser').text
                logger.error(err_msg)
                raise CustomIpamRecordNotFoundException(err_msg)
            else:
                if 'text' in r6_json:
                    err_msg += r6.status_code + " : " + BeautifulSoup(r6.text, 'html.parser').text
                logger.error(err_msg)
                raise CustomIpamRecordNotFoundException(err_msg)
        elif 'server' in auth_params:
            r = requests.get(url=rest_url, auth=(auth_params['username'], auth_params['password']), 
                            verify=False, timeout=30)
            logger.info("F[DeleteIpamRecord] req[%s] status_code[%s]" % (rest_url, r.status_code))
            _check_and_raise_auth_error(r)
            r_json = r.json()
            host_ref = None
            err_msg = "F[DeleteIpamRecord] Record[%s] not found!" % name
            if r.status_code == 200:
                host_ref = r_json[0]['_ref'] if len(r_json) > 0 and r_json[0]['_ref'] else None
                if not host_ref:
                    logger.error(err_msg)
                    raise CustomIpamRecordNotFoundException(err_msg)
                # Step 2: Delete the record
                url = 'https://' + auth_params['server'] + '/wapi/' + \
                    auth_params['wapi_version'] + '/' + host_ref
                r = requests.delete(url=url, auth=(
                    auth_params['username'], auth_params['password']), verify=False)
                logger.info("F[DeleteIpamRecord] req[%s] status_code[%s]" % (url, r.status_code))
                _check_and_raise_auth_error(r)
                r_json = r.json()
                if r.status_code == 200:
                    return True
            if 'text' in r_json:
                err_msg += r.status_code + " : " + BeautifulSoup(r.text, 'html.parser').text
            logger.error(err_msg)
            raise CustomIpamRecordNotFoundException(err_msg)
    except CustomIpamAuthenticationErrorException as e:
        raise
    except CustomIpamRecordNotFoundException as e:
        raise
    except Exception as e:
        logger.error("F[DeleteIpamRecord] Error deleting the record[%s] reason[%s]" % (name, str(e)))
        raise CustomIpamGeneralException("F[DeleteIpamRecord] Error deleting the record[%s] reason[%s]" % (name, str(e)))


def UpdateIpamRecord(auth_params, new_record_info, old_record_info):
    """
    Function to handle update IPAM record requests. Eg: Change of allocation_type from 
    V4_ONLY to V6_ONLY.
    Args
    ----
        auth_params: (dict of str: str)
            Parameters required for authentication.
        new_record_info: (dict of str: str)
            New record information with following keys.
            id (str): uuid of vsvip.
            fqdns (list of str): list of fqdn from dns_info in vsvip.
            preferred_ip (str): the vsvip IPv4 if it's already configured by the user.
            preferred_ip6 (str): the vsvip IPv6 if it's already configured by the user.
            allocation_type (str): IP allocation type. Allowed values: V4_ONLY, V6_ONLY and V4_V6.
            nw_and_subnet_list (list of tuples : str): List of networks and subnets to use for an 
                IPAM record IP allocation. Each tuple has 3 values (network, v4_subnet, v6_subnet)
        old_record_info: (dict of str: str)
            Old record information with following keys.
            id (str): uuid of vsvip.
            fqdns (list of str): list of fqdn from dns_info in vsvip of an old record.
            preferred_ip (str): old record's preferred IPv4.
            preferred_ip6 (str): old record's preferred IPv6.
            allocation_type (str): old record's IP allocation type. Allowed values: V4_ONLY, V6_ONLY and V4_V6.
            nw_and_subnet_list (list of tuples : str): List of networks and subnets used for an old IPAM
                record IP allocation. Each tuple has 3 values (network, v4_subnet, v6_subnet)
    Returns
    -------
        alloc_info(dict of str: str): 
            Dictionary of following keys
            v4_ip (str): allocated IPv4
            v4_subnet (str): subnet used for IPv4 allocation.
            v6_ip (str): allocated IPv6
            v6_subnet (str): subnet used for IPv6 allocation.
            network (str): network used for IPv4/IPv6 allocation.
    Raises
    ------
        CustomIpamNotImplementedException: if this function or specific update requests not implemented.
        CustomIpamAuthenticationErrorException: if authentication fails.
        CustomIpamRecordNotFoundException: if the given record not found
        CustomIpamGeneralException: if the api request fails for any other reason.
    """

    _verify_required_fields_in_auth_params(auth_params)
    logger = logging.getLogger(auth_params.get('logger_name', ''))
    tmp_auth_params = copy.deepcopy(auth_params)
    tmp_auth_params['password'] = '<sensitive>'
    logger.info("Inside F[UpdateIpamRecord] auth_params[%s] new_record_info[%s] old_record_info[%s]", tmp_auth_params, new_record_info, old_record_info)
    id = new_record_info.get('id', None)
    new_fqdns = new_record_info.get('fqdns', None)
    old_fqdns = old_record_info.get('fqdns', None)
    preferred_ip = new_record_info.get('preferred_ip', None)
    preferred_ip6 = new_record_info.get('preferred_ip6', None)
    new_nw_and_subnet_list = new_record_info.get('nw_and_subnet_list', [])
    old_nw_and_subnet_list = old_record_info.get('nw_and_subnet_list', [])
    new_allocation_type = new_record_info.get('allocation_type', None)
    old_allocation_type = old_record_info.get('allocation_type', None)
    network_view = auth_params.get('network_view', 'default')
    dns_view = auth_params.get('dns_view', None)
    
    # fqdn change: <TODO>
    # record update with preferred ipv4/ipv6: <TODO>
    # nw_and_subnet_list change: <TODO>
    # nw_and_subnet_list and allocation_type change: <TODO>

    # Note: Only allocation type change is handled here as an example update request. This is an in-place update.
    # Hence raise CustomIpamNotImplementedException exception for other update requests.
    if new_allocation_type == old_allocation_type or  not len(new_nw_and_subnet_list) == 1:
        logger.error("F[UpdateIpamRecord] script supports update allocation type only.")
        raise CustomIpamNotImplementedException("F[UpdateIpamRecord] script supports update allocation type only.")
    # network or subnet change along with allocation type update is also not supported.
    if old_allocation_type == 'V4_V6' or new_allocation_type == 'V4_V6':
        if (new_allocation_type == 'V4_ONLY' or old_allocation_type == 'V4_ONLY') and new_nw_and_subnet_list[0][1] != old_nw_and_subnet_list[0][1]:
            logger.error("F[UpdateIpamRecord] script supports update allocation type only.")
            raise CustomIpamNotImplementedException("F[UpdateIpamRecord] script supports update allocation type only, subnet change not supported!")
        if (new_allocation_type == 'V6_ONLY' or old_allocation_type == 'V6_ONLY') and new_nw_and_subnet_list[0][2] != old_nw_and_subnet_list[0][2]:
            logger.error("F[UpdateIpamRecord] script supports update allocation type only.")
            raise CustomIpamNotImplementedException("F[UpdateIpamRecord] script supports update allocation type only, subnet change not supported!")

    # Step 1: Get the reference of the given IPAM record
    name = id
    host_ref = None
    if 'server' in auth_params:
        rest_url = 'https://' + auth_params['server'] + '/wapi/' + auth_params['wapi_version'] + \
                '/record:host?name=' + name
    if 'server6' in auth_params:
        rest_url6 = 'https://[' + auth_params['server6'] + ']/wapi/' + auth_params['wapi_version'] + \
                '/record:host?name=' + name
    try:
        if 'server6' in auth_params:
            r6 = requests.get(url=rest_url6, auth=(auth_params['username'], auth_params['password']),
                            verify=False, timeout=30)
            logger.info("F[UpdateIpamRecord] req[%s] status_code[%s]" % (rest_url6, r6.status_code))
            _check_and_raise_auth_error(r6)
            r6_json = r6.json()
            if r6.status_code == 200:
                host_ref = r6_json[0]['_ref'] if len(r6_json) > 0 and r6_json[0]['_ref'] else None
            elif 'server' in auth_params:
                r = requests.get(url=rest_url, auth=(auth_params['username'], auth_params['password']),
                            verify=False, timeout=30)
                logger.info("F[UpdateIpamRecord] req[%s] status_code[%s]" % (rest_url, r.status_code))
                _check_and_raise_auth_error(r)
                r_json = r.json()
                if r.status_code == 200:
                    host_ref = r_json[0]['_ref'] if len(r_json) > 0 and r_json[0]['_ref'] else None
                else:
                    err_msg = r.status_code 
                    err_msg += ' : '  + r_json['text'] if 'text' in r_json else None
                    logger.error("F[UpdateIpamRecord] Error retrieving the record[%s] reason[%s]" % (name, err_msg))
                    raise CustomIpamRecordNotFoundException("F[UpdateIpamRecord] Error retrieving the record[%s] reason[%s]" % (name, err_msg))
            else:
                err_msg = r6.status_code 
                err_msg += ' : '  + r6_json['text'] if 'text' in r6_json else None
                logger.error("F[UpdateIpamRecord] Error retrieving the record[%s] reason[%s]" % (name, err_msg))
                raise CustomIpamRecordNotFoundException("F[UpdateIpamRecord] Error retrieving the record[%s] reason[%s]" % (name, err_msg))
        elif 'server' in auth_params:
            r = requests.get(url=rest_url, auth=(auth_params['username'], auth_params['password']),
                                verify=False, timeout=30)
            logger.info("F[UpdateIpamRecord] req[%s] status_code[%s]" % (rest_url, r.status_code))
            _check_and_raise_auth_error(r)
            r_json = r.json()
            if r.status_code == 200:
                host_ref = r_json[0]['_ref'] if len(r_json) > 0 and r_json[0]['_ref'] else None
            else:
                err_msg = r.status_code 
                err_msg += ' : '  + r_json['text'] if 'text' in r_json else None
                logger.error("F[UpdateIpamRecord] Error retrieving the record[%s] reason[%s]" % (name, err_msg))
                raise CustomIpamRecordNotFoundException("F[UpdateIpamRecord] Error retrieving the record[%s] reason[%s]" % (name, err_msg))
    except CustomIpamAuthenticationErrorException as e:
        raise
    except CustomIpamRecordNotFoundException as e:
        raise
    except Exception as e:
        logger.error("F[UpdateIpamRecord] Error retrieving the record[%s] reason[%s]" % (name, str(e)))
        raise CustomIpamGeneralException("F[UpdateIpamRecord] Error retrieving the record[%s] reason[%s]" % (name, str(e)))
    
    # Step 2: Raise a valid error message if the given record not found
    if not host_ref:
        err_msg = "F[UpdateIpamRecord] Record[%s] not found!" % name
        logger.error(err_msg)
        raise CustomIpamRecordNotFoundException(err_msg)
 
    # Step 3: Build payload data according to the new allocation_type
    # and call specific rest API and return new allocated items(alloc_info).
    if 'server' in auth_params:
        rest_url = 'https://' + auth_params['server'] + '/wapi/' + \
                        auth_params['wapi_version'] + '/' + host_ref + '?_return_fields=ipv4addrs,ipv6addrs'
    if 'server6' in auth_params:
        rest_url6 = 'https://[' + auth_params['server6'] + ']/wapi/' + \
                        auth_params['wapi_version'] + '/' + host_ref + '?_return_fields=ipv4addrs,ipv6addrs'
    v4_subnet = new_nw_and_subnet_list[0][1]
    v6_subnet = new_nw_and_subnet_list[0][2]
    payload_dict = {}
    if new_allocation_type == 'V4_ONLY' and old_allocation_type == 'V6_ONLY':
        payload_dict['ipv4addrs'] = [{"ipv4addr": 'func:nextavailableip:' + v4_subnet + ',' + network_view}]
        payload_dict['ipv6addrs'] = []
    elif new_allocation_type == 'V4_ONLY' and old_allocation_type == 'V4_V6':
        payload_dict['ipv6addrs'] = []
    elif new_allocation_type == 'V6_ONLY' and old_allocation_type == 'V4_ONLY':
        payload_dict['ipv4addrs'] = []
        payload_dict['ipv6addrs'] = [{"ipv6addr": 'func:nextavailableip:' + v6_subnet + ',' + network_view}]
    elif new_allocation_type == 'V6_ONLY' and old_allocation_type == 'V4_V6':
        payload_dict['ipv4addrs'] = []
    elif new_allocation_type == 'V4_V6' and old_allocation_type == 'V4_ONLY':
        payload_dict['ipv6addrs'] = [{"ipv6addr": 'func:nextavailableip:' + v6_subnet + ',' + network_view}]
    elif new_allocation_type == 'V4_V6' and old_allocation_type == 'V6_ONLY':
        payload_dict['ipv4addrs'] = [{"ipv4addr": 'func:nextavailableip:' + v4_subnet + ',' + network_view}]

    payload = json.dumps(payload_dict)

    if 'server6' in auth_params:
        r6 = requests.put(url=rest_url6, auth=(auth_params['username'], auth_params['password']),
                    verify=False, data=payload, timeout=30)
        logger.info("F[UpdateIpamRecord] req[%s %s] status_code[%s]" % (rest_url6, payload, r6.status_code))
        _check_and_raise_auth_error(r6)
        if r6.status_code in [200, 201]:
            r6_json = r6.json()
            alloc_info = {}
            if 'ipv4addrs' in r6_json and r6_json['ipv4addrs'][0]['ipv4addr']:
                alloc_info['v4_ip'] = r6_json['ipv4addrs'][0]['ipv4addr']
                alloc_info['v4_subnet'] = v4_subnet
            if 'ipv6addrs' in r6_json and r6_json['ipv6addrs'][0]['ipv6addr']:
                alloc_info['v6_ip'] = r6_json['ipv6addrs'][0]['ipv6addr']
                alloc_info['v6_subnet'] = v6_subnet
            return alloc_info
        elif 'server' in auth_params:
            r = requests.put(url=rest_url, auth=(auth_params['username'], auth_params['password']),
                    verify=False, data=payload, timeout=30)
            logger.info("F[UpdateIpamRecord] req[%s %s] status_code[%s]" % (rest_url, payload, r.status_code))
            _check_and_raise_auth_error(r)
            if r.status_code not in [200, 201]:
                err_msg = "%d %s" % (r.status_code, r.text)
                logger.error("F[UpdateIpamRecord] Error updating the host record[%s] req[%s,%s] reason[%s]", name, rest_url, payload, err_msg)
                raise CustomIpamGeneralException("F[UpdateIpamRecord] Error updating the host record[%s] req[%s,%s] reason[%s]", 
                    name, rest_url, payload, err_msg)
            r_json = r.json()
            alloc_info = {}
            if 'ipv4addrs' in r_json and r_json['ipv4addrs'][0]['ipv4addr']:
                alloc_info['v4_ip'] = r_json['ipv4addrs'][0]['ipv4addr']
                alloc_info['v4_subnet'] = v4_subnet
            if 'ipv6addrs' in r_json and r_json['ipv6addrs'][0]['ipv6addr']:
                alloc_info['v6_ip'] = r_json['ipv6addrs'][0]['ipv6addr']
                alloc_info['v6_subnet'] = v6_subnet
            return alloc_info 
        else:
            err_msg = "%d %s" % (r6.status_code, r6.text)
            logger.error("F[UpdateIpamRecord] Error updating the host record[%s] req[%s,%s] reason[%s]", name, rest_url6, payload, err_msg)
            raise CustomIpamGeneralException("F[UpdateIpamRecord] Error updating the host record[%s] req[%s,%s] reason[%s]", 
                name, rest_url6, payload, err_msg)
    elif 'server' in auth_params:
        r = requests.put(url=rest_url, auth=(auth_params['username'], auth_params['password']),
                        verify=False, data=payload, timeout=30)
        logger.info("F[UpdateIpamRecord] req[%s %s] status_code[%s]" % (rest_url, payload, r.status_code))
        _check_and_raise_auth_error(r)
        if r.status_code not in [200, 201]:
            err_msg = "%d %s" % (r.status_code, r.text)
            logger.error("F[UpdateIpamRecord] Error updating the host record[%s] req[%s,%s] reason[%s]", name, rest_url, payload, err_msg)
            raise CustomIpamGeneralException("F[UpdateIpamRecord] Error updating the host record[%s] req[%s,%s] reason[%s]", 
                name, rest_url, payload, err_msg)
        r_json = r.json()
        alloc_info = {}
        if 'ipv4addrs' in r_json and r_json['ipv4addrs'][0]['ipv4addr']:
            alloc_info['v4_ip'] = r_json['ipv4addrs'][0]['ipv4addr']
            alloc_info['v4_subnet'] = v4_subnet
        if 'ipv6addrs' in r_json and r_json['ipv6addrs'][0]['ipv6addr']:
            alloc_info['v6_ip'] = r_json['ipv6addrs'][0]['ipv6addr']
            alloc_info['v6_subnet'] = v6_subnet
        return alloc_info 
