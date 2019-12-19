Avi Ansible Training Site Example
``````````````````````````````
.. contents::
  :local:

This is an example of setting up a full Avi Site with Cloud and applications. Note This version is compatible with Ansible 2.4 only.

*********
Installation
*********

The site example requires avinetworks.avisdk and avinetworks.aviconfig roles.
Please install them from Ansible galaxy using following command

.. code-block:: shell

  pip install avisdk
  ansible-galaxy install avinetworks.avisdk
  ansible-galaxy install avinetworks.aviconfig



*********
Site Layout 
*********
Here are the main components of the site example.
- `site.yml <https://github.com/avinetworks/devops/blob/master/ansible/training/site-example/site.yml>`_: This describes the playbooks for setup of the site. It includes sections for cloud setup and application setup.

Usage for full site setup

.. code-block:: shell
  
  ansible-playbook site.yml --extra-vars "site_dir=`pwd`"

Usage for just cloud setup

.. code-block:: shell
  
  ansible-playbook site_clouds.yml --extra-vars "site_dir=`pwd`"

Usage for just applications setup. This would setup all the applications that are registered in site_applications.yml

.. code-block:: shell
  
  ansible-playbook site_applications.yml --extra-vars "site_dir=`pwd`"

Usage to delete all applications in the site_applications.yml. The flag avi_config_state=absent will override the individual object state for deletion purpose.

.. code-block:: shell
  
  ansible-playbook site_applications.yml --extra-vars "site_dir=`pwd` avi_config_state=absent"

************
Roles
************

The roles directory contains AviConfig role that has ability to process a configuration file with avi configurations that is listed on a per-resource type. It performs the configuration in the right order as required by the object dependencies.

************
Clouds
************
All site clouds are registered to the site.yml via `site_clouds.yml <site_clouds.yml>`_. Each cloud has a directory with a configuration file config.yml. The cloud settings for the site are perform via a cloud role that contains playbook to setup Avi Cloud object, service engine group and cloud networks. It also allows for a separate cloud credential files that is automatically merged by the cloud role before applying it to the Avi Controller.

-------------------
Add a VMWare Cloud setup
-------------------

Add a new directory for vmware cloud in `clouds <clouds>` directory. The following lists the steps to create a new cloud

1. Playbook for the cloud as `cloud.yml <clouds/vmware/cloud.yml>`_

.. code-block:: yaml

    - hosts: localhost
      connection: local
      vars:
        api_version: 17.1.2
        # this will pick up config from the clouds/vmware directory
        cloud_name: vmware
      roles:
        - role: avinetworks.avisdk
      tasks:
        - name: Setting up cloud
          debug: msg="{{cloud_name}}"
        - name: Avi Cloud | Setup VMWare Cloud with Write Access
          include_role:
            name: avinetworks.aviconfig
          vars:
            avi_config_file: "{{ site_dir }}/clouds/{{cloud_name}}/config.yml"
            avi_creds_file: "{{ site_dir }}/vars/creds.yml"
            
 
2. Provide cloud configuration settings as `config.yml <clouds/vmware/config.yml>`_

.. code-block:: yaml

  avi_config:
    cloud:
      - api_version: 17.1.2
        name: Default-Cloud
        vtype: CLOUD_VCENTER
        dhcp_enabled: true
        license_type: "LIC_CORES"
        vcenter_configuration:
          username: root
          password: vmware
          datacenter: "10GTest"
          management_network: "/api/vimgrnwruntime?name=Mgmt_Arista"
          privilege: "WRITE_ACCESS"
          vcenter_url: "10.10.2.10"


3. Register in the `site_cloud.yml <site_clouds.yml>`_:

.. code-block:: yaml

  - include: clouds/vmware/cloud.yml

************
Applications
************
All the site applications are registered in the `site_applications.yml <site_applications.yml>`_. The configuration files for the applications are kept in the `applications <applications>`_ directory. Each applications directory contains `config.yml <applications/app1/config.yml>`_ that represents all Avi RESTful objects that are needed for the application. In addition, there is an playbook for setting up application eg. `app.yml <applications/app1/app.yml>`_. The example only configures Avi settings but this playbook can be extended to create VMs, create SSL certs etc. The `app1 <applications/app1>`_ contains one pool and one l7 virtualservice with VIP 10.90.64.240. 

Here are steps to enable the application Here are the step:

-------------------
Basic Application
-------------------

1. Register in the `site_applications.yml <site_applications.yml>`_:

.. code-block:: yaml

    - include: applications/app1/app.yml

2. Create app1 directory under applications and create `config.yml <applications/app1/config.yml>`_ for the application.

.. code-block:: yaml

    avi_config:
      pool:
        - name: app1-pool
          lb_algorithm: LB_ALGORITHM_ROUND_ROBIN
          servers:
            - ip:
                 addr: '10.90.64.16'
                 type: 'V4'
            - ip:
                 addr: '10.90.64.14'
                 type: 'V4'

      virtualservice:
        - name: app1
          services:
            - port: 80
          pool_ref: '/api/pool?name=app1-pool'
          vip:
            - ip_address:
                addr: 10.90.64.240
                type: 'V4'
              vip_id: '1'

3. Create `app.yml <applications/app1/app.yml>`_ playbook under the applications directory

.. code-block:: yaml

  ---
  - hosts: localhost
    connection: local
    vars:
      api_version: 17.1.2
      app_name: app1

    roles:
      - role: avinetworks.avisdk

    tasks:
      - name: Setting up Application
        debug: msg="{{ app_name }}"

      - name: Avi Application | Setup VMWare Cloud with Write Access
        include_role:
          name: avinetworks.aviconfig
        vars:
          avi_config_file: "{{ site_dir }}/applications/{{app_name}}/config.yml"
          avi_creds_file: "{{ site_dir }}/vars/creds.yml"

-------------------
SSL Application with Content Switching 
-------------------

1. Register in the `site_applications.yml <site_applications.yml>`_

.. code-block:: yaml

    - include: applications/app3/app.yml

2. Create app1 directory under applications and create `config.yml <applications/app3/config.yml>`_ for the application.

.. code-block:: yaml

  avi_config:
    pool:
      - name: app3-pool-A
      - name: app3-pool-B

    httppolicyset:
      - api_version: 17.1.2
        name: "app3-httppolicy"
        http_request_policy: ...

    virtualservice:
      - name: app3

3. Create `app.yml <applications/app3/app.yml>`_ playbook under the applications directory

.. code-block:: yaml

  ---
  - hosts: localhost
    connection: local
    vars:
      api_version: 17.1.2
      app_name: app3

    roles:
      - role: avinetworks.avisdk

    tasks:
      - name: Setting up Application
        debug: msg="{{ app_name }}"

      - name: Avi Application | Setup VMWare Cloud with Write Access
        include_role:
          name: avinetworks.aviconfig
        vars:
          avi_config_file: "{{ site_dir }}/applications/{{app_name}}/config.yml"
          avi_creds_file: "{{ site_dir }}/vars/creds.yml"
          
          
