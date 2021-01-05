import json
import time
import click
import arrow
import sys
from prettytable import PrettyTable
from ruamel import yaml
from distutils.version import LooseVersion as LV

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.tools import get_module_from_file
from calm.dsl.config import get_context
from calm.dsl.builtins import Account

from .utils import get_name_query, get_states_filter, highlight_text
from calm.dsl.constants import PROVIDER
from calm.dsl.providers import get_provider
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
    res, _ = client.account.list(params=params)

    response = res.json()
    entities = response.get("entities", None)
    account = None
    if entities:
        if len(entities) != 1:
            LOG.error("More than one account found - {}".format(entities))
            sys.exit(-1)

        LOG.info("{} found ".format(account_name))
        account = entities[0]
    else:
        LOG.error("No account having name {} found".format(account_name))
        sys.exit(-1)

    account_id = account["metadata"]["uuid"]
    LOG.info("Fetching account details")
    res, _ = client.account.read(account_id)

    account = res.json()
    return account


def get_account_module_from_file(account_file):
    """Returns Account module given a user account dsl file (.py)"""
    return get_module_from_file("calm.dsl.user_account", account_file)


def get_account_class_from_module(user_account_module):
    """Returns account class given a module"""

    UserAccount = None
    for item in dir(user_account_module):
        obj = getattr(user_account_module, item)
        if isinstance(obj, type(Account)):
            if obj.__bases__[0] == Account:
                UserAccount = obj

    return UserAccount


def compile_account(account_file):
    """returns compiled payload from dsl account file"""

    user_account_module = get_account_module_from_file(account_file)
    UserAccount = get_account_class_from_module(user_account_module)
    if UserAccount is None:
        LOG.error("User account not found in {}".format(account_file))
        return

    # create account payload
    account_payload = {
        "spec": {
            "name": UserAccount.__name__,
            "resources": UserAccount.get_dict(),
        },
        "metadata": {
            "name": UserAccount.__name__,
            "kind": getattr(UserAccount, "__kind__"),
        },
    }

    return account_payload


def compile_account_command(account_file, out):
    """displays the account payload"""

    account_payload = compile_account(account_file)

    if out == "json":
        click.echo(json.dumps(account_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(account_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def create_account(account_file, name):
    """creates an account"""

    client = get_api_client()

    account_payload = compile_account(account_file=account_file)
    if name:
        account_payload["spec"]["name"] = name
        account_payload["metadata"]["name"] = name
    else:
        name = account_payload["spec"]["name"]

    # check if any account already exists with given name
    params = {"filter": "name=={}".format(name)}
    account_name_uuid_map = client.account.get_name_uuid_map(params=params)

    if account_name_uuid_map:
        LOG.error("Account with same name '{}' already exists".format(name))
        sys.exit(-1)

    LOG.info("Creating account '{}'".format(name))

    account_type = account_payload["spec"]["resources"]["type"]
    # Some attributes should be sent in update payload

    # Extract public images from gcp account
    gcp_public_images = []
    if account_type == PROVIDER.ACCOUNT.GCP:
        gcp_public_images = (
            account_payload["spec"]["resources"]["data"].pop("public_images", None)
            or []
        )

    # Extract public images for aws account
    aws_region_image_map = {}
    if account_type == PROVIDER.ACCOUNT.AWS:
        for _en in account_payload["spec"]["resources"]["data"].get("regions", []):
            aws_region_image_map[_en["name"]] = _en.get("images", [])
            _en["images"] = []

    res, err = client.account.create(account_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    account = res.json()
    account_state = account["status"]["resources"]["state"]
    account_uuid = account["metadata"]["uuid"]
    msg_list = account["status"].get("message_list")

    if account_state != ACCOUNT.STATES.ACTIVE:
        LOG.error("Account went to '{}' state".format(account_state))
        if msg_list:
            LOG.error("Api returned following messages: {}".format(msg_list))
        return

    account.pop("status", None)
    if account_type == PROVIDER.ACCOUNT.GCP and gcp_public_images:
        GcpProvider = get_provider(PROVIDER.VM.GCP)
        GcpObj = GcpProvider.get_api_obj()

        params = {"filter": "account_uuid=={};public_only==true".format(account_uuid)}
        res, _ = GcpObj.public_images(params=params)
        res = res.json()

        update_payload = account
        update_payload["spec"]["resources"]["data"]["public_images"] = []
        for _en in res["entities"]:
            if _en["status"]["resources"]["name"] in gcp_public_images:
                update_payload["spec"]["resources"]["data"]["public_images"].append(
                    {
                        "diskSizeGb": _en["status"]["resources"]["diskSizeGb"],
                        "selfLink": _en["status"]["resources"]["selfLink"],
                    }
                )

        res, err = client.account.update(uuid=account_uuid, payload=update_payload)
        if err:
            LOG.error(err)
            sys.exit(-1)
        res = res.json()
        account_state = res["status"]["resources"]["state"]

    if account_type == PROVIDER.ACCOUNT.AWS and aws_region_image_map:
        AwsProvider = get_provider(PROVIDER.VM.AWS)
        AwsObj = AwsProvider.get_api_obj()

        update_payload = account
        for _en in update_payload["spec"]["resources"]["data"].get("regions", []):
            region_name = _en["name"]

            _en["images"] = []
            for _image in aws_region_image_map.get(region_name, []):
                payload = {
                    "filter": "account_uuid=={};region=={};public_images==true;public_only==true;image_name=={}".format(
                        account_uuid, _en["name"], _image
                    )
                }
                res, _ = AwsObj.images(payload)
                res = res.json()

                if res["metadata"]["total_matches"] == 0:
                    LOG.warning(
                        "'{}' image not found in region '{}'".format(
                            _image, region_name
                        )
                    )
                    continue

                if res["metadata"]["total_matches"] > 1:
                    LOG.warning(
                        "More than one images with name '{}' found in region '{}'. Skipping image.".format(
                            _image, region_name
                        )
                    )
                    continue

                _en["images"].append(
                    {
                        "name": _image,
                        "image_id": res["entities"][0]["status"]["resources"]["id"],
                        "root_device_name": res["entities"][0]["status"]["resources"][
                            "root_device_name"
                        ],
                    }
                )

        res, err = client.account.update(uuid=account_uuid, payload=update_payload)
        if err:
            LOG.error(err)
            sys.exit(-1)
        res = res.json()
        account_state = res["status"]["resources"]["state"]

    stdout_dict = {
        "name": name,
        "uuid": account_uuid,
        "state": account_state,
    }

    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))
    click.echo(
        '# Hint: You can verify accounts using: calm verify account "{}"'.format(name)
    )


def delete_account(account_names):
    """deletes an account"""

    client = get_api_client()
    for account_name in account_names:
        account = get_account(client, account_name)
        account_id = account["metadata"]["uuid"]
        res, _ = client.account.delete(
            account_id
        )  # err will be handled in connection.py
        if res.ok:
            res = res.json()
            LOG.info(res["description"])


def verify_account(account_name):
    """verifies the account"""

    client = get_api_client()

    # Find account_uuid using list call
    params = {"filter": "name=={}".format(account_name)}
    account_name_uuid_map = client.account.get_name_uuid_map(params=params)

    if not account_name_uuid_map:
        LOG.error("No account with name '{}' found.".format(account_name))
        sys.exit(-1)

    account_uuid = account_name_uuid_map.get(account_name)
    res, _ = client.account.verify(
        account_uuid
    )  # err is already handled in connection.pyi

    if res.ok:
        res = res.json()
        LOG.info(res["description"])


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
        LOG.exception("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

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

    if account_type == PROVIDER.ACCOUNT.NUTANIX:
        describe_nutanix_pc_account(provider_data)

    elif account_type == PROVIDER.ACCOUNT.AWS:
        describe_aws_account(provider_data)

    elif account_type == PROVIDER.ACCOUNT.VMWARE:
        describe_vmware_account(provider_data)

    elif account_type == PROVIDER.ACCOUNT.GCP:
        describe_gcp_account(client, provider_data, account_id)

    elif account_type == "k8s":
        describe_k8s_account(provider_data)

    elif account_type == PROVIDER.ACCOUNT.AZURE:
        describe_azure_account(provider_data)

    else:
        click.echo("Provider details not present")

    if account_type in ["nutanix", PROVIDER.ACCOUNT.VMWARE]:
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
