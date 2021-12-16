# Log4j - CVE-2021-44228

This playbook will deploy a Pre-CRS group and log4j rules via following kb:
https://kb.vmware.com/s/article/87100

## How to use

Populate variables.yml file once completed

``` bash
ansible-playbook pre-crs.yml --extra-vars=@variables.yml
```