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
Playbook Examples
********************

-------------------
1. `Include AviSDK Role <https://github.com/avinetworks/devops/blob/master/ansible/training/avi_sdk_role.yml>`_
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
2. `Use Avi Credentials in a Vault <https://github.com/avinetworks/devops/blob/master/ansible/training/avi_controller_vault.yml>`_
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
3. `Basic Avi Pool Setup <https://github.com/avinetworks/devops/blob/master/ansible/training/basic_pool.yml>`_
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
4. `Basic Avi VirtualService Setup <https://github.com/avinetworks/devops/blob/master/ansible/training/basic_vs.yml>`_
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
5. `Basic SSL VirtualService Setup <https://github.com/avinetworks/devops/blob/master/ansible/training/basic_ssl_vs.yml>`_
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



