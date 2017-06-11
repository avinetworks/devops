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

