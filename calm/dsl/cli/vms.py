import json
import sys
import click
from ruamel import yaml
import arrow
import click
from prettytable import PrettyTable

from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.config import get_config
from calm.dsl.store import Cache
from calm.dsl.log import get_logging_handle

from .utils import highlight_text

LOG = get_logging_handle(__name__)


def get_ahv_vm_list(limit, offset, quiet, out):

    client = get_api_client()

    params = {"length": limit, "offset": offset}
    Obj = get_resource_api("vms", client.connection)
    res, err = Obj.list(params=params)

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
        "UUID",
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

        vm_uuid = None
        if "uuid" in metadata:
            vm_uuid = metadata["uuid"]

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
                highlight_text(vm_uuid),
            ]
        )

    click.echo(table)


def get_brownfield_ahv_vm_list(limit, offset, quiet, out):

    client = get_api_client()
    Obj = get_resource_api("blueprints/brownfield_import/vms", client.connection)

    config = get_config()
    project_name = config["PROJECT"]["name"]
    project_cache_data = Cache.get_entity_data(entity_type="project", name=project_name)

    if not project_cache_data:
        LOG.error(
            "Project {} not found. Please run: calm update cache".format(project_name)
        )
        sys.exit(-1)

    project_accounts = project_cache_data["accounts_data"]
    project_subnets = project_cache_data["whitelisted_subnets"]
    # Fetch Nutanix_PC account registered
    project_uuid = project_cache_data["uuid"]
    account_uuid = project_accounts.get("nutanix_pc", "")

    if not account_uuid:
        LOG.error("No nutanix account registered to project {}".format(project_name))
        sys.exit(-1)

    res, err = client.account.read(account_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    clusters = res["status"]["resources"]["data"].get(
        "cluster_account_reference_list", []
    )
    if not clusters:
        LOG.error("No cluster found in ahv account (uuid='{}')".format(account_uuid))
        sys.exit(-1)

    cluster_uuid = clusters[0]["uuid"]

    filter_query = "project_uuid=={};account_uuid=={}".format(
        project_uuid, cluster_uuid
    )
    params = {"length": limit, "offset": offset, "filter": filter_query}
    res, err = Obj.list(params=params)
    if err:
        LOG.error(err)
        sys.exit(-1)

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(
            highlight_text(
                "No ahv_vm on account(uuid={}) found !!!\n".format(account_uuid)
            )
        )
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "CLUSTER",
        "SUBNET",
        "ADDRESS",
        "MEMORY",
        "SOCKETS",
        "VCPU",
        "UUID",
    ]

    for row in json_rows:

        # Status section
        st_resources = row["status"]["resources"]

        cluster = st_resources["cluster_name"]
        subnet = st_resources["subnet_list"]
        address = ",".join(st_resources["address_list"])
        memory = st_resources["memory_size_mib"] // 1024
        sockets = st_resources["num_sockets"]
        vcpus = st_resources["num_vcpus_per_socket"]
        instance_id = st_resources["instance_id"]
        instance_name = st_resources["instance_name"]

        table.add_row(
            [
                highlight_text(instance_name),
                highlight_text(cluster),
                highlight_text(subnet),
                highlight_text(address),
                highlight_text(memory),
                highlight_text(sockets),
                highlight_text(vcpus),
                highlight_text(instance_id),
            ]
        )

    click.echo(table)
