import time
import click
import arrow
import sys
import copy
from prettytable import PrettyTable
from distutils.version import LooseVersion as LV
import json
import uuid
from ruamel import yaml

from calm.dsl.builtins import (
    Account,
)

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.config import get_context
from calm.dsl.builtins.models.metadata_payload import get_metadata_payload
from .providers import (
    update_custom_provider,
    get_custom_provider,
    create_custom_provider,
)
from calm.dsl.providers import get_provider
from .resource_types import update_resource_types, create_resource_type

from .utils import (
    get_name_query,
    get_states_filter,
    highlight_text,
    insert_uuid,
    _get_nested_messages,
)
from calm.dsl.constants import PROVIDER, ACCOUNT
from calm.dsl.store import Version
from calm.dsl.tools import get_module_from_file
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE

LOG = get_logging_handle(__name__)


def get_accounts(name, filter_by, limit, offset, quiet, all_items, account_type):
    """Get the accounts, optionally filtered by a string"""

    client = get_api_client()
    calm_version = Version.get_version("Calm")
    ContextObj = get_context()

    params = {"length": limit, "offset": offset}

    filter_query = ""
    stratos_config = ContextObj.get_stratos_config()
    if stratos_config.get("stratos_status", False):
        filter_query = "child_account==true"
    if name:
        filter_query = filter_query + ";" + get_name_query([name])
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
        server_config = ContextObj.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch accounts from {}".format(pc_ip))
        return

    res = res.json()
    total_matches = res["metadata"]["total_matches"]
    if total_matches > limit:
        LOG.warning(
            "Displaying {} out of {} entities. Please use --limit and --offset option for more results.".format(
                limit, total_matches
            )
        )

    json_rows = res["entities"]
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

    ContextObj = get_context()
    stratos_config = ContextObj.get_stratos_config()
    if stratos_config.get("stratos_status", False):
        params["filter"] += ";child_account==true"

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


def compile_account(account_file):
    """Returns the compiled payload from an account_file"""

    user_account_module = get_account_module_from_file(account_file)
    UserAccount = get_account_class_from_module(user_account_module)

    if UserAccount is None:
        return None

    account_payload = create_account_payload(UserAccount)

    account_type = UserAccount.type

    if account_type == "credential_provider":
        account_payload = create_credential_provider_account_payload(UserAccount)

    return account_payload


def compile_account_command(account_file, out):

    account_payload = compile_account(account_file)

    if account_payload is None:
        LOG.error("User account not found in {}".format(account_file))
        return

    account_type = (
        account_payload.get("account", {})
        .get("spec", {})
        .get("resources", {})
        .get("type", "")
    )

    # if is is a credential provider account
    if account_type == "custom_provider":
        account_payload = account_payload.get("account", {})

    if out == "json":
        click.echo(json.dumps(account_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(account_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def create_account(client, account_payload, name=None, force_create=False):
    """
    create account with the provided payload
    """

    account_type = (
        account_payload.get("account", {})
        .get("spec", {})
        .get("resources", {})
        .get("type", "")
    )

    # For custom_provider type we create provider and resource_type before creating account
    if account_type == "custom_provider":
        if account_payload["provider"]:
            create_custom_provider(
                provider_payload=account_payload.get("provider", {}), name=name
            )
        if account_payload["resource_type"]:
            create_resource_type(
                resource_type_payload=account_payload.get("resource_type", {}),
                name=name,
            )
        account_payload = account_payload.get("account", {})

    else:
        account_resources = account_payload.get("spec", {}).get("resources", {})
        account_type = account_resources.get("type", "")
        account_data = account_resources.get("data", "")

        if account_type == ACCOUNT.TYPE.GCP:
            public_images = account_data.get("public_images", [])
            if public_images:
                LOG.error("public_images is not a valid parameter for create command")
                sys.exit("Invalid argument public_images")

        elif account_type == ACCOUNT.TYPE.VMWARE:
            datacenter = account_data.get("datacenter", "")
            if datacenter:
                LOG.error("'datacenter' is not a valid parameter for create command")
                sys.exit("Invalid parameter 'datacenter'")

        elif account_type == ACCOUNT.TYPE.AZURE:
            subscriptions = account_data.get("subscriptions", [])
            default_subscription = account_data.get("default_subscription", "")

            if subscriptions or default_subscription:
                LOG.error(
                    "'subscriptions', 'default_subscription' are not valid parameters for create command"
                )
                sys.exit("Invalid parameter 'subscriptions' / 'default_subscription")

        elif account_type == ACCOUNT.TYPE.AWS:
            regions = account_data.get("regions", [])
            for _rd in regions:
                if _rd.get("images", []):
                    LOG.error(
                        "Region-Images are not valid parameter for create command. User can set them on existing account using update command only"
                    )
                    sys.exit("Invalid parameter 'Images'")

    if name:
        account_payload["spec"]["name"] = name
        account_payload["metadata"]["name"] = name

    account_name = account_payload["spec"]["name"]

    return client.account.create(
        account_name,
        account_payload,
        force_create=force_create,
    )


def create_account_from_dsl(client, account_file, name=None, force_create=False):

    account_payload = compile_account(account_file)

    if account_payload is None:
        LOG.error("User account not found in {}".format(account_file))
        sys.exit("User account not found")

    res, err = create_account(
        client, account_payload, name=name, force_create=force_create
    )
    if err:
        LOG.error(err["error"])
        sys.exit("Account creation failed")

    account = res.json()

    account_uuid = account["metadata"]["uuid"]
    account_name = account["metadata"]["name"]
    account_status = account.get("status", {})
    account_state = account_status.get("resources", {}).get("state", "DRAFT")
    account_type = account_status.get("resources", {}).get("type", "")
    LOG.debug("Account {} has state: {}".format(account_name, account_state))

    if account_state == "DRAFT":
        msg_list = []
        _get_nested_messages("", account_status, msg_list)

        if not msg_list:
            LOG.error("Account {} created with errors.".format(account_name))
            LOG.debug(json.dumps(account_status))

        msgs = []
        for msg_dict in msg_list:
            msg = ""
            path = msg_dict.get("path", "")
            if path:
                msg = path + ": "
            msgs.append(msg + msg_dict.get("message", ""))

        LOG.error(
            "Account {} created with {} error(s):".format(account_name, len(msg_list))
        )
        click.echo("\n".join(msgs))
        sys.exit("Account went to {} state".format(account_state))

    LOG.info("Updating accounts cache ...")
    if account_type == ACCOUNT.TYPE.AHV:
        Cache.sync_table(
            cache_type=[
                CACHE.ENTITY.ACCOUNT,
                CACHE.ENTITY.AHV_DISK_IMAGE,
                CACHE.ENTITY.AHV_CLUSTER,
                CACHE.ENTITY.AHV_VPC,
                CACHE.ENTITY.AHV_SUBNET,
            ]
        )
    else:
        # TODO Fix case for custom providers
        Cache.add_one(CACHE.ENTITY.ACCOUNT, account_uuid)
        click.echo(".[Done]", err=True)

    LOG.info("Account {} created successfully.".format(account_name))
    context = get_context()
    server_config = context.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    link = "https://{}:{}/dm/self_service/settings/accounts".format(pc_ip, pc_port)
    stdout_dict = {
        "name": account_name,
        "uuid": account_uuid,
        "link": link,
        "state": account_state,
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    return stdout_dict


def get_account_module_from_file(account_file):
    """Returns Account module given a user account dsl file (.py)"""
    return get_module_from_file("calm.dsl.user_account", account_file)


def get_account_class_from_module(user_account_module):
    """Returns account class given a module"""

    UserAccount = None
    for item in dir(user_account_module):
        obj = getattr(user_account_module, item)
        if isinstance(obj, (type(Account))):
            UserAccount = obj

    return UserAccount


def create_account_payload(UserAccount):
    err = {"error": "", "code": -1}

    if UserAccount is None:
        err["error"] = "Given account is empty."
        return None, err

    if not isinstance(UserAccount, type(Account)):
        err["error"] = "Given account is not of type Account"
        LOG.info("Given account is not of type Account")
        return None, err

    account_name = getattr(UserAccount, "__name__", "")
    spec = {"name": account_name, "resources": UserAccount.get_dict()}
    metadata = {"kind": "account", "name": account_name, "uuid": str(uuid.uuid4())}

    account_payload = {"spec": spec, "metadata": metadata}

    return account_payload


def create_credential_provider_account_payload(UserAccount):
    """
    create payload for credential provider

    Returns:
        credential_provider_payload(dict): contains payload for credential provider
            Keys:
                provider: Provider payload
                resource_type: resource_type payload
                account: Account payload
    """

    err = {"error": "", "code": -1}

    if UserAccount is None:
        err["error"] = "Given account is empty."
        return None, err

    if not isinstance(UserAccount, type(Account)):
        err["error"] = "Given account is not of type Account"
        LOG.info("Given account is not of type Account")
        return None, err

    # creating provider payload
    provider_payload = create_provider_payload(UserAccount)

    # creating resource_type payload
    provider_uuid = provider_payload.get("metadata", {}).get("uuid")
    resource_type_payload = create_resource_type_payload(
        UserAccount, provider_uuid=provider_uuid
    )

    account_payload = {}

    account_name = getattr(UserAccount, "name", "") or getattr(
        UserAccount, "__name__", ""
    )

    metadata = {"kind": "account", "name": account_name, "uuid": str(uuid.uuid4())}
    resources = getattr(UserAccount, "resources", "").get_dict()
    variable_list = resources.get("auth_schema_list", [])
    for variable in variable_list:
        variable["uuid"] = str(uuid.uuid4())
        if variable["type"] == "SECRET":
            variable["attrs"] = {"is_secret_modified": True, "type": "SECRET"}

    provider_reference = (
        resource_type_payload.get("spec", {})
        .get("resources", {})
        .get("provider_reference", {})
    )

    account_resources = {
        "type": "custom_provider",
        "data": {
            "provider_reference": provider_reference,
            "variable_list": variable_list,
        },
    }
    spec = {"name": account_name, "resources": account_resources}

    account_payload["spec"] = spec
    account_payload["metadata"] = metadata

    credential_provider_payload = {}
    credential_provider_payload["provider"] = provider_payload
    credential_provider_payload["resource_type"] = resource_type_payload
    credential_provider_payload["account"] = account_payload

    return credential_provider_payload


def create_resource_type_payload(UserAccount, provider_uuid):
    """
    creates resource_type payload
    """

    name = getattr(UserAccount, "name", "") or getattr(UserAccount, "__name__", "")

    metadata = {"kind": "resource_type", "name": name, "uuid": str(uuid.uuid4())}
    resources = UserAccount.get_dict().get("data", {}).get("resource_config", {})

    input_vars = resources.get("variables", []).copy()
    output_vars = resources.get("cred_attrs", []).copy()

    for var in input_vars:
        if var["type"] == "SECRET":
            var["attrs"] = {"is_secret_modified": True, "type": "SECRET"}

    for var in output_vars:
        if var["type"] == "SECRET":
            var["attrs"] = {"is_secret_modified": True, "type": "SECRET"}

    action_list = resources.get("action_list", []).copy()

    name_uuid_map = {}
    action_list_with_uuid = copy.deepcopy(action_list)

    # Inserting uuids in action_list
    insert_uuid(
        action=action_list,
        name_uuid_map=name_uuid_map,
        action_list_with_uuid=action_list_with_uuid,
    )

    for input_var in input_vars:
        input_var["uuid"] = str(uuid.uuid4())
    for output_var in output_vars:
        output_var["uuid"] = str(uuid.uuid4())

    provider_reference = {"kind": "provider", "uuid": provider_uuid}

    resource_type_resources = {
        "provider_reference": provider_reference,
        "variable_list": input_vars,
        "schema_list": output_vars,
        "action_list": action_list_with_uuid,
    }

    spec = {"name": name, "resources": resource_type_resources}
    resource_type_payload = {}
    resource_type_payload["spec"] = spec
    resource_type_payload["metadata"] = metadata

    return resource_type_payload


def create_provider_payload(UserAccount):
    """
    creates provider payload
    """

    name = getattr(UserAccount, "name", "") or getattr(UserAccount, "__name__", "")

    metadata = {"kind": "provider", "uuid": str(uuid.uuid4())}
    resources = UserAccount.get_dict().get("data", {})

    auth_schema_list = resources.get("auth_schema_list", []).copy()
    for auth_schema in auth_schema_list:
        auth_schema["value"] = ""
        auth_schema["uuid"] = str(uuid.uuid4())
        if auth_schema["type"] == "SECRET":
            auth_schema["attrs"] = {"is_secret_modified": True, "type": "SECRET"}

    provider_resources = {"auth_schema_list": auth_schema_list}

    spec = {"name": name, "resources": provider_resources}
    provider_payload = {}
    provider_payload["spec"] = spec
    provider_payload["metadata"] = metadata

    return provider_payload


def delete_account(account_names):
    client = get_api_client()
    any_ahv_account = False
    delete_accounts_uuids = []
    for account_name in account_names:
        account_payload = get_account(client, account_name)
        account_uuid = account_payload["metadata"]["uuid"]
        delete_accounts_uuids.append(account_uuid)
        account_type = (
            account_payload.get("spec", {}).get("resources", {}).get("type", "")
        )

        if account_type in [ACCOUNT.TYPE.AHV, ACCOUNT.TYPE.AHV_PE]:
            any_ahv_account = True

        # Handling case where account type is not custom provider
        if account_type != "custom_provider":
            _, err = client.account.delete(account_uuid)
            if err:
                LOG.error("Unable to delete Account")
                sys.exit("Error Code: [{}]".format(err["code"]))
            LOG.info("Account {} deleted".format(account_name))

        # Handling case where account type is custom provider
        else:
            LOG.info(
                "Custom Provider Account Found. Deleting attached Provider and ResourceType."
            )

            provider_uuid = (
                account_payload.get("spec", {})
                .get("resources", {})
                .get("data", {})
                .get("provider_reference", {})
                .get("uuid", None)
            )

            provider_payload = get_custom_provider(account_name, provider_uuid)
            resources = (
                provider_payload.get("status", {})
                .get("resources", {})
                .get("resource_type_references", [])
            )

            provider_payload_type = (
                provider_payload.get("status", {})
                .get("resources", {})
                .get("type", None)
            )

            resource_uuids = []
            for resource in resources:
                if resource["kind"] == "resource_type":
                    resource_uuids.append(resource["uuid"])

            # If provider type is CREDENTIAL, deleting in this order ->
            # ResourceType, Account, Provider
            if provider_payload_type and provider_payload_type == "CREDENTIAL":
                for resource_uuid in resource_uuids:
                    _, err = client.resource_types.delete(resource_uuid)
                    if err:
                        LOG.error("Unable to delete ResourceType")
                        sys.exit("Error Code: [{}]".format(err["code"]))
                    LOG.info("ResourceType (uuid='{}') deleted".format(resource_uuid))

                _, err = client.account.delete(account_uuid)
                if err:
                    LOG.error("Unable to delete Account")
                    sys.exit("Error Code: [{}]".format(err["code"]))
                LOG.info("Account {} deleted".format(account_name))

                _, err = client.provider.delete(provider_uuid)
                if err:
                    LOG.error("Unable to delete Provider")
                    sys.exit("Error Code: [{}]".format(err["code"]))
                LOG.info("Provider (uuid='{}') deleted".format(provider_uuid))

    # Update account related caches i.e. Account, AhvImage, AhvSubnet
    LOG.info("Updating accounts cache ...")
    if any_ahv_account:
        Cache.sync_table(
            cache_type=[
                CACHE.ENTITY.ACCOUNT,
                CACHE.ENTITY.AHV_DISK_IMAGE,
                CACHE.ENTITY.AHV_CLUSTER,
                CACHE.ENTITY.AHV_VPC,
                CACHE.ENTITY.AHV_SUBNET,
            ]
        )
    else:
        # TODO Fix case for custom providers
        if delete_accounts_uuids:
            for _acc_id in delete_accounts_uuids:
                Cache.delete_one(entity_type=CACHE.ENTITY.ACCOUNT, uuid=_acc_id)
            click.echo(".[Done]", err=True)


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
        "service_account": "Service Account",
    }

    auth = spec["authentication"]
    auth_type = auth_types[auth["type"]]
    click.echo(highlight_text(auth_type))


def describe_custom_provider_account(client, spec):
    provider_name = resource_type_name = spec["provider_reference"]["name"]
    click.echo("Provider Name: {}".format(provider_name))

    click.echo("Account Variables")
    for variable in spec["variable_list"]:
        click.echo("\t{}".format(highlight_text(variable["name"])))

    Obj = client.resource_types

    params = {"filter": "name=={}".format(resource_type_name)}
    res, err = Obj.list(params=params)
    if err:
        LOG.exception("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    response = res.json()
    entities = response.get("entities", None)
    resource_type = None
    if entities:
        if len(entities) != 1:
            LOG.exception("More than one account found - {}".format(entities))
            sys.exit(-1)

        LOG.info("{} found ".format(resource_type_name))
        resource_type = entities[0]
    else:
        LOG.exception("No account having name {} found".format(resource_type_name))
        sys.exit(-1)

    click.echo("Resource Type Schema Variables")
    for schema_variable in resource_type["status"]["resources"]["schema_list"]:
        click.echo("\t{}".format(highlight_text(schema_variable["name"])))

    click.echo("Resource Type Variables List")
    for variable in resource_type["status"]["resources"]["variable_list"]:
        click.echo("\t{}".format(highlight_text(variable["name"])))


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

    elif account_type == "custom_provider":
        describe_custom_provider_account(client, provider_data)

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


def sync_account(account_name):
    """Sync account with corresponding account name"""

    client = get_api_client()
    account_uuid = client.account.get_name_uuid_map().get(account_name, "")

    if not account_uuid:
        LOG.error("Could not find the account {}".format(account_name))
        sys.exit(-1)

    LOG.info("Syncing Account")
    res, err = client.account.platform_sync(account_uuid)

    if err:
        LOG.exception("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    LOG.info("Syncing account successfull")


def verify_account(account_name):
    """Verify an account with corresponding account name"""

    client = get_api_client()
    account_uuid = client.account.get_name_uuid_map().get(account_name, "")

    if not account_uuid:
        LOG.error("Could not find the account {}".format(account_name))
        sys.exit(-1)

    LOG.info("Verifying account '{}'".format(account_name))
    _, err = client.account.verify(account_uuid)

    if err:
        LOG.exception("[{}] - {}".format(err["code"], err["error"]))
        sys.exit("Account verification failed")

    LOG.info("Account '{}' sucessfully verified".format(account_name))


def update_account(client, account_payload, name=None, updated_name=None):

    account_payload.pop("status", None)

    # updating the name of the account to updated_name if provided otherwise it is kept as it is originally
    account_payload["spec"]["name"] = updated_name or name
    account_payload["metadata"]["name"] = updated_name or name

    account_resources = account_payload["spec"]["resources"]
    account_name = account_payload["spec"]["name"]

    account = get_account(client, name)
    uuid = account["metadata"]["uuid"]
    spec_version = account["metadata"]["spec_version"]

    account_type = account_payload.get("spec", {}).get("resources", {}).get("type", "")

    if account_type == "NDB":
        variable_uuid_map = {}

        for variable in account["spec"]["resources"]["data"]["variable_list"]:
            variable_uuid_map[variable["label"]] = variable["uuid"]

        for variable in account_resources["data"]["variable_list"]:
            variable["uuid"] = variable_uuid_map[variable["label"]]

    # creting updated account payload
    account_payload = {
        "spec": {"name": account_name, "resources": account_resources},
        "metadata": {
            "spec_version": spec_version,
            "name": account_name,
            "kind": "account",
        },
        "api_version": "3.0",
    }

    return client.account.update(uuid, account_payload)


def update_account_from_json(client, path_to_json, name=None, updated_name=None):

    account_payload = json.loads(open(path_to_json, "r").read())
    return update_account(client, account_payload, name=name)


def update_account_from_dsl(client, account_file, name=None, updated_name=None):

    account_payload = compile_account(account_file)
    if account_payload is None:
        err_msg = "User account not found in {}".format(account_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    account_type = (
        account_payload.get("account", {})
        .get("spec", {})
        .get("resources", {})
        .get("type", "")
    )

    account = get_account(client, name)
    account_uuid = account["metadata"]["uuid"]

    # if is is a credential provider account
    if account_type == ACCOUNT.TYPE.CUSTOM_PROVIDER:
        update_custom_provider(
            provider_payload=account_payload["provider"],
            name=name,
            updated_name=updated_name,
        )
        update_resource_types(
            resource_type_payload=account_payload["resource_type"],
            account_uuid=account_uuid,
            name=name,
            updated_name=updated_name,
        )
        account_payload = account_payload.get("account", {})
        provider = get_custom_provider(updated_name or name)
        account_payload["spec"]["resources"]["data"]["provider_reference"][
            "uuid"
        ] = provider["metadata"]["uuid"]

    else:
        account_resources = account_payload.get("spec", {}).get("resources", {})
        account_type = account_resources.get("type", "")
        account_data = account_resources.get("data", "")

        if account_type == ACCOUNT.TYPE.GCP:
            public_images = account_data.get("public_images", [])
            if public_images:
                gcpProvider = get_provider(PROVIDER.TYPE.GCP)
                gcpResource = gcpProvider.get_api_obj()

                payload = {
                    "filter": "account_uuid=={};public_only==true".format(account_uuid)
                }
                images_name_data_map = gcpResource.images(payload)

                final_public_images = []
                for pi in public_images:
                    if not images_name_data_map.get(pi):
                        LOG.error("Invalid public image provided {}".format(pi))
                        sys.exit("Invalid public image")

                    final_public_images.append(
                        {
                            "selfLink": images_name_data_map[pi]["selfLink"],
                            "diskSizeGb": images_name_data_map[pi]["diskSizeGb"],
                        }
                    )

                account_data["public_images"] = final_public_images

        elif account_type == ACCOUNT.TYPE.VMWARE:
            datacenter = account_data.get("datacenter", "")
            if datacenter:
                vmwProvider = get_provider(PROVIDER.TYPE.VMWARE)
                vmwResource = vmwProvider.get_api_obj()
                verifiedDatacenters = vmwResource.datacenters(account_uuid)
                if datacenter not in verifiedDatacenters:
                    LOG.error(
                        "Invalid datacenter '{}' found. Please select one of {}".format(
                            datacenter, json.dumps(verifiedDatacenters)
                        )
                    )
                    sys.exit("Invalid datacenter provided")

        elif account_type == ACCOUNT.TYPE.AZURE:
            subscriptions = account_data.pop("subscriptions", [])
            default_subscription = account_data.pop("default_subscription", "")

            if subscriptions or default_subscription:
                azureProvider = get_provider(PROVIDER.TYPE.AZURE)
                azureResource = azureProvider.get_api_obj()
                valid_subs = azureResource.subscriptions(account_uuid)

                subs_data = []
                for _subs_name in subscriptions:
                    if _subs_name not in valid_subs:
                        LOG.error(
                            "Invalid subscription '{}' found in subscriptions. Please select one of {}".format(
                                _subs_name, json.dumps(list(valid_subs.keys()))
                            )
                        )
                        sys.exit("Invalid subscription provided")

                    subs_data.append({"subscription_id": valid_subs[_subs_name]["id"]})

                if subs_data:
                    account_data["subscriptions"] = subs_data

                if default_subscription:
                    if default_subscription not in valid_subs:
                        LOG.error(
                            "Invalid subscription '{}' found in default_subscription. Please select one of {}".format(
                                default_subscription,
                                json.dumps(list(valid_subs.keys())),
                            )
                        )
                        sys.exit("Invalid subscription provided")

                    account_data["subscription_id"] = valid_subs[default_subscription][
                        "id"
                    ]

        elif account_type == ACCOUNT.TYPE.AWS:
            awsProvider = get_provider(PROVIDER.TYPE.AWS)
            awsResource = awsProvider.get_api_obj()
            regions = account_data.get("regions", [])
            for _rd in regions:
                _rname = _rd.get("name", "")
                if not _rname:
                    LOG.error("Region name is compulsory")
                    sys.exit("Invalid region data")

                _rimgs = _rd.pop("images", [])
                if _rimgs:
                    _fimgs = []
                    for _ri in _rimgs:
                        img_data = awsResource.images(account_uuid, _rname, _ri)
                        if not img_data.get(_ri):
                            LOG.error("Image not found {}".format(_ri))
                            sys.exit("Invalid image {}".format(_ri))

                        _fimgs.append(
                            {
                                "name": img_data[_ri]["name"],
                                "image_id": img_data[_ri]["id"],
                                "root_device_name": img_data[_ri]["root_device_name"],
                            }
                        )

                    _rd["images"] = _fimgs

    return update_account(client, account_payload, name=name, updated_name=updated_name)


def update_account_command(account_file, name, updated_name):
    """Updates a account"""

    client = get_api_client()

    if account_file.endswith(".json"):
        res, err = update_account_from_json(
            client, account_file, name=name, updated_name=updated_name
        )
    elif account_file.endswith(".py"):
        res, err = update_account_from_dsl(
            client, account_file, name=name, updated_name=updated_name
        )
    else:
        LOG.error("Unknown file format {}".format(account_file))
        return

    if err:
        LOG.error(err["error"])
        return

    account = res.json()
    account_uuid = account["metadata"]["uuid"]
    account_name = account["metadata"]["name"]
    account_status = account.get("status", {})
    account_state = account_status.get("resources", {}).get("state", "DRAFT")
    account_type = account_status.get("resources", {}).get("type", "")
    LOG.debug("Account {} has state: {}".format(account_name, account_state))

    if account_state != "ACTIVE":
        msg_list = account_status.get("message_list", [])
        if not msg_list:
            LOG.error("Account {} updated with errors.".format(account_name))
            LOG.debug(json.dumps(account_status))
            sys.exit(-1)

        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        LOG.error(
            "Account {} updated with {} error(s): {}".format(
                account_name, len(msg_list), msgs
            )
        )
        sys.exit("Account went to {} state".format(account_state))

    LOG.info("Updating accounts cache ...")
    if account_type == ACCOUNT.TYPE.AHV:
        Cache.sync_table(
            cache_type=[
                CACHE.ENTITY.ACCOUNT,
                CACHE.ENTITY.AHV_DISK_IMAGE,
                CACHE.ENTITY.AHV_CLUSTER,
                CACHE.ENTITY.AHV_VPC,
                CACHE.ENTITY.AHV_SUBNET,
            ]
        )
    else:
        # TODO Fix case for custom providers
        Cache.update_one(CACHE.ENTITY.ACCOUNT, account_uuid)
        click.echo(".[Done]", err=True)

    LOG.info("Account {} updated successfully.".format(account_name))
    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    link = "https://{}:{}/dm/self_service/settings/accounts".format(pc_ip, pc_port)
    stdout_dict = {"name": account_name, "link": link, "state": account_state}
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))
