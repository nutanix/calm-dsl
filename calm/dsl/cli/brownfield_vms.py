import sys
import json
import click
import json
from prettytable import PrettyTable
from distutils.version import LooseVersion as LV

from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.constants import PROVIDER_ACCOUNT_TYPE_MAP
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Version
from .utils import highlight_text, get_account_details

LOG = get_logging_handle(__name__)


def get_brownfield_ahv_vm_list(entity_rows):
    """displays ahv brownfield vms"""

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "CLUSTER",
        "SUBNET",
        "ADDRESS",
        "MEMORY",
        "SOCKETS",
        "VCPU",
        "ID",
    ]

    for row in entity_rows:

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


def get_brownfield_aws_vm_list(entity_rows):
    """displays aws brownfield vms"""

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "PUBLIC IP ADDRESS",
        "PRIVATE DNS",
        "PUBLIC DNS",
        "REGION",
        "POWER STATE",
        "ID",
    ]

    for row in entity_rows:

        # Status section
        st_resources = row["status"]["resources"]

        address = ",".join(st_resources["public_ip_address"])
        private_dns_name = st_resources["private_dns_name"]
        public_dns_name = ",".join(st_resources["public_dns_name"])
        region = ",".join(st_resources["region"])
        power_state = st_resources["power_state"]
        instance_id = st_resources["instance_id"]
        instance_name = st_resources["instance_name"]

        table.add_row(
            [
                highlight_text(instance_name),
                highlight_text(address),
                highlight_text(private_dns_name),
                highlight_text(public_dns_name),
                highlight_text(region),
                highlight_text(power_state),
                highlight_text(instance_id),
            ]
        )

    click.echo(table)


def get_brownfield_azure_vm_list(entity_rows):
    """displays azure brownfield vms"""

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "RESOURCE GROUP",
        "LOCATION",
        "PUBLIC IP",
        "PRIVATE IP",
        "HARDWARE PROFILE",
        "ID",
    ]

    for row in entity_rows:

        # Status section
        st_resources = row["status"]["resources"]

        instance_id = st_resources["instance_id"]
        instance_name = st_resources["instance_name"]
        resource_group = st_resources["resource_group"]
        location = st_resources["location"]
        public_ip = st_resources["public_ip_address"]
        private_ip = st_resources["private_ip_address"]
        hardwareProfile = (
            st_resources["properties"].get("hardwareProfile", {}).get("vmSize", "")
        )

        table.add_row(
            [
                highlight_text(instance_name),
                highlight_text(resource_group),
                highlight_text(location),
                highlight_text(public_ip),
                highlight_text(private_ip),
                highlight_text(hardwareProfile),
                highlight_text(instance_id),
            ]
        )

    click.echo(table)


def get_brownfield_gcp_vm_list(entity_rows):
    """displays gcp brownfield vms"""

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "ZONE",
        "SUBNETS",
        "NETWORK",
        "NAT IP",
        "NETWORK NAME",
        "ID",
    ]

    for row in entity_rows:

        # Status section
        st_resources = row["status"]["resources"]

        instance_id = st_resources["id"]
        instance_name = st_resources["instance_name"]
        zone = st_resources["zone"]
        subnetwork = st_resources["subnetwork"]
        network = st_resources["network"]
        natIP = ",".join(st_resources["natIP"])
        network_name = ",".join(st_resources["network_name"])

        table.add_row(
            [
                highlight_text(instance_name),
                highlight_text(zone),
                highlight_text(subnetwork),
                highlight_text(network),
                highlight_text(natIP),
                highlight_text(network_name),
                highlight_text(instance_id),
            ]
        )

    click.echo(table)


def get_vmware_vm_data_with_version_filtering(vm_data):
    """returns instance_data_according_to_version_filter"""

    CALM_VERSION = Version.get_version("Calm")

    instance_id = vm_data["instance_id"]
    instance_name = vm_data["instance_name"]

    if LV(CALM_VERSION) >= LV("3.3.0"):
        hostname = vm_data["guest_hostname"]
        address = ",".join(vm_data["guest_ipaddress"])
        vcpus = vm_data["cpu"]
        sockets = vm_data["num_vcpus_per_socket"]
        memory = int(vm_data["memory"]) // 1024
        guest_family = vm_data.get("guest_family", "")
        template = vm_data.get("is_template", False)

    else:
        hostname = vm_data["guest.hostName"]
        address = ",".join(vm_data["guest.ipAddress"])
        vcpus = vm_data["config.hardware.numCPU"]
        sockets = vm_data["config.hardware.numCoresPerSocket"]
        memory = int(vm_data["config.hardware.memoryMB"]) // 1024
        guest_family = vm_data.get("guest.guestFamily", "")
        template = vm_data.get("config.template", False)

    return (
        instance_id,
        instance_name,
        hostname,
        address,
        vcpus,
        sockets,
        memory,
        guest_family,
        template,
    )


def get_brownfield_vmware_vm_list(entity_rows):
    """displays vmware brownfield vms"""

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "HOSTNAME",
        "IP ADDRESS",
        "VCPU",
        "CORES PER VCPU",
        "MEMORY (GIB)",
        "GUEST FAMILY",
        "TEMPLATE",
        "ID",
    ]

    for row in entity_rows:

        # Status section
        st_resources = row["status"]["resources"]
        (
            instance_id,
            instance_name,
            hostname,
            address,
            vcpus,
            sockets,
            memory,
            guest_family,
            template,
        ) = get_vmware_vm_data_with_version_filtering(st_resources)

        table.add_row(
            [
                highlight_text(instance_name),
                highlight_text(hostname),
                highlight_text(address),
                highlight_text(vcpus),
                highlight_text(sockets),
                highlight_text(memory),
                highlight_text(guest_family),
                highlight_text(template),
                highlight_text(instance_id),
            ]
        )

    click.echo(table)


def get_brownfield_vms(
    limit, offset, quiet, out, project_name, provider_type, account_name
):
    """displays brownfield vms for a provider"""

    client = get_api_client()

    account_detail = get_account_details(
        project_name=project_name,
        account_name=account_name,
        provider_type=provider_type,
        pe_account_needed=True,
    )
    project_uuid = account_detail["project"]["uuid"]
    account_name = account_detail["account"]["name"]
    account_uuid = account_detail["account"]["uuid"]

    LOG.info("Using account '{}' for listing brownfield vms".format(account_name))

    LOG.info("Fetching brownfield vms")
    Obj = get_resource_api("blueprints/brownfield_import/vms", client.connection)
    filter_query = "project_uuid=={};account_uuid=={}".format(
        project_uuid, account_uuid
    )
    params = {"length": limit, "offset": offset, "filter": filter_query}
    res, err = Obj.list(params=params)
    if err:
        LOG.error(err)
        sys.exit(-1)

    if out == "json":
        click.echo(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(
            highlight_text(
                "No brownfield {} found on account '{}' !!!\n".format(
                    provider_type, account_name
                )
            )
        )
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    if provider_type == "AHV_VM":
        get_brownfield_ahv_vm_list(json_rows)
    elif provider_type == "AWS_VM":
        get_brownfield_aws_vm_list(json_rows)
    elif provider_type == "AZURE_VM":
        get_brownfield_azure_vm_list(json_rows)
    elif provider_type == "GCP_VM":
        get_brownfield_gcp_vm_list(json_rows)
    elif provider_type == "VMWARE_VM":
        get_brownfield_vmware_vm_list(json_rows)
