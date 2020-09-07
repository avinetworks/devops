import datetime
import logging
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from msrestazure.azure_active_directory import MSIAuthentication
import os
import azure.functions as func


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')


    credentials = MSIAuthentication()

    compute_client = ComputeManagementClient(credentials, "0eebbbed-14c0-462e-99e0-dfec1d42e0c9")

    def poweroff_vm(logging):
        for vm in compute_client.virtual_machines.list('rahulr-resource-group'):
            logging.info("Deallocating VM %s"%vm.name)
            compute_client.virtual_machines.deallocate('rahulr-resource-group',vm.name)
    poweroff_vm(logging)


    logging.info('Python timer trigger function ran at %s', utc_timestamp)
