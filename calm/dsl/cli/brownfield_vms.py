import sys
import click
from prettytable import PrettyTable

from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.log import get_logging_handle
from .utils import highlight_text

LOG = get_logging_handle(__name__)


def get_provider_account_from_project(project_name, provider_type):
    """
    Returns tuple containing project_uuid and account_uuid of provider_account registered in project
    i.e (project_uuid, account_uuid)
    """

    client = get_api_client()

    # Getting the account uuid map
    params = {"length": 250, "filter": "state!=DELETED;type=={}".format(provider_type)}
    account_uuid_type_map = client.account.get_uuid_type_map(params)
    provider_account_uuids = list(account_uuid_type_map.keys())

    params = {"length": 250, "filter": "name=={}".format(project_name)}
    res, err = client.project.list(params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    if res["metadata"]["total_matches"] == 0:
        LOG.error("Project {} not found".format(project_name))
        sys.exit(-1)

    pj_data = res["entities"][0]
    account_list = pj_data["status"]["resources"]["account_reference_list"]
    project_uuid = pj_data["metadata"]["uuid"]
    account_uuid = ""
    for account in account_list:
        if account["uuid"] in provider_account_uuids:
            account_uuid = account["uuid"]

    # If provider acount not found raise error
    if not account_uuid:
        LOG.error(
            "No {} account registered to project {}".format(provider_type, project_name)
        )
        sys.exit(-1)
    else:
        return (project_uuid, account_uuid)


def get_brownfield_ahv_vm_list(limit, offset, quiet, out, project_name):
    """returns ahv brownfield vms"""

    client = get_api_client()

    # Getting provider account_uuid registered in project
    LOG.info("Fetching project '{}' details".format(project_name))
    project_uuid, account_uuid = get_provider_account_from_project(
        project_name, "nutanix_pc"
    )

    LOG.info("Fetching account(uuid={}) details".format(account_uuid))
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

    LOG.info("Fetching brownfield vms")
    Obj = get_resource_api("blueprints/brownfield_import/vms", client.connection)
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
        "ID",
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


def get_brownfield_aws_vm_list(limit, offset, quiet, out, project_name):
    """returns aws brownfield vms"""

    client = get_api_client()

    # Getting provider account_uuid registered in project
    LOG.info("Fetching project '{}' details".format(project_name))
    project_uuid, account_uuid = get_provider_account_from_project(project_name, "aws")

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

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(
            highlight_text(
                "No aws brownfield vm on account(uuid={}) found !!!\n".format(
                    account_uuid
                )
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
        "PUBLIC IP ADDRESS",
        "PRIVATE DNS",
        "PUBLIC DNS",
        "REGION",
        "POWER STATE",
        "ID",
    ]

    for row in json_rows:

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


def get_brownfield_azure_vm_list(limit, offset, quiet, out, project_name):
    """returns azure brownfield vms"""

    client = get_api_client()

    # Getting provider account_uuid registered in project
    LOG.info("Fetching project '{}' details".format(project_name))
    project_uuid, account_uuid = get_provider_account_from_project(
        project_name, "azure"
    )

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

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(
            highlight_text(
                "No azure brownfield vm on account(uuid={}) found !!!\n".format(
                    account_uuid
                )
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
        "RESOURCE GROUP",
        "LOCATION",
        "PUBLIC IP",
        "PRIVATE IP",
        "HARDWARE PROFILE",
        "ID",
    ]

    for row in json_rows:

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


def get_brownfield_gcp_vm_list(limit, offset, quiet, out, project_name):
    """returns gcp brownfield vms"""

    client = get_api_client()

    # Getting provider account_uuid registered in project
    LOG.info("Fetching project '{}' details".format(project_name))
    project_uuid, account_uuid = get_provider_account_from_project(project_name, "gcp")

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

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(
            highlight_text(
                "No azure brownfield vm on account(uuid={}) found !!!\n".format(
                    account_uuid
                )
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
        "ZONE",
        "SUBNETS",
        "NETWORK",
        "NAT IP",
        "NETWORK NAME",
        "ID",
    ]

    for row in json_rows:

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


def get_brownfield_vmware_vm_list(limit, offset, quiet, out, project_name):
    """returns vmware brownfield vms"""

    client = get_api_client()

    # Getting provider account_uuid registered in project
    LOG.info("Fetching project '{}' details".format(project_name))
    project_uuid, account_uuid = get_provider_account_from_project(project_name, "gcp")

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

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(
            highlight_text(
                "No vmware brownfield vm on account(uuid={}) found !!!\n".format(
                    account_uuid
                )
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
        "HOSTNAME",
        "IP ADDRESS",
        "VCPU",
        "CORES PER VCPU",
        "MEMORY (GIB)",
        "GUEST FAMILY",
        "TEMPLATE",
        "ID",
    ]

    for row in json_rows:

        # Status section
        st_resources = row["status"]["resources"]

        instance_id = st_resources["instance_id"]
        instance_name = st_resources["instance_name"]
        hostname = st_resources["guest.hostName"]
        address = ",".join(st_resources["guest.ipAddress"])
        vcpus = st_resources["config.hardware.numCPU"]
        sockets = st_resources["config.hardware.numCoresPerSocket"]
        memory = int(st_resources["config.hardware.memoryMB"]) // 1024
        guest_family = st_resources["guest.guestFamily"]
        template = st_resources["config.template"]

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
