Avi Ansible Training Site Example
``````````````````````````````
.. contents::
  :local:

This is an example of setting up a full Avi Site with Cloud and applications. 

*********
Site Layout 
*********
Here are the main components of the site example.
- `site.yml <https://github.com/avinetworks/devops/blob/master/ansible/training/site-example/site.yml>`_: This describes the playbooks for setup of the site. It includes sections for cloud setup and application setup.

Usage for full site setup
.. code-block:: shell
  
  ansible-playbook site.yml

Usage for just cloud setup
.. code-block:: shell
  
  ansible-playbook playbooks/site_clouds.yml

Usage for just applications setup. This would setup all the applications that are registered in site_applications.yml
.. code-block:: shell
  
  ansible-playbook playbooks/site_applications.yml

************
Playbooks
************

The playbooks directory contains all the resusable playbooks and role to setup site.

* `setup_basic_vs.yml <playbooks/setup_basic_vs.yml>`_: Contains playbook to setup basic pool and vs
* `setup_ssl_vs.yml <playbooks/setup_ssl_vs.yml>`_: Playbook to setup SSL VS with HTTP policies like content swtiching etc.
* `role <playbooks/role>`_: local roles like cloud to setup cloud configurations

************
Clouds
************
All site clouds are registered to the site.yml via `site_clouds.yml <playbooks/site_clouds.yml>`_. Each cloud has a directory with a configuration file config.yml. The cloud settings for the site are perform via a cloud role that contains playbook to setup Avi Cloud object, service engine group and cloud networks. It also allows for a separate cloud credential files that is automatically merged by the cloud role before applying it to the Avi Controller.

-------------------
Add a VMWare Cloud setup
-------------------

Register in the `site_applications.yml <playbooks/site_applications.yml>`_:

.. code-block:: yaml

  - name: Avi Cloud | Setup VMWare Cloud with Write Access
    include_role:
      name: cloud
    vars:
      cloud_name: vmware

Create vmware cloud `config.yml <clouds/vmware/config.yml>`_:

The config.yml has a Avi Cloud object that represents the cloud configuration. It also has a setting to customize wait times for the cloud discovery. Note, that the vmware cloud password is not included here but provided via a separate creds.yml file. 

.. code-block:: yaml

  avi_cloud_obj:
    api_version: 17.1.2
    name: Default-Cloud
    vtype: CLOUD_VCENTER
    dhcp_enabled: true
    license_type: "LIC_CORES"
    vcenter_configuration:
      username: "root"
      datacenter: "10GTest"
      management_network: "/api/vimgrnwruntime?name=Mgmt_Arista"
      privilege: "WRITE_ACCESS"
      vcenter_url: "10.10.2.10"

  cloud_discovery_wait: 1

************
Applications
************
All the site applications are registered in the `site_applications.yml <playbooks/site_applications.yml>`_. The configuration files for the applications are kept in the `applications <applications>`_ directory. Each applications directory contains `config.yml <applications/app1/config.yml>`_ that represents all Avi RESTful objects that are needed for the application. For example `app1 <applications/app1>`_ contains one pool and one l7 virtualservice with VIP 10.90.64.240. In order to enable the application Here are the step

-------------------
Basic Application
-------------------

Register in the `site_applications.yml <playbooks/site_applications.yml>`_:

.. code-block:: yaml

  - name: setup app1
    tags:
      - app1
    include: setup_basic_vs.yml
    vars:
      app_name: app1

Create app1 directory under applications and create `config.yml <applications/app1/config.yml>`_ for the application.

.. code-block:: yaml

    avi_pool_objs:
      - name: app1-pool
        lb_algorithm: LB_ALGORITHM_ROUND_ROBIN
        servers:
          - ip:
               addr: '10.90.64.16'
               type: 'V4'
          - ip:
               addr: '10.90.64.14'
               type: 'V4'

    avi_virtualservice_objs:
      - name: app1
        services:
          - port: 80
        pool_ref: '/api/pool?name=app1-pool'
        vip:
          - ip_address:
              addr: 10.90.64.240
              type: 'V4'
            vip_id: '1'

-------------------
SSL Application with Content Switching 
-------------------

Register in the `site_applications.yml <playbooks/site_applications.yml>`_

.. code-block:: yaml

    - name: setup app3
      tags:
        - app3
      include: setup_ssl_vs.yml
      vars:
        app_name: app3

Create app1 directory under applications and create `config.yml <applications/app3/config.yml>`_ for the application.

.. code-block:: yaml

    avi_pool_objs:
      - name: app3-pool-A
      - name: app3-pool-B

    avi_httppolicyset_objs:
      - api_version: 17.1.2
        name: "app3-httppolicy"
        http_request_policy: ...

    avi_virtualservice_objs:
      - name: app3
