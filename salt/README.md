# Salt Integration

This directory will contain examples of using Avi with SaltStack


## About SaltStack

SaltStack is python based, and uses a master-minion relationship for configuration management.


## Installing SaltStack Master

### CentOS

1.  Install the SaltStack repository
    `sudo yum install https://repo.saltstack.com/yum/redhat/salt-repo-latest-2.el7.noarch.rpm`
2.  Run `sudo yum clean expire-cache`
3.  Install the salt-master and salt-minion
    `sudo yum install salt-master salt-minion`
4.  Enable the salt-master and minion at boot
    `systemctl enable salt-master`
    `systemctl enable salt-minion`
5.  Start the salt-master and salt-minion
    `systemctl start salt-master`
    `systemctl start salt-minion`

### Ubuntu

1.  Make sure `python-software-properties` is installed
    `sudo apt-get install python-software-properties`
2.  Install the SaltStack repository
    `sudo add-apt-repository ppa:saltstack/salt`
3.  Update the package management database
    `sudo apt-get update`
4.  Install the salt-master and salt-minion
    `sudo apt-get install salt-master salt-minion`
5.  Enable the salt-master and minion at boot
    `systemctl enable salt-master`
    `systemctl enable salt-minion`
6.  Start the salt-master and salt-minion
    `systemctl start salt-master`
    `systemctl start salt-minion`

Coming Soon!

## Installing SaltStack Minion

### CentOS

1.  Install the SaltStack repository
    `sudo yum install https://repo.saltstack.com/yum/redhat/salt-repo-latest-2.el7.noarch.rpm`
2.  Run `sudo yum clean expire-cache`
3.  Install the salt-minion
    `sudo yum install salt-minion`
4.  Configure the salt-minion configuration file.
5.  Enable the salt-minion at boot
    `systemctl enable salt-minion`
6.  Start the salt-minion
    `systemctl start salt-minion`

### Ubuntu

1.  Make sure `python-software-properties` is installed
    `sudo apt-get install python-software-properties`
2.  Install the SaltStack repository
    `sudo add-apt-repository ppa:saltstack/salt`
3.  Update the package management database
    `sudo apt-get update`
4.  Install the salt-minion
    `sudo apt-get install salt-master salt-minion`
5.  Configure the salt-minion configuration file.
6.  Enable the and minion at boot
    `systemctl enable salt-minion`
7.  Start the salt-minion
    `systemctl start salt-minion`

## Salt Examples

Coming Soon!
