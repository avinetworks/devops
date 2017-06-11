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


-------------------
Add New Basic Application
-------------------
All the site applications are registered in the `site_applications.yml <playbooks/site_applications.yml>`_. The configuration files for the applications are kept in the `applications <applications>`_ directory. Each applications directory contains `config.yml <applications/app1/config.yml>`_ that represents all Avi RESTful objects that are needed for the application. For example `app1 <applications/app1>`_ contains one pool and one l7 virtualservice with VIP 10.90.64.240. In order to enable the application Here are the step

1. Register in the `site_applications.yml <playbooks/site_applications.yml>`_

.. code-block:: yaml

  - name: setup app1
    tags:
      - app1
    include: setup_basic_vs.yml
    vars:
      app_name: app1

2. Create app1 directory under applications and create `config.yml <applications/app1/config.yml>`_ for the application.

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


      
