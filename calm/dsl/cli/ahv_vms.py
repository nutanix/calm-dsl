import json

import click
from prettytable import PrettyTable

from calm.dsl.config import get_config
from calm.dsl.api import get_api_client
from calm.dsl.tools import get_logging_handle

from .utils import highlight_text

LOG = get_logging_handle(__name__)


def get_ahv_vm_list(limit, offset, quiet):

    client = get_api_client()

    params = {"length": limit, "offset": offset}
    res, err = client.ahv_vm.list(params=params)

    if err:
        config = get_config()
        pc_ip = config["SERVER"]["pc_ip"]
        LOG.warning("Cannot fetch ahv_vms from {}".format(pc_ip))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No ahv_vm found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "HOST",
        "PROJECT",
        "OWNER",
        "HYPERVISOR",
        "MEMORY CAPACITY (GiB)",
        "IP ADDRESSES",
        "POWER STATE",
        "CLUSTER",
    ]

    for row in json_rows:

        # Metadata section
        metadata = row["metadata"]

        project = None
        if "project_reference" in metadata:
            project = metadata["project_reference"]["name"]

        owner = None
        if "owner_reference" in metadata:
            owner = metadata["owner_reference"]["name"]

        # Status section
        status = row["status"]

        cluster = None
        if "cluster_reference" in status:
            cluster = status["cluster_reference"]["name"]

        name = None
        if "name" in status:
            name = status["name"]

        # Resources section
        resources = status["resources"]

        host = None
        if "host_reference" in resources:
            host = resources["host_reference"]["name"]

        hypervisor = None
        if "hypervisor_type" in resources:
            hypervisor = resources["hypervisor_type"]

        memory_capacity = None
        if "memory_size_mib" in resources:
            try:
                memory_capacity = int(resources["memory_size_mib"]) // 1024
            except:
                pass

        ip_address = None
        if "nic_list" in resources:
            nic_list = resources["nic_list"]
            try:
                # ToDo - get all IPs
                ip_address = nic_list[0]["ip_endpoint_list"][0]["ip"]
            except:
                pass

        power_state = None
        if "power_state" in resources:
            power_state = resources["power_state"]

        table.add_row(
            [
                highlight_text(name),
                highlight_text(host),
                highlight_text(project),
                highlight_text(owner),
                highlight_text(hypervisor),
                highlight_text(memory_capacity),
                highlight_text(ip_address),
                highlight_text(power_state),
                highlight_text(cluster),
            ]
        )

    click.echo(table)
