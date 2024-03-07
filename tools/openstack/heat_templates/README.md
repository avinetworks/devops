# HEAT Deployment

This heat template will deploy the supporting infrastructure for, and including,
3 AVI controllers.

## Requirements

* A user and project has been created for AVI
* The controller image has been uploaded
* Nova flavors have been created
* A python virtualenv for the openstack cli - virtualenvwrapper is recommended

### Deployment environment

You'll need the openstack cli, which is best installed in a python virtualenv.
With virutalenvwrapper, this is easily done with:

    mkvirtualenv avi -r requirements.txt

### Environment variables

The heat template requires the following information in a yaml file. This will
be passed as environment data to the cli. The meaning of each variable is
documented in the template:

```yaml
parameters:
  avi_controller_image: avi-controller-17.1.7
  avi_controller_flavor: avi_ctrl.small
  avi_controller_disk_size: 64
  external_network: public
  mgmt_subnet_cidr: 192.168.1.0/24
  se_subnet_cidr: '192.168.2.0/24'
  se_subnet_pool_start: 192.168.2.50
  se_subnet_pool_end: 192.168.2.254
```

## Creating the stack

This command assumes you have already sourced your openstack rc file, otherwise
you can use the `clouds.yaml` approach, in which case you would append the
command with `--os-cloud <name>`.

    openstack stack create <name> -t avi.yml -e <environment>.yml

Once the stack is up, the output data can be retrived and used to complete the
controller setup:

    openstack stack output show <name> --all

## Completing Controller Setup

At this point 3 controllers and supporting infrastructure have been created. Not
handled by the heat template is obtaining direct access to at least one
controller to complete the install. This depends on your openstack environment,
but one method is to allocate a floating ip and assign it to a controller. Once
completed, the floating ip can be unallocated and using the `cluster_public_ip`
can then be used to reach the controllers.
