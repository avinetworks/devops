# Certificate Renewal

Playbook Developed by: William Stoneman</br>


## Table of Contents
1.	[Introduction](#Introduction)
1.	[Installation](#Installation)
1.	[Requirements](#Requirements)
1.	[Variable Input File](#Variable-Input-File)
1.	[Execution](#Execution)
1.	[Considerations](#Considerations)




# Introduction

The purpose of this Terraform Script is to provide the ability to replace Application or Controller certificates that were generated using the CSR method on the Avi Controller.

# Installation

The methods used within this Terraform Script can be found in the Avi Networks Terriform Provider (vmware/avi). The following software is required to successfully execute this Terraform Script:

Terraform (tested on Terraform version 1.1.0 and up)

# Requirements

This Terraform Script has been tested against renewing certificate Objects for both Application and Controller certificates generated using the built in CSR process on the Avi Controller. 

* A CSR will need to be manaully created on the Avi Controller, and a certificate generated from a CA.

* The generated certificate file will need to be stored in the same directory as this Terraform Script.



**[Back to top](#table-of-contents)**


# Variable-Input-File

The following is a breakdown of the required Variables for this Terraform Script.

avi_username.default = *\<Avi Username\>*

avi_controller.default = *\<Avi Controller IP/FQDN\>*

avi_password.default = *\<Avi Password\>*

avi_tenant.default = *\<Avi Tenant\>*

avi_version.default = *\<Avi Version\>*

cert_name.default = *\<Avi Certificate Name\>*

cert_file.default = *\<Certificate file name (Ex. cert.csr)\>*


**[Back to top](#table-of-contents)**

# Execution

The flow of Actions for this Terraform Script are:

1.	Replace the Certificate element field of the specified certificate Object.

If the certificate renewal failed, the Terraform Script will fail, and the end user will need to validate the provided information.


**[Back to top](#table-of-contents)**

# Considerations

The following are considerations that need to be understood when executing this Playbook:

* There is no way for the Terraform Script to validate that the provided certificate text is valid for the selected Certificate Object. Therefore, we assume the end user has validated that the provided text is correct.

* We are relying on the positive response of the Certificate Object update, that the operation was successful. Therefore, we leave it up to the end user to validate the Controller accessibility.


