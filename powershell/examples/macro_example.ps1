Import-Module AviSDK

#Disable certificate errors if self-signed cert is being used
Disable-AviCertificateWarnings

$AviSession = New-AviSession -Controller controller.avi.local -Username admin -Password password123 -ApiVersion 18.2.8

#Use the macro API to configure a VS, pool and health monitor in one
#call to New-AviObject
$MacroVS = @{
  model_name="VirtualService";
  data=@{
    name="rc-example-vs";
    services=@(@{port=80});
    vsvip_ref_data=@{
      name="vsvip-rc-example-vs";
      vip=@(
        @{vip_id=0;
          ip_address=@{
            type="V4";
            addr="1.2.3.4"
          }
        }
      )
    };
    application_profile_ref="/api/applicationprofile?name=System-HTTP";
    pool_ref_data=@{
      name="rc-example-vs-pool";
      servers=@(
        @{hostname="server01"; ip=@{type="V4"; addr="10.20.20.1"}};
        @{hostname="server02"; ip=@{type="V4"; addr="10.20.20.2"}}
      )
    };
    health_monitor_refs_data=@(@{
        type="HEALTH_MONITOR_HTTP";
        name="rc-example-http-mon";
        http_monitor=@{
          http_response_code=@(@{code="HTTP_2xx"})
        }
      }
    )
  }
}

$MacroObject = New-AviObject -AviSession $AviSession -ObjectType macro -ObjectData $MacroVS -Verbose

#Delete the VS and unique child objects using macro DELETE
#(in this example, we obtain the VS UUID from the VS created by the above macro)
$MacroVS = $MacroObject | Where-Object {$_.name -eq "rc-example-vs"}

$MacroVSRemove = @{
  model_name="VirtualService";
  data=@{
    uuid=$MacroVS.uuid
  }
}

$Result = Remove-AviObject -AviSession $AviSession -Url macro -ObjectData $MacroVSRemove
