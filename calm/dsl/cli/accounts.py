import time
import click
import arrow
import sys
from prettytable import PrettyTable
from distutils.version import LooseVersion as LV

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.config import get_context

from .utils import get_name_query, get_states_filter, highlight_text
from .constants import ACCOUNT
from calm.dsl.store import Version
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def get_accounts(name, filter_by, limit, offset, quiet, all_items, account_type):
    """ Get the accounts, optionally filtered by a string """

    client = get_api_client()
    calm_version = Version.get_version("Calm")

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if account_type:
        filter_query += ";(type=={})".format(",type==".join(account_type))
    if all_items:
        filter_query += get_states_filter(ACCOUNT.STATES)

    # Remove PE accounts for versions >= 2.9.0 (TODO move to constants)
    if LV(calm_version) >= LV("2.9.0"):
        filter_query += ";type!=nutanix"

    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.account.list(params)

    if err:
        ContextObj = get_context()
        server_config = ContextObj.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch accounts from {}".format(pc_ip))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No account found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "ACCOUNT TYPE",
        "STATE",
        "OWNER",
        "CREATED ON",
        "LAST UPDATED",
        "UUID",
    ]

    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        creation_time = int(metadata["creation_time"]) // 1000000
        last_update_time = int(metadata["last_update_time"]) // 1000000
        if "owner_reference" in metadata:
            owner_reference_name = metadata["owner_reference"]["name"]
        else:
            owner_reference_name = "-"

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["resources"]["type"]),
                highlight_text(row["resources"]["state"]),
                highlight_text(owner_reference_name),
                highlight_text(time.ctime(creation_time)),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(metadata["uuid"]),
            ]
        )
    click.echo(table)


def get_account(client, account_name):

    params = {"filter": "name=={}".format(account_name)}
    res, err = client.account.list(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    account = None
    if entities:
        if len(entities) != 1:
            raise Exception("More than one account found - {}".format(entities))

        LOG.info("{} found ".format(account_name))
        account = entities[0]
    else:
        raise Exception("No account having name {} found".format(account_name))

    account_id = account["metadata"]["uuid"]
    LOG.info("Fetching account details")
    res, err = client.account.read(account_id)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    account = res.json()
    return account


def delete_account(account_names):

    client = get_api_client()
    for account_name in account_names:
        account = get_account(client, account_name)
        account_id = account["metadata"]["uuid"]
        res, err = client.account.delete(account_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        LOG.info("Account {} deleted".format(account_name))


def describe_showback_data(spec):

    cost_items = spec[0]["state_cost_list"]

    for cost_item in cost_items:
        if cost_item["state"] == "ON":
            cost_list = cost_item["cost_list"]
            for item in cost_list:
                name = item["name"]
                value = item["value"]
                click.echo("\t{}: ".format(name.upper()), nl=False)
                click.echo(highlight_text(str(value)))


def describe_nutanix_pe_account(spec):

    cluster_id = spec["cluster_uuid"]
    cluster_name = spec["cluster_name"]

    click.echo("Cluster Id: {}".format(highlight_text(cluster_id)))
    click.echo("Cluster Name: {}".format(highlight_text(cluster_name)))


def describe_nutanix_pc_account(provider_data):

    client = get_api_client()
    ContextObj = get_context()
    server_config = ContextObj.get_server_config()

    pc_port = provider_data["port"]
    host_pc = provider_data["host_pc"]
    pc_ip = provider_data["server"] if not host_pc else server_config["pc_ip"]

    click.echo("Is Host PC: {}".format(highlight_text(host_pc)))
    click.echo("PC IP: {}".format(highlight_text(pc_ip)))
    click.echo("PC Port: {}".format(highlight_text(pc_port)))

    cluster_list = provider_data["cluster_account_reference_list"]
    if cluster_list:
        click.echo("\nCluster Accounts:\n-----------------")

    for index, cluster in enumerate(cluster_list):
        cluster_data = cluster["resources"]["data"]
        click.echo(
            "\n{}. {} (uuid: {})\tPE Account UUID: {}".format(
                str(index + 1),
                highlight_text(cluster_data["cluster_name"]),
                highlight_text(cluster_data["cluster_uuid"]),
                highlight_text(cluster["uuid"]),
            )
        )

        res, err = client.showback.status()
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(-1)

        res = res.json()
        showback_status = res["current_status"] == "enabled"
        if not showback_status:
            click.echo("Showback Status: {}".format(highlight_text("Not Enabled")))
        else:
            click.echo("Showback Status: {}".format(highlight_text("Enabled")))
            price_items = cluster["resources"].get("price_items", [])
            click.echo("Resource Usage Costs:\n----------------------")
            describe_showback_data(price_items)


def describe_aws_account(spec):

    click.echo("Access Key ID: {}".format(spec["access_key_id"]))
    regions = spec["regions"]

    click.echo("\nRegions:\n-------------- ")
    for index, region in enumerate(regions):
        click.echo("\t{}. {}".format(str(index + 1), highlight_text(region["name"])))

    click.echo("\nPublic Images:\n-------------- ")
    image_present = False
    for region in regions:
        if region.get("images"):
            click.echo("\nRegion: {}".format(region["name"]))
            click.echo("Images: ")
            for index, image in enumerate(region["images"]):
                image_present = True
                click.echo(
                    "\t{}. {}".format(str(index + 1), highlight_text(image["name"]))
                )

    if not image_present:
        click.echo("\t{}".format(highlight_text("No images provided")))


def describe_vmware_account(spec):

    click.echo("Server: {}".format(highlight_text(spec["server"])))
    click.echo("Username: {}".format(highlight_text(spec["username"])))
    click.echo("Port: {}".format(highlight_text(spec["port"])))
    click.echo("Datacenter: {}".format(highlight_text(spec["datacenter"])))


def describe_gcp_account(client, spec, account_id):

    click.echo("Project Id: {}".format(highlight_text(spec["project_id"])))
    click.echo("Client Email: {}".format(highlight_text(spec["client_email"])))
    click.echo("Token URI: {}".format(highlight_text(spec["token_uri"])))

    click.echo("\nRegions:\n--------------\n")
    regions = spec["regions"]
    for index, region in enumerate(regions):
        click.echo("\t{}. {}".format(str(index + 1), highlight_text(region["name"])))

    if not regions:
        click.echo("\t{}".format(highlight_text("No regions provided")))

    click.echo("\nPublic Images:\n--------------\n")
    images = spec["public_images"]

    Obj = get_resource_api("gcp/v1/images", client.connection)
    payload = {"filter": "account_uuid=={};public_only==true".format(account_id)}

    res, err = Obj.list(payload)  # TODO move this to GCP specific method
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    public_images = res.json()["entities"]
    image_selfLink_name_map = {}

    for image in public_images:
        name = image["status"]["name"]
        selfLink = image["status"]["resources"]["selfLink"]
        image_selfLink_name_map[selfLink] = name

    for index, image in enumerate(images):
        name = image_selfLink_name_map.get(image["selfLink"], None)
        if name:
            click.echo("\t{}. {}".format(str(index + 1), highlight_text(name)))

    if not regions:
        click.echo(highlight_text("No regions provided"))

    click.echo("\nGKE Details:\n--------------\n")
    gke_config = spec["gke_config"]

    if not gke_config:
        click.echo("\t{}".format(highlight_text("GKE not enabled")))
    else:
        click.echo("{}: {}".format("Port", highlight_text(str(gke_config["port"]))))
        click.echo("{}: {}".format("Server", highlight_text(gke_config["server"])))


def describe_azure_account(spec):

    click.echo("Subscription ID: {}".format(highlight_text(spec["subscription_id"])))
    click.echo("Tenant ID: {}".format(highlight_text(spec["tenant_id"])))
    click.echo("Client ID: {}".format(highlight_text(spec["client_id"])))
    click.echo(
        "Cloud Environment: {}".format(highlight_text(spec["cloud_environment"]))
    )


def describe_k8s_account(spec):

    click.echo("Server IP: {}".format(highlight_text(spec["server"])))
    click.echo("Port: {}".format(highlight_text(spec["port"])))

    click.echo("Authentication Type: ", nl=False)
    auth_types = {
        "basic": "Basic Auth",
        "client_certificate": "Client Certificate",
        "ca_certificate": "CA Certificate",
    }

    auth = spec["authentication"]
    auth_type = auth_types[auth["type"]]
    click.echo(highlight_text(auth_type))


def describe_account(account_name):

    client = get_api_client()
    account = get_account(client, account_name)
    account_type = account["status"]["resources"]["type"]
    account_id = account["metadata"]["uuid"]

    click.echo("\n----Account Summary----\n")

    click.echo("\t\t", nl=False)
    click.secho("GENERAL DETAILS\n", bold=True, underline=True)
    click.echo(
        "Name: "
        + highlight_text(account_name)
        + " (uuid: "
        + highlight_text(account_id)
        + ")"
    )
    click.echo("Status: " + highlight_text(account["status"]["resources"]["state"]))
    click.echo("Account Type: " + highlight_text(account_type.upper()))
    click.echo(
        "Owner: " + highlight_text(account["metadata"]["owner_reference"]["name"])
    )
    created_on = int(account["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )

    provider_data = account["status"]["resources"]["data"]

    click.echo("\n\t\t", nl=False)
    click.secho("PROVIDER SPECIFIC DETAILS\n", bold=True, underline=True)

    if account_type == "nutanix":
        describe_nutanix_pe_account(provider_data)

    if account_type == "nutanix_pc":
        describe_nutanix_pc_account(provider_data)

    elif account_type == "aws":
        describe_aws_account(provider_data)

    elif account_type == "vmware":
        describe_vmware_account(provider_data)

    elif account_type == "gcp":
        describe_gcp_account(client, provider_data, account_id)

    elif account_type == "k8s":
        describe_k8s_account(provider_data)

    elif account_type == "azure":
        describe_azure_account(provider_data)

    else:
        click.echo("Provider details not present")

    if account_type in ["nutanix", "vmware"]:
        res, err = client.showback.status()
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(-1)

        res = res.json()
        showback_status = res["current_status"] == "enabled"
        if not showback_status:
            click.echo("Showback Status: {}".format(highlight_text("Not Enabled")))
        else:
            price_items = account["status"]["resources"]["price_items"]
            click.echo("Showback Status: {}".format(highlight_text("Enabled")))
            click.echo("Resource Usage Costs:\n----------------------")
            describe_showback_data(price_items)

    click.echo("")
