# -*- coding: utf-8 -*-
"""
requests_toolbelt.source_adapter
================================

This file contains an implementation of the SourceAddressAdapter originally
demonstrated on the Requests GitHub page.
"""
from requests.adapters import HTTPAdapter
import ssl
import requests
import random
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

from _compat import poolmanager, basestring


class SourceAddressAdapter(HTTPAdapter):
    """
    A Source Address Adapter for Python Requests that enables you to choose the
    local address to bind to. This allows you to send your HTTP requests from a
    specific interface and IP address.

    Two address formats are accepted. The first is a string: this will set the
    local IP address to the address given in the string, and will also choose a
    semi-random high port for the local port number.

    The second is a two-tuple of the form (ip address, port): for example,
    ``('10.10.10.10', 8999)``. This will set the local IP address to the first
    element, and the local port to the second element. If ``0`` is used as the
    port number, a semi-random high port will be selected.

    .. warning:: Setting an explicit local port can have negative interactions
                 with connection-pooling in Requests: in particular, it risks
                 the possibility of getting "Address in use" errors. The
                 string-only argument is generally preferred to the tuple-form.

    Example usage:

    .. code-block:: python

        import requests
        from requests_toolbelt.adapters.source import SourceAddressAdapter

        s = requests.Session()
        s.mount('http://', SourceAddressAdapter('10.10.10.10'))
        s.mount('https://', SourceAddressAdapter(('10.10.10.10', 8999)))
    """

    __attrs__ = HTTPAdapter.__attrs__ + ['ssl_version']



    def __init__(self, source_address, **kwargs):
        if isinstance(source_address, basestring):
            self.source_address = (source_address, 0)
        elif isinstance(source_address, tuple):
            self.source_address = source_address
        else:
            raise TypeError(
                "source_address must be IP address string or (ip, port) tuple"
            )

        super(SourceAddressAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):

# TLSv1_3 supported ciphers
# TLS_AES_256_GCM_SHA384
# TLS_CHACHA20_POLY1305_SHA256
# TLS_AES_128_GCM_SHA256
# TLS_AES_128_CCM_8_SHA256
# TLS_AES_128_CCM_SHA256


        def pick_ssl():
            #TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
            ssldict1 = {"cipher":"ECDHE-ECDSA-AES128-GCM-SHA256" , "sslver": ssl.PROTOCOL_TLSv1_2}
            ssldict2 = {"cipher":"TLS_AES_128_GCM_SHA256" , "sslver": "tls13"}
            #TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
            ssldict3 = {"cipher":"ECDHE-ECDSA-AES256-GCM-SHA384" , "sslver": ssl.PROTOCOL_TLSv1_2}
            ssldict4 = {"cipher":"TLS_AES_256_GCM_SHA384" , "sslver": "tls13"}
            #TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
            ssldict5 = {"cipher":"ECDHE-RSA-AES128-GCM-SHA256" , "sslver": ssl.PROTOCOL_TLSv1_2}
            #TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
            ssldict6 = {"cipher":"ECDHE-RSA-AES256-GCM-SHA384" , "sslver": ssl.PROTOCOL_TLSv1_2}
            ssldict7 = {"cipher":"TLS_CHACHA20_POLY1305_SHA256", "sslver": "tls13"}
            ssldict8 = {"cipher":"TLS_AES_128_CCM_8_SHA256", "sslver": "tls13"}
            ssldict9 = {"cipher":"TLS_AES_128_CCM_SHA256", "sslver": "tls13"}
            #ssldictset = [ssldict1,ssldict2,ssldict3,ssldict4,ssldict5,ssldict6,ssldict7,ssldict8,ssldict9]
            #ssldictset = [ssldict5,ssldict2,ssldict6,ssldict4,ssldict7]

            ## legacy
            # ssldict1 = {"cipher":"AES128-SHA256" , "sslver": ssl.PROTOCOL_TLSv1_2}
            # ssldict2 = {"cipher":"ECDHE-RSA-AES128-SHA" , "sslver": ssl.PROTOCOL_TLSv1_1}
            # ssldict3 = {"cipher":"AES128-GCM-SHA256", "sslver": ssl.PROTOCOL_TLSv1_2}
            # ssldict4 = {"cipher":"ECDHE-ECDSA-AES128-SHA" , "sslver": ssl.PROTOCOL_TLSv1_1}
            # ssldict5 = {"cipher":"ECDHE-RSA-AES128-SHA" , "sslver": ssl.PROTOCOL_TLSv1}
            # ssldict6 = {"cipher":"ECDHE-ECDSA-AES128-SHA" , "sslver": ssl.PROTOCOL_TLSv1}
            # ssldict7 = {"cipher":"ECDHE-ECDSA-AES128-GCM-SHA256", "sslver": ssl.PROTOCOL_TLSv1_2}
            # #ssldict8 = {"cipher":"TLS_AES_128_GCM_SHA256", "sslver": "tls13"}
            # # ssldict9 = {"cipher":"ECDHE-RSA-AES128-GCM-SHA256", "sslver": ssl.PROTOCOL_TLSv1_2}
            # ssldictset = [ssldict1,ssldict2,ssldict3,ssldict4,ssldict5,ssldict6,ssldict7]

            return(random.choices([ssldict1, ssldict2, ssldict3, ssldict4, ssldict5, ssldict6, ssldict7, ssldict8, ssldict9], weights=[20,80,20,80,20,20,80,80,80],k=1)[0])
            #return(random.choice(ssldictset))

        ssldict = pick_ssl()
        #print(ssldict)
        if ssldict['sslver'] == "tls13":
            context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)
            #context.protocol = ssl.PROTOCOL_TLS  
            context.options = ssl.OP_NO_TLSv1 # prevents TLS 1.0
            context.options = ssl.OP_NO_TLSv1_1 # prevents TLS 1.1
            context.options = ssl.OP_NO_TLSv1_2
        else:    
            context = ssl.SSLContext(ssldict['sslver'])
            context.set_ciphers(ssldict['cipher'])
        context.verify_mode = ssl.CERT_NONE  # 1. key, 2. cert, 3. intermediates

        self.poolmanager = poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            source_address=self.source_address,
            ssl_context=context)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['source_address'] = self.source_address
        return super(SourceAddressAdapter, self).proxy_manager_for(
            *args, **kwargs)