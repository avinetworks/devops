# AviPowerShellSDK

PowerShell Module for Avi Networks API.

This directory contains a PowerShell module which acts as a wrapper around the Avi Networks API.

Tested with PowerShell Core 6.x+ and (Windows) PowerShell 5.x.

## Basic Usage

Copy the AviSDK folder and its contents into one of the default PowerShell module locations, e.g.:

`%userprofile%\Documents\WindowsPowerShell\Modules`

The module can then be imported using:

```powershell
Import-Module AviSDK
```

Sample scripts can be found in the examples directory.

## Scriptlets provided

```powershell
New-AviSession
Invoke-AviRestMethod
Get-AviObjectsByType
Get-AviObjectByName
Get-AviObjectsPaged
Remove-AviObject
Get-AviObject
Set-AviObject
New-AviObject
Edit-AviObject
Disable-AviCertificateWarnings
```

Standard PowerShell help functions are supported, e.g.:

```powershell
Get-Help New-AviSession
Get-Help Get-AviObjectByName -examples
Get-Help Get-AviObject -full
```
