Avi Ansible Training Playbooks
``````````````````````````````
.. contents::
  :local:

Avi RESTful objects can be programmed using Avi Ansible Modules. With Ansible 2.4 Avi Ansible 
`Network Modules <http://docs.ansible.com/ansible/list_of_network_modules.html>`_. Avi Ansible modules can also be installed
via Ansible Galaxy as

.. code-block:: shell 

    ansible-galaxy install avinetworks.avisdk 


********************
Setup and Installation
********************
Here are simple steps to try Avi Ansible Integration

1. Install Avi SDK with version >= 17.1.2

.. code-block:: shell 

    pip install --upgrade avisdk>=17.1.2

2. Install Ansible if not already present

.. code-block:: shell 

    pip install ansible==2.3

3. Update Avi controller's credentials

.. code-block:: shell 

    update controller credentials in vars/cred_unsecure.yml

4. Run Avi Ansible Example to create a sample VS. Note that the VIPs would be down as the example server IPs may not be up.

.. code-block:: shell 

    ansible-playbook basic_vs.yml 


********************
Playbook Examples
********************

-------------------
`Include AviSDK Role <https://github.com/avinetworks/devops/blob/master/ansible/training/avi_sdk_role.yml>`_
-------------------
This shows example of how to include avisdk role in playbook and test that it works.

.. code-block:: yaml 

    ---
    - hosts: localhost
    connection: local
    roles:
      - role: avinetworks.avisdk
    tasks:
      - name: Print Hello
        debug: msg="Hello"
      
---------------
`Use Avi Credentials in a Vault <https://github.com/avinetworks/devops/blob/master/ansible/training/avi_controller_vault.yml>`_
---------------
Example playbook using Avi Controller credentials in an Ansible vault

.. code-block:: yaml

    ---
    - hosts: localhost
      connection: local
      vars_files:
        - "vars/creds.yml"
      vars:
        tenant: admin
      roles:
        - role: avinetworks.avisdk

-------------
`Basic Avi Pool Setup <https://github.com/avinetworks/devops/blob/master/ansible/training/basic_pool.yml>`_
-------------
Example to setup a simple Avi Pool with two servers

.. code-block:: yaml

  tasks:
    - name: Create or Update Pool
      avi_pool:
        controller: "{{ avi_controller}}"
        username: "{{ avi_username }}"
        password: "{{ avi_password }}"
        api_version: "{{ api_version }}"
        name: "foo-pool"
        health_monitor_refs:
          - '/api/healthmonitor?name=System-HTTP'
        servers:
          - ip:
               addr: '10.90.64.16'
               type: 'V4'
          - ip:
               addr: '10.90.64.14'
               type: 'V4'

-------------
`Basic Avi VirtualService Setup <https://github.com/avinetworks/devops/blob/master/ansible/training/basic_vs.yml>`_
-------------
Example to setup a simple Avi Virtualservice and Pool with two servers

.. code-block:: yaml

  tasks:
    - name: Create or Update Pool
      avi_pool:
        controller: "{{ avi_controller}}"
        username: "{{ avi_username }}"
        password: "{{ avi_password }}"
        api_version: "{{ api_version }}"
        name: "{{app_name}}-pool"
        health_monitor_refs:
          - '/api/healthmonitor?name=System-HTTP'
          - '/api/healthmonitor?name=System-Ping'
        cloud_ref: '/api/cloud?name=Default-Cloud'
        servers:
          - ip:
               addr: '10.90.64.16'
               type: 'V4'
          - ip:
               addr: '10.90.64.14'
               type: 'V4'

    - name: Create Virtual Service
      avi_virtualservice:
        controller: "{{ avi_controller}}"
        username: "{{ avi_username }}"
        password: "{{ avi_password }}"
        api_version: "{{ api_version }}"
        name: "{{app_name}}"
        pool_ref: "/api/pool?name={{app_name}}-pool"
        cloud_ref: '/api/cloud?name=Default-Cloud'
        vip:
          - ip_address:

              addr: '10.90.64.222'
              type: 'V4'
            vip_id: '1'
        services:
          - port: 80
          
 
-------------
`Basic SSL VirtualService Setup <https://github.com/avinetworks/devops/blob/master/ansible/training/basic_ssl_vs.yml>`_
-------------
Example to setup a simple Avi SSL Virtualservice and Pool with two servers. In this case SSL key and Certificate object needs to be created first. Here is example of how to create a self signed certificate and register it to Avi. The playbook creates the ssl certs in ssl_certs directory which is then lookedup by the avi_sslkeyandcertificate module. 

.. code-block:: yaml
  
  vars:
    app_name: foo
  tasks:
    - name: create self-signed SSL cert
      command: openssl req -new -nodes -x509 -subj "/C=US/ST=CA/L=San Francisco/O=IT/CN={{ app_name }}.com" -days 3650 -keyout ssl_certs/{{app_name}}.key -out ssl_certs/{{app_name}}.crt -extensions v3_ca creates=ssl_certs/{{app_name}}.crt

    - name: Upload or Update SSL certificate - always changed due to sensitve field
      avi_sslkeyandcertificate:
        controller: "{{ avi_controller}}"
        username: "{{ avi_username }}"
        password: "{{ avi_password }}"
        api_version: "{{ api_version }}"
        tenant: admin
        key: "{{ lookup('file', 'ssl_certs/'~app_name~'.key') }}"
        certificate:
          self_signed: true
          certificate: "{{ lookup('file', 'ssl_certs/'~app_name~'.crt')}}"
        type: SSL_CERTIFICATE_TYPE_VIRTUALSERVICE
        name: "{{app_name}}-cert"

Once the SSL certificate object is uploaded to Avi. The SSL virtualservice can be setup. In this example, the virtual service is setup with `SSL Everywhere <https://kb.avinetworks.com/docs/17.1/ssl-everywhere/>`_.

.. code-block:: yaml

  tasks:
    - name: Create Virtual Service
      avi_virtualservice:
        controller: "{{ avi_controller}}"
        username: "{{ avi_username }}"
        password: "{{ avi_password }}"
        api_version: "{{ api_version }}"
        name: "{{app_name}}"
        pool_ref: "/api/pool?name={{app_name}}-pool"
        cloud_ref: '/api/cloud?name=Default-Cloud'
        vip:
          - ip_address:
              addr: '10.90.64.225'
              type: 'V4'
            vip_id: '1'
        ssl_key_and_certificate_refs:
          - '/api/sslkeyandcertificate?name={{app_name}}-cert'
        ssl_profile_ref: '/api/sslprofile?name=System-Standard'
        application_profile_ref: '/api/applicationprofile?name=System-Secure-HTTP'
        services:
          - port: 80
          - port: 443
            enable_ssl: true

-------------
`SSL Virtualservice with Content Switching <https://github.com/avinetworks/devops/blob/master/ansible/training/basic_ssl_vs_content_switching.yml>`_
-------------
Example to perform content swtiching to two pools A and B using HTTP Policysets. Here is a simple task representing setup of such a HTTP Policyset.

.. code-block:: yaml

  tasks:
    - name: Create HTTP PolicySet
      avi_httppolicyset:
        controller: "{{ avi_controller}}"
        username: "{{ avi_username }}"
        password: "{{ avi_password }}"
        api_version: "{{ api_version }}"
        name: "{{app_name}}-httppolicy"
        http_request_policy:
          rules:
            - index: 1
              enable: true
              name: "{{app_name}}-pool-foo"
              match:
                path:
                  match_case: INSENSITIVE
                  match_str:
                    - /foo
                  match_criteria: EQUALS
              switching_action:
                action: HTTP_SWITCHING_SELECT_POOL
                status_code: HTTP_LOCAL_RESPONSE_STATUS_CODE_200
                pool_ref: "/api/pool?name={{app_name}}-pool-foo"
            - index: 2
              enable: true
              name: test-test2
              match:
                path:
                  match_case: INSENSITIVE
                  match_str:
                    - /bar
                  match_criteria: CONTAINS
              switching_action:
                action: HTTP_SWITCHING_SELECT_POOL
                status_code: HTTP_LOCAL_RESPONSE_STATUS_CODE_200
                pool_ref: "/api/pool?name={{app_name}}-pool-bar"
        is_internal_policy: false

The above HTTP Policyset can be configured in the virtualservice as

.. code-block:: yaml

    - name: Create Virtual Service with HTTP Policies
      avi_virtualservice:
        controller: "{{ avi_controller}}"
        username: "{{ avi_username }}"
        password: "{{ avi_password }}"
        api_version: "{{ api_version }}"
        name: "{{app_name}}"
        pool_ref: "/api/pool?name={{app_name}}-pool"
        cloud_ref: '/api/cloud?name=Default-Cloud'
        vip:
          - ip_address:
              addr: '10.90.64.230'
              type: 'V4'
            vip_id: '1'
        ssl_key_and_certificate_refs:
          - '/api/sslkeyandcertificate?name={{app_name}}-cert'
        ssl_profile_ref: '/api/sslprofile?name=System-Standard'
        application_profile_ref: '/api/applicationprofile?name=System-Secure-HTTP'
        services:
          - port: 80
          - port: 443
            enable_ssl: true
        http_policies:
          - index: 11
            http_policy_set_ref: '/api/httppolicyset?name={{app_name}}-httppolicy'

********
`Full Site Example <site-example>`_
********

This has example of a full featured site automation for Avi configuration. It show how to setup clouds and applications for the full site. 
