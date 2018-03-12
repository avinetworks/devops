Import-Module AviSDK

#Disable certificate errors if self-signed cert is being used
Disable-AviCertificateWarnings

$AviSession = New-AviSession -Controller controller.avi.local -Username admin -Password password123

#Get a pool object by name
$AviPool = Get-AviObjectByName -AviSession $AviSession -ObjectType pool -Name rc-demo-pool

#Disable pool members
foreach ($Server in $AviPool.servers) {
  $Server.enabled = $False
}

#Add a new pool member
$NewServer = @{hostname="server01"; ip=@{type="V4"; addr="10.20.20.1"}}
$AviPool.servers  += $NewServer

#Update the pool object (REST PUT)
$AviPool = Set-AviObject -AviSession $AviSession -Object $AviPool

#Use PATCH function to remove a pool member with patch operation in object data
$AviPoolPatched = Edit-AviObject -AviSession $AviSession -Url $AviPool.Url -ObjectData (@{delete=@{servers=@($NewServer)}})

#Use PATCH function to disable a VS (need VS UUID) specifying patch operation
$AviVS = Edit-AviObject -AviSession $AviSession -Url "virtualservice/virtualservice-50735f52-6c4e-4bc4-b41d-08b0a641bf8f" -PatchOperation replace -ObjectData (@{enabled=$False})

#Create a new pool object (REST POST)
$NewPool = @{
  name="rc-powershell-01-pool";
  lb_algorithm="LB_ALGORITHM_LEAST_CONNECTIONS";
  default_server_port=80;
  servers=@(@{hostname="server01"; ip=@{type="V4"; addr="10.20.20.1"}};
            @{hostname="server02"; ip=@{type="V4"; addr="10.20.20.2"}})
}

$NewPool = New-AviObject -AviSession $AviSession -ObjectType pool -ObjectData $NewPool

#Get specific fields from an object
$PoolServers = Get-AviObjectByName -AviSession $AviSession -ObjectType pool -Name rc-powershell-01-pool -QueryParams @{fields="servers,default_server_port"}

#Delete the pool object (REST DELETE)

$Response = Remove-AviObject -AviSession $AviSession -Url $NewPool.Url

#Retrieve the last minute's real-time metric data for average client bandwidth for a VS
$Metrics = Get-AviObject -AviSession $AviSession -Url /analytics/metrics/virtualservice/virtualservice-bab4bd10-e2ea-4dce-9faa-eadcc467b889 -QueryParams @{step=5; limit=12; metric_id="l4_client.avg_bandwidth"}

#Retrieve current healthscore for a VS
$HealthScore = (Get-AviObject -AviSession $AviSession -Url /analytics/healthscore/virtualservice/virtualservice-bab4bd10-e2ea-4dce-9faa-eadcc467b889).series.data.value

#Retrieve virtual services that use the System-HTTP application profile
$SystemHTTP = (Get-AviObjectByName -AviSession $AviSession -ObjectType applicationprofile -Name System-HTTP -QueryParams @{fields=""}).uuid
$VSList = Get-AviObjectsByType -AviSession $AviSession -ObjectType virtualservice -QueryParams @{refers_to="applicationprofile:$($SystemHTTP)"}
