# Helper tool for installing Avi into VCF 9.0

This shell script will assist you in the following tasks
- Uploading the Avi bundle to SDDC manager


- Uploading the SDDC manager root certificate to NSX manager as a trusted CA


- Registering the Avi enforcement point in NSX Manager

The helper script is a bash script and will need to be run from an appropriate system. (Linux, MacOS, Windows with WSL)




## Detailed information

<details>
    <summary>Uploading the bundle to SDDC manager</summary>
<br/><br/>

This requires 3 files, pvc.json, pvc.sig, and the Avi OVA for the 31.1.1 (VCF 9.0) or 31.1.2 (VCF 9.0.1) release.  The pvc files are available in this repo, and the controller OVA is available on the Broadcom support portal.

It is critical that the product version entered in the tool matches the build number in the pvc.json exactly.


Avi Version | VCF version | Avi OVA filename | Avi product version 
----------- | ----------- | ---------------- | -------------------
31.1.1 | 9.0.0 | controller-31.1.1-9122.ova | 31.1.1-24544104
31.1.2 | 9.0.1 | controller-31.1.2-9193.ova | 31.1.2-24923866

</details>



<details>
    <summary>Uploading the SDDC manager root certificate to NSX manager as a trusted CA</summary>
<br/><br/>

This step is only necessary if you're using the SDDC Manager certificate lifecycle integration.  The easiest way to get the certificate in the format required is to export the root CA cert from the Avi controller UI and save it to a file named root.crt.

### Exporting the certificate
![Exporting certificate in Avi UI](images/export_cert.png 'Exporting the certificate')

### Copy certificate to clipboard
![Copying certificate to clipboard](images/copy_to_clipboard.png 'Copy to clipboard')
Then save the clipboard content to a file named root.crt  
</details>