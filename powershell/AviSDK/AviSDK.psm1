#Class for storing Avi credentials
class AviCredentials {
  [string]
  $Controller
  
  [string]
  $Username
  
  [string]
  $Password
  
  [string]
  $ApiVersion
  
  [string]
  $Tenant
  
  [string]
  $TenantUUID
  
  [string]
  $Token
  
  [Int32]
  $Port
  
  [bool]
  $Secure
  
  [string]
  $SessionID
  
  [string]
  $CSRFToken
  
  [Int32]
  $Timeout

  [Int32]
  $RetryCount

  [Int32]
  $RetryWait

  [System.Uri]
  $Proxy

  [System.Management.Automation.PSCredential]
  $ProxyCredential

  [switch]
  $ProxyUseDefaultCredentials
}

#Class for storing the API session information
class AviSession {
  [AviCredentials]
  $Credentials
  
  [string]
  $Prefix
  
  [System.Object]
  $WebSession
  
  [System.DateTime]
  $LastUsed

  [System.Collections.HashTable]
  $Flags

  [System.Object]
  $AuthResponse
}

<# 
  .Synopsis
  Initialize an API session to an Avi Vantage controller.

  .Description
  Creates a new API session to an Avi Vantage controller or controller cluster.

  .Parameter Controller
  The hostname or IP address of the Avi Vantage controller or controller cluster.

  .Parameter Username
  The username to authenticate with.

  .Parameter Password
  The password to authenticate with.

  .Parameter Port
  The TCP port on which to connect to the Avi Vantage controller or controller cluster.

  .Parameter Secure
  $True to use https, $False to use http.

  .Parameter APIVersion
  Avi API version (default="16.4.4").

  .Parameter Tenant
  Name of tenant to bind the session to (default="admin").

  .Parameter TenantUUID
  UUID of tenant to bind to.

  .Parameter Timeout
  Timeout for REST calls (default=30).

  .Parameter RetryCount
  Retry count for unsuccessful REST calls (default=3).

  .Parameter RetryWait
  Seconds to wait before retrying a failed REST call (default=2).

  .Parameter ErrorOnNotFound
  Switch to raise an error on object not found rather than returning $null

  .Parameter Proxy
  Proxy server to use for all REST calls.

  .Parameter ProxyCredential
  Proxy credentials to use for all REST calls (Proxy must be specified).

  .Parameter ProxyUseDefaultCredentials
  Use default credentials for proxy (Proxy must be specified).

  .Inputs
  None. You cannot pipe objects to New-AviSession.

  .Outputs
  AviSession object for use in other SDK functions.

  .Example  
  New-AviSession -Controller 1.2.3.4 -Username admin -Password avi123 -APIVersion 16.2.3

  .Example
  New-AviSession -Controller controller.avi.local -Username admin -Password avi123 -APIVersion 17.2.4 -Tenant Demo

  New session scoped to tenant "Demo"
#>
function New-AviSession {
  [CmdletBinding(DefaultParametersetName="None")]
  param(
    [Parameter(Mandatory=$True, Position=1)]
    [string]
    $Controller,
    
    [Parameter(Mandatory=$True, Position=2)]
    [string]
    $Username,
    
    [Parameter(Mandatory=$True, Position=3)]
    [string]
    $Password,
    
    [Parameter(Mandatory=$False)]
    [Int32]
    $Port,
    
    [Parameter(Mandatory=$False)]
    [bool]
    $Secure=$True,
    
    [Parameter(Mandatory=$False)]
    [string]
    $ApiVersion="16.4.4",
    
    [Parameter(Mandatory=$False)]
    [string]
    $Tenant="admin",
    
    [Parameter(Mandatory=$False)]
    [string]
    $TenantUUID,
    
    [Parameter(Mandatory=$False)]
    [Int32]
    $Timeout=30,

    [Parameter(Mandatory=$False)]
    [Int32]
    $RetryCount=3,

    [Parameter(Mandatory=$False)]
    [Int32]
    $RetryWait=2,

    [Parameter(Mandatory=$False)]
    [switch]
    $ErrorOnNotFound,

    [Parameter(ParameterSetName="Proxy", Mandatory=$True)]
    [System.Uri]
    $Proxy,

    [Parameter(ParameterSetName="Proxy", Mandatory=$False)]
    [System.Management.Automation.PSCredential]
    $ProxyCredential,

    [Parameter(ParameterSetName="Proxy", Mandatory=$False)]
    [switch]
    $ProxyUseDefaultCredentials
  )

  $AviCredentials = [AviCredentials]::new()
  $AviCredentials.Controller = $Controller
  $AviCredentials.Username = $Username
  $AviCredentials.Password = $Password
  $AviCredentials.Port = $Port
  $AviCredentials.Secure = $Secure
  $AviCredentials.ApiVersion = $ApiVersion
  $AviCredentials.Timeout = $Timeout
  $AviCredentials.RetryCount = $RetryCount
  $AviCredentials.RetryWait = $RetryWait
  $AviCredentials.Tenant = $Tenant
  $AviCredentials.TenantUUID = $TenantUUID
  $AviCredentials.Proxy = $Proxy
  $AviCredentials.ProxyCredential = $ProxyCredential
  $AviCredentials.ProxyUseDefaultCredentials = $ProxyUseDefaultCredentials

  if ($AviCredentials.Controller.StartsWith("http://") -or $AviCredentials.Controller.StartsWith("https://")) {
    $Prefix = $AviCredentials.Controller
  } else {
    if ($AviCredentials.Secure) {
      $Prefix = "https"
      if (!$AviCredentials.Port) {
        $AviCredentials.Port = 443
      }
    } else {
      $Prefix = "http"
      if (!$AviCredentials.Port) {
        $AviCredentials.Port = 80
      }
    }
    $Prefix = $Prefix + "://" + $AviCredentials.Controller
    if (($AviCredentials.Secure -and $AviCredentials.Port -ne 443) -or (!$AviCredentials.Secure -and $AviCredentials.Port -ne 80))  {
      $Prefix = $Prefix + ":" + $AviCredentials.Port
    }
  }

  $AviSession = [AviSession]::new()
  $AviSession.Credentials = $AviCredentials
  $AviSession.Prefix = $Prefix
  $AviSession.Flags = @{ErrorOnNotFound=($ErrorOnNotFound.IsPresent)}

  Initialize-AviSession $AviSession
  Write-Verbose "API session established to $($AviSession.AuthResponse.version.ProductName) version $($AviSession.AuthResponse.version.Version) build $($AviSession.AuthResponse.version.Build)"

  return $AviSession
}

<# 
  .Synopsis
  [PRIVATE] Initializes or re-initializes an API session to an Avi Vantage controller.

  .Description
  Initializes or re-initializes an API session to an Avi Vantage controller or controller cluster.

  .Parameter AviSession
  An AviSession object obtained from calling New-AviSession.    
#>
function Initialize-AviSession {
  param(
    [AviSession]
    $AviSession
  )
  
  $AuthJson = (@{username=$AviSession.Credentials.Username; password=$AviSession.Credentials.Password} | ConvertTo-Json -Compress)

  $Headers = Get-AviApiHeaders -AviSession $AviSession
  
  $Retries = $AviSession.Credentials.RetryCount

  $LoginUrl = ($AviSession.Prefix + "/login")

  while ($Retries -ge 0) {
    try {
      Write-Verbose "Starting controller login $($LoginUrl)"

      $AuthResponse = Invoke-RestMethod -Uri $LoginUrl -Method POST -Body $AuthJson -ContentType "application/json" -SessionVariable WebSession -Headers $Headers -TimeoutSec $AviSession.Credentials.Timeout -Proxy $AviSession.Credentials.Proxy -ProxyCredential $AviSession.Credentials.ProxyCredential -ProxyUseDefaultCredentials:($AviSession.Credentials.ProxyUseDefaultCredentials)
      break
    }
    catch [System.Net.WebException] {
      $ErrorRecord = $PSItem
      $Exception = $ErrorRecord.Exception
      switch ($Exception.Status) {
        "ProtocolError" {
          switch ($Exception.Response.StatusCode.value__) {
            {@(401, 419) -contains $_} {
              #Authentication failed or timed out - abort.
              $PSCmdlet.ThrowTerminatingError($ErrorRecord)
            }
            502 {
              #Gateway failure typically occurs due to a transient
              #issue with an intermediate proxy - follow retry logic.
              Write-Verbose "Gateway failure - will retry"
              break
            }
            default {
              #Some other ProtocolError occurred - abort.
              $PSCmdlet.ThrowTerminatingError($ErrorRecord)
            }
          }
          break
        }
        "Timeout" {
          #Timeout occurred - follow retry logic.
          break
        }
        default {
          #Some other unexpected error occurred - follow retry logic.
          break
        }
      }
      $Retries -= 1
      if ($Retries -lt 0) {
        $PSCmdlet.ThrowTerminatingError($ErrorRecord)
      } else {
        Write-Verbose "Retrying after $($AviSession.Credentials.RetryWait) seconds..."
        Start-Sleep -Seconds $AviSession.Credentials.RetryWait
        Write-Verbose "Retries remaining: $($Retries)"
      }
    }
  }

  $Cookies = $WebSession.Cookies.GetCookies($AviSession.Prefix)

  $SessionCookie = $Cookies["sessionid"]
  $CSRFCookie = $Cookies["csrftoken"]

  $AviSession.Credentials.CSRFToken = $CSRFCookie.Value
  $AviSession.Credentials.SessionID = $SessionCookie.Value
  $AviSession.WebSession = $WebSession
  $AviSession.LastUsed = [System.DateTime]::UtcNow
  $AviSession.AuthResponse = $AuthResponse

  Write-Verbose "Session ID=$($AviSession.Credentials.SessionID)"
  Write-Verbose "CSRF Token=$($AviSession.Credentials.CSRFToken)"
}

<# 
  .Synopsis
  [PRIVATE] Populates HTTP Headers for the session.

  .Description
  Populates HTTP Headers for the session, potentially overriding the session's default tenant or API version.

  .Parameter AviSession
  An AviSession object obtained from calling New-AviSession.
  
  .Parameter Tenant
  Override the default tenant for the API call.

  .Parameter TenantUUID
  Override the default tenantUUID for the API call.

  .Parameter ApiVersion
  Override the default Api Version for the API call.
#>
function Get-AviApiHeaders {
  param(
    [AviSession]
    $AviSession,

    [string]
    $Tenant,

    [string]
    $TenantUUID,

    [string]
    $ApiVersion
  )

  if (!$ApiVersion) {
    $ApiVersion = $AviSession.Credentials.ApiVersion
  }

  $Headers = New-Object "System.Collections.Generic.Dictionary[[String],[String]]"
  $Headers.Add("X-Avi-Version", $ApiVersion)
  $Headers.Add("Accept", "application/json")
  $Headers.Add("Referer", $AviSession.Prefix)
  if ($AviSession.Credentials.CSRFToken) {
    $Headers.Add("X-CSRFToken", $AviSession.Credentials.CSRFToken)
  }

  if ($Tenant) {
    $TenantUUID = $null
  } else {
    if ($TenantUUID) {
      $Tenant = $null
    } else {
      $Tenant = $AviSession.Credentials.Tenant
      $TenantUUID = $AviSession.Credentials.TenantUUID
    }
  }
  if ($TenantUUID) {
    $Headers.Add("X-Avi-Tenant-UUID", $TenantUUID)
  } else {
    if ($Tenant) {
      $Headers.Add("X-Avi-Tenant", $Tenant)
    }
  }
  return $Headers
}

<# 
  .Synopsis
  Invokes a REST method.

  .Description
  Invokes a REST method on the Avi Session using the provided URL.

  .Parameter AviSession
  An AviSession object obtained from calling New-AviSession.

  .Parameter Method
  The REST method to invoke (e.g. GET, PUT, POST, PATCH, DELETE).
  
  .Parameter Url
  The REST URL (can be fully-qualifed or just the API path).

  .Parameter Body
  The REST Body for methods that require it.

  .Parameter Timeout
  Override the default timeout for the API call.

  .Parameter Tenant
  Override the default tenant for the API call.

  .Parameter TenantUUID
  Override the default tenantUUID for the API call.

  .Parameter ApiVersion
  Override the default Api Version for the API call.

  .Inputs
  None. You cannot pipe objects to Invoke-AviRestMethod.

  .Outputs
  Result from invoking the specified REST API.

  .Example  
  Invoke-AviRestMethod -AviSession $Session -Method GET -Url /virtualservice

  .Example
  Invoke-AviRestMethod -AviSession $Session -Method PUT -Url $virtualservice.URL -Body $virtualservice
#>
function Invoke-AviRestMethod {
  param(
    [AviSession]
    $AviSession,
    
    [Microsoft.PowerShell.Commands.WebRequestMethod]
    $Method,
    
    [string]
    $Url,
    
    [System.Object]
    $Body,
    
    [Int32]
    $Timeout,

    [string]
    $Tenant,

    [string]
    $TenantUUID,
    
    [string]
    $ApiVersion
  )

  if ($Timeout -le 0) {
    $Timeout = $AviSession.Credentials.Timeout
  }

  $FullUrl = ($AviSession.Prefix + "/api/" + (Get-AviQualifiedUrl $Url))

  $Headers = Get-AviApiHeaders -AviSession $AviSession -Tenant $Tenant -TenantUUID $TenantUUID -ApiVersion $ApiVersion

  $Retries = $AviSession.Credentials.RetryCount
  $ReauthenticationCount = 0

  #The Body needs to be in Json format...
  if ($Body) {
    if ($Body.GetType().Name -eq "String") {
      #If $Body is a string, assume it is already in Json format
      $JsonBody = $Body
    } else {
      #Otherwise convert from PS object to Json
      $JsonBody = $Body | ConvertTo-Json -Depth 100 -Compress
    }
  }
  
  while ($Retries -ge 0) {
    if ($ReauthenticationCount -eq 1) {
      #First attempt at invocation failed due to authentiction error or
      #an underlying socket error, so try re-authenticating the session
      #using the stored credentials.
      Initialize-AviSession $AviSession
      $Headers = Get-AviApiHeaders -AviSession $AviSession -Tenant $Tenant -TenantUUID $TenantUUID -ApiVersion $ApiVersion
      $ReauthenticationCount = 2
    }
    try {
      $Response = Invoke-RestMethod -uri $FullUrl -Method $Method -WebSession $AviSession.WebSession -Headers $Headers -Body $JsonBody -ContentType "application/json" -TimeoutSec $Timeout -Proxy $AviSession.Credentials.Proxy -ProxyCredential $AviSession.Credentials.ProxyCredential -ProxyUseDefaultCredentials:($AviSession.Credentials.ProxyUseDefaultCredentials)
      #Received a valid response so break out of the retry loop
      break
    }
    catch [System.Net.WebException] {
      $ErrorRecord = $PSItem
      $Exception = $ErrorRecord.Exception
      switch ($Exception.Status) {
        "ProtocolError" {
          switch ($Exception.Response.StatusCode.value__) {
            {@(401, 419) -contains $_} {
              #Unauthorized or authentication timeout error occurred.
              if ($ReauthenticationCount -eq 0) {
                #Try reauthenticating.
                $ReauthenticationCount = 1
                Write-Verbose "Authentication failure - will try to re-authenticate"
              } else {
                #Reauthentication failed - abort.
                $PSCmdlet.ThrowTerminatingError($ErrorRecord)
              }
              break
            }
            404 {
              #Not Found either throws an error or returns NULL
              #depending on session flag ErrorOnNotFound.
              if ($AviSession.Flags["ErrorOnNotFound"]) {
                $PSCmdlet.ThrowTerminatingError($ErrorRecord)
              } else {
                Write-Verbose "404 Not Found - returning $null"
                return $null
              }
            }
            412 {
              #Typically indicates a concurrent update error - we cannot retry
              #request as the object state may be inconsistent. This condition
              #should be handled by the calling code.
              Write-Verbose "412 Precondition Failed - object state is invalid (usually due to a concurrent update); the caller should re-read the object"
              $PSCmdlet.ThrowTerminatingError($ErrorRecord)
            }
            502 {
              #Gateway failure typically occurs due to a transient
              #issue with an intermediate proxy - follow retry logic.
              Write-Verbose "502 Gateway failure - will retry"
              break
            }
            default {
              #Other ProtocolError occurred - abort.
              $PSCmdlet.ThrowTerminatingError($ErrorRecord)
            }
          }
          break
        }
        {@("SendFailure", "ReceiveFailure") -contains $_} {
          #Underlying socket error (e.g. connection reset) - try a new session
          if ($ReauthenticationCount -eq 0) {
            #Try reauthenticating.
            $ReauthenticationCount = 1
            Write-Verbose "Connection failure ($($Exception.Status)) - will try to re-establish"
          } else {
            #Reauthentication failed - abort.
            $PSCmdlet.ThrowTerminatingError($ErrorRecord)
          }
          break
        }
        "NameResolutionFailure" {
          #Name resolution failed - follow retry logic.
          Write-Verbose "Name resolution failed - will retry"
          break
        }
        "Timeout" {
          #Timeout occurred - follow retry logic.
          Write-Verbose "API request timed out - will retry"
          break
        }
        default {
          #Some other unexpected error occurred - follow retry logic.
          Write-Verbose "Error occured ($($Exception.Status)) - will retry"
          break
        }
      }
      if ($ReauthenticationCount -ne 1)
      {
        $Retries -= 1
        if ($Retries -lt 0) {
          #Max retries reached - throw the error.
          $PSCmdlet.ThrowTerminatingError($ErrorRecord)
        } else {
          #Pause before retrying.
          Write-Verbose "Retrying after $($AviSession.Credentials.RetryWait) seconds..."
          Start-Sleep -Seconds $AviSession.Credentials.RetryWait
          Write-Verbose "Retries remaining: $($Retries)"
        }
      }
    }
  }
  $AviSession.LastUsed = [System.DateTime]::UtcNow
  return $Response
}

<# 
  .Synopsis
  [PRIVATE] Extracts the API URL part.

  .Description
  Extracts the API URL part (the path after /api/) from a full or partial URL.

  .Parameter Url
  A full or partial API URL.
#>
function Get-AviQualifiedUrl {
  param(
    [string]
    $Url
  )

  if ($Url -match "(https?://[^/]*)?(/?api)?/?(.*)") {
    $Url = $Matches[3]
  }

  return $Url
}

<# 
  .Synopsis
  [PRIVATE] Converts a PS HashTable to a URI query string.

  .Description
  Converts a PS HashTable to a URI query string with escaping as needed.

  .Parameter QueryParams
  A HashTable of query parameters.
#>
function Get-AviQueryParams {
  param(
    [System.Collections.HashTable]
    $QueryParams
  )

  if ($QueryParams) {
    $QueryParamsT = @()
    foreach ($Param in $QueryParams.GetEnumerator()) {
      $QueryParamsT += ($Param.Key + "=" + [uri]::EscapeUriString($Param.Value))
    }
    return [string]::Join("&", $QueryParamsT)
  } else {
    return ""
  }
}

<# 
  .Synopsis
  Retrieves an object or collection of objects from the Avi controller.

  .Description
  Retrieves an object or collection of objects of a specific type from the Avi controller.

  .Parameter AviSession
  An AviSession object obtained from calling New-AviSession.

  .Parameter ObjectType
  The type of object to retrieve.

  .Parameter QueryParams
  A HashTable of query parameters.

  .Parameter Timeout
  Override the default timeout for the API call.

  .Parameter Tenant
  Override the default tenant for the API call.

  .Parameter TenantUUID
  Override the default tenantUUID for the API call.

  .Parameter ApiVersion
  Override the default Api Version for the API call.

  .Inputs
  None. You cannot pipe objects to Get-AviObjectsByType.

  .Outputs
  Array of objects of the specified type.

  .Example
  Get-AviObjectsByType -AviSession $Session -ObjectType virtualservice -Tenant Demo

  Retrieve all virtual service objects in the Demo tenant
#>
function Get-AviObjectsByType {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$True, Position=1)]
    [AviSession]
    $AviSession,
    
    [Parameter(Mandatory=$True, Position=2)]
    [string]
    $ObjectType,
    
    [Parameter(Mandatory=$False)]
    [System.Object]
    $QueryParams,

    [Parameter(Mandatory=$False)]
    [Int32]
    $Timeout,

    [Parameter(Mandatory=$False)]
    [string]
    $Tenant,

    [Parameter(Mandatory=$False)]
    [string]
    $TenantUUID,

    [Parameter(Mandatory=$False)]
    [string]
    $ApiVersion
  )

  $Url = $ObjectType

  if ($QueryParams) {
    $Url += ("?" + (Get-AviQueryParams $QueryParams))
  }

  $Response = Invoke-AviRestMethod -AviSession $AviSession -Url $Url -Method GET -Timeout $Timeout -Tenant $Tenant -TenantUUID $TenantUUID -ApiVersion $ApiVersion

  if ($Response) {
    return $Response.results
  } else {
    return $null
  }
}

<# 
  .Synopsis
  Retrieves an object by URL.

  .Description
  Retrieves an object or collection of objects by URL from the Avi controller.

  .Parameter AviSession
  An AviSession object obtained from calling New-AviSession.

  .Parameter Url
  A resource URL.

  .Parameter QueryParams
  A HashTable of query parameters.
  
  .Parameter Timeout
  Override the default timeout for the API call.

  .Parameter Tenant
  Override the default tenant for the API call.

  .Parameter TenantUUID
  Override the default tenantUUID for the API call.
  
  .Parameter ApiVersion
  Override the default Api Version for the API call.

  .Inputs
  None. You cannot pipe objects to Get-AviObject.

  .Outputs
  Result of specified REST API GET call.

  .Example
  Get-AviObject -AviSession $AviSession -Url /virtualservice/virtualservice-bab4bd10-e2ea-4dce-9faa-eadcc467b889 -QueryParams @{fields="pool_ref"}

  Retrieve the pool_ref field only from a specific virtual service.

  .Example
  Get-AviObject -AviSession $AviSession -Url /analytics/healthscore/virtualservice/virtualservice-bab4bd10-e2ea-4dce-9faa-eadcc467b889

  Get health score for a virtual service.

  .Example
  Get-AviSession $Session -Url /analytics/metrics/virtualservice/virtualservice-bab4bd10-e2ea-4dce-9faa-eadcc467b889 -QueryParams @{step=5; limit=12; metric_id="l4_client.avg_bandwidth"}

  Retrieve last minute's real-time metrics for a VS.
#>
function Get-AviObject {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$True, Position=1)]
    [AviSession]
    $AviSession,
    
    [Parameter(Mandatory=$True, Position=2)]
    [string]
    $Url,

    [Parameter(Mandatory=$False)]
    [System.Object]
    $QueryParams,
    
    [Parameter(Mandatory=$False)]
    [Int32]
    $Timeout,

    [Parameter(Mandatory=$False)]
    [string]
    $Tenant,

    [Parameter(Mandatory=$False)]
    [string]
    $TenantUUID,

    [Parameter(Mandatory=$False)]
    [string]
    $ApiVersion
  )

  if ($QueryParams) {
    if ($Url.Contains("?")) {
      $Url += ("&" + (Get-AviQueryParams $QueryParams))
    } else {
      $Url += ("?" + (Get-AviQueryParams $QueryParams))
    }
  }

  $Response = Invoke-AviRestMethod -AviSession $AviSession -Url $Url -Method GET -Timeout $Timeout -Tenant $Tenant -TenantUUID $TenantUUID -ApiVersion $ApiVersion

  return $Response
}

<# 
  .Synopsis
  Retrieves an object by name.

  .Description
  Retrieves an object of a specific type by name from the Avi Controller.

  .Parameter AviSession
  An AviSession object obtained from calling New-AviSession.

  .Parameter ObjectType
  The type of object to retrieve.

  .Parameter Name
  The name of the object to retrieve.

  .Parameter QueryParams
  A HashTable of query parameters.

  .Parameter Timeout
  Override the default timeout for the API call.

  .Parameter Tenant
  Override the default tenant for the API call.

  .Parameter TenantUUID
  Override the default tenantUUID for the API call.

  .Parameter AllMatches
  Returns all matching objects rather than just the first.

  .Parameter ReturnUUID
  Returns the UUID of the matching object(s) rather than the object itself.

  .Parameter ApiVersion
  Override the default Api Version for the API call.

  .Inputs
  None. You cannot pipe objects to Get-AviObjectByName.

  .Outputs
  First object matching specified name or array of all matching objects if -AllMatches specified.

  .Example
  Get-AviObjectByName -AviSession $Session -ObjectType virtualservice -Name avi-example-vs -Tenant Demo

  Retrieve virtual service named "avi-example-vs" in tenant "Demo".

  .Example
  Get-AviObjectByName -AviSession $Session -ObjectType virtualservice -Name avi-example-vs -AllMatches

  Retrieve all virtual services named "avi-example-vs" in all accessible tenants.

  .Example
  Get-AviObjectByName -AviSession $Session -ObjectType virtualservice -Name avi-example-vs -ReturnUUID

  Retrieve the UUID of the service named "avi-example-vs".
#>
function Get-AviObjectByName {
  [CmdletBinding()]
  param(
    
    [Parameter(Mandatory=$True, Position=1)]
    [AviSession]
    $AviSession,
    
    [Parameter(Mandatory=$True, Position=2)]
    [string]
    $ObjectType,
    
    [Parameter(Mandatory=$True, Position=3)]
    [string]
    $Name,

    [Parameter(Mandatory=$False)]
    [System.Object]
    $QueryParams,
    
    [Parameter(Mandatory=$False)]
    [Int32]
    $Timeout=0,

    [Parameter(Mandatory=$False)]
    [string]
    $Tenant,

    [Parameter(Mandatory=$False)]
    [string]
    $TenantUUID,

    [Parameter(Mandatory=$False)]
    [switch]
    $AllMatches,
    
    [Parameter(Mandatory=$False)]
    [switch]
    $ReturnUUID,

    [Parameter(Mandatory=$False)]
    [string]
    $ApiVersion
  )

  $Url = ($ObjectType + "?name=" + $Name)

  if ($ReturnUUID) {
    $Url += "&fields="
  }

  if ($QueryParams) {
    $QueryParams.Remove("name")
    if ($ReturnUUID) {
      $QueryParams.Remove("fields")
    }
    $Url += ("&" + (Get-AviQueryParams $QueryParams))
  }
  
  $Response = Invoke-AviRestMethod -AviSession $AviSession -Url $Url -Method GET -Timeout $Timeout -Tenant $Tenant -TenantUUID $TenantUUID -ApiVersion $ApiVersion

  if ($Response) {
    if ($AllMatches) {
      Write-Verbose "Returning $($Response.count) result(s)"
      $Results = $Response.results
    } else {
      Write-Verbose "Returning result 1 of $($Response.count)"
      $Results = $Response.results[0]
    }
    if ($ReturnUUID) {
      return $Results.uuid
    } else {
      return $Results
    }
  } else {
    return $null
  }
}

<# 
  .Synopsis
  Deletes an object (REST DELETE).

  .Description
  Deletes an object of a specific type by name from the Avi Controller.

  .Parameter AviSession
  An AviSession object obtained from calling New-AviSession.

  .Parameter UrlObjectType
  The Url of the object to delete.

  .Parameter Timeout
  Override the default timeout for the API call.

  .Parameter Tenant
  Override the default tenant for the API call.

  .Parameter TenantUUID
  Override the default tenantUUID for the API call.

  .Parameter ApiVersion
  Override the default Api Version for the API call.

  .Inputs
  None. You cannot pipe objects to Remove-AviObject.

  .Outputs
  Result of REST DELETE API call.

  .Example
  Remove-AviObject -AviSession $Session -Url /virtualservice/virtualservice-bab4bd10-e2ea-4dce-9faa-eadcc467b889

  Deletes the specified virtual service.

  .Example
  Remove-AviObject -AviSession $Session -Url $VirtualService.Url

  Deletes the virtual service previously retrieved and held in the $VirtualService variable.
#>
function Remove-AviObject {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$True, Position=1)]
    [AviSession]
    $AviSession,
    
    [Parameter(Mandatory=$True, Position=2)]
    [string]
    $Url,

    [Parameter(Mandatory=$False)]
    [System.Object]
    $ObjectData,
    
    [Parameter(Mandatory=$False)]
    [Int32]
    $Timeout,

    [Parameter(Mandatory=$False)]
    [string]
    $Tenant,

    [Parameter(Mandatory=$False)]
    [string]
    $TenantUUID,

    [Parameter(Mandatory=$False)]
    [string]
    $ApiVersion
  )

  $Response = Invoke-AviRestMethod -AviSession $AviSession -Url $Url -Method DELETE -Body $ObjectData -Timeout $Timeout -Tenant $Tenant -TenantUUID $TenantUUID -ApiVersion $ApiVersion
  
  return $Response
}

<# 
  .Synopsis
  Update an existing object (REST PUT).

  .Description
  Updates an existing object using a REST PUT. If the object does not have a valid URL property, a new object will be created instead.

  .Parameter AviSession
  An AviSession object obtained from calling New-AviSession.

  .Parameter Object
  The object to set.

  .Parameter Timeout
  Override the default timeout for the API call.
 
  .Parameter Tenant
  Override the default tenant for the API call.

  .Parameter TenantUUID
  Override the default tenantUUID for the API call.

  .Parameter ApiVersion
  Override the default Api Version for the API call.

  .Inputs
  None. You cannot pipe objects to Set-AviObject.

  .Outputs
  Result of REST PUT API call.

  .Example
  Set-AviObject -AviSession $Session -Object $VirtualService

  Updates the virtual service object held in $VirtualService.
#>
function Set-AviObject {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$True, Position=1)]
    [AviSession]
    $AviSession,
    
    [Parameter(Mandatory=$True, Position=2)]
    [System.Object]
    $Object,

    [Parameter(Mandatory=$False)]
    [string]
    $Url,

    [Parameter(Mandatory=$False)]
    [System.Object]
    $QueryParams,
        
    [Parameter(Mandatory=$False)]
    [Int32]
    $Timeout=0,

    [Parameter(Mandatory=$False)]
    [string]
    $Tenant,

    [Parameter(Mandatory=$False)]
    [string]
    $TenantUUID,

    [Parameter(Mandatory=$False)]
    [string]
    $ApiVersion
  )

  if ($Url) {
    $Object.Url = $null
  } else {
    $Url = $Object.Url
  }

  if ($QueryParams) {
    $Url += ("?" + (Get-AviQueryParams $QueryParams))
  }

  $Response = Invoke-AviRestMethod -AviSession $AviSession -Url $Url -Method PUT -Body $Object -Timeout $Timeout -Tenant $Tenant -TenantUUID $TenantUUID -ApiVersion $ApiVersion

  return $Response
}

<# 
  .Synopsis
  Create a new object (REST POST).

  .Description
  Creates a new object using a REST POST.

  .Parameter AviSession
  An AviSession object obtained from calling New-AviSession.

  .Parameter ObjectType
  The type of object to be created.

  .Parameter ObjectData
  The data of the object to be created.

  .Parameter QueryParams
  A HashTable of query parameters.

  .Parameter Timeout
  Override the default timeout for the API call.
 
  .Parameter Tenant
  Override the default tenant for the API call.

  .Parameter TenantUUID
  Override the default tenantUUID for the API call.

  .Parameter ApiVersion
  Override the default Api Version for the API call.

  .Inputs
  None. You cannot pipe objects to New-AviObject.

  .Outputs
  Result of REST POST API call.

  .Example
  New-AviObject -AviSession $Session -ObjectType virtualservice -ObjectData $VirtualServiceData

  Creates a new virtual service. $VirtualServiceData holds the VS configuration in PowerShell HashTable object format.
#>
function New-AviObject {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$True, Position=1)]
    [AviSession]
    $AviSession,
    
    [Parameter(Mandatory=$True, Position=2)]
    [string]
    $ObjectType,

    [Parameter(Mandatory=$True, Position=3)]
    [System.Object]
    $ObjectData,

    [Parameter(Mandatory=$False)]
    [System.Object]
    $QueryParams,
        
    [Parameter(Mandatory=$False)]
    [Int32]
    $Timeout=0,

    [Parameter(Mandatory=$False)]
    [string]
    $Tenant,

    [Parameter(Mandatory=$False)]
    [string]
    $TenantUUID,

    [Parameter(Mandatory=$False)]
    [string]
    $ApiVersion
  )

  $Url = $ObjectType

  if ($QueryParams) {
    $Url += ("?" + (Get-AviQueryParams $QueryParams))
  }

  $Response = Invoke-AviRestMethod -AviSession $AviSession -Url $Url -Method POST -Body $ObjectData -Timeout $Timeout -Tenant $Tenant -TenantUUID $TenantUUID -ApiVersion $ApiVersion

  return $Response
}

<# 
  .Synopsis
  Edits an existing object (REST PATCH).

  .Description
  Updates an existing object using a REST PATCH.

  .Parameter AviSession
  An AviSession object obtained from calling New-AviSession.

  .Parameter Url
  The URL of the object to be edited.

  .Parameter ObjectData
  The data to be updated.

  .Parameter PatchOperation
  The patch operation (if missing, the patch operation must be specified in the object data.

  .Parameter Timeout
  Override the default timeout for the API call.
 
  .Parameter Tenant
  Override the default tenant for the API call.

  .Parameter TenantUUID
  Override the default tenantUUID for the API call.

  .Parameter ApiVersion
  Override the default Api Version for the API call.

  .Inputs
  None. You cannot pipe objects to Edit-AviObject.

  .Outputs
  Result of REST PATCH API call.

  .Example
  Set-AviObject -AviSession $Session -Object $VirtualService
#>
function Edit-AviObject {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$True, Position=1)]
    [AviSession]
    $AviSession,
    
    [Parameter(Mandatory=$True, Position=2)]
    [string]
    $Url,

    [Parameter(Mandatory=$True, Position=3)]
    [System.Object]
    $ObjectData,

    [Parameter(Mandatory=$False)]
    [string]
    $PatchOperation,

    [Parameter(Mandatory=$False)]
    [System.Object]
    $QueryParams,
        
    [Parameter(Mandatory=$False)]
    [Int32]
    $Timeout=0,

    [Parameter(Mandatory=$False)]
    [string]
    $Tenant,

    [Parameter(Mandatory=$False)]
    [string]
    $TenantUUID,

    [Parameter(Mandatory=$False)]
    [string]
    $ApiVersion
  )

  if ($QueryParams) {
    if ($Url.Contains("?")) {
      $Url += ("&" + (Get-AviQueryParams $QueryParams))
    } else {
      $Url += ("?" + (Get-AviQueryParams $QueryParams))
    }
  }

  if ($PatchOperation) {
    $ObjectData = (@{$PatchOperation=$ObjectData})
    Write-Host ($ObjectData | ConvertTo-Json)
  }
  
  $Response = Invoke-AviRestMethod -AviSession $AviSession -Url $Url -Method PATCH -Body $ObjectData -Timeout $Timeout -Tenant $Tenant -TenantUUID $TenantUUID -ApiVersion $ApiVersion

  return $Response
}

<# 
  .Synopsis
  Suppresses certificate warnings.

  .Description
  Suppresses certificate warnings, for example due to self-signed certificates. 

  .Example
  Disable-AviCertificateWarnings
#>
function Disable-AviCertificateWarnings {
  [CmdletBinding()]
  param()
  [System.Net.ServicePointManager]::ServerCertificateValidationCallback={$True}
  Write-Verbose "Certificate errors will be ignored"
}