import arrow
import click
import copy
import json
import os
import pathlib
import sys
import time
import uuid

from black import format_file_in_place, WriteBack, FileMode
from prettytable import PrettyTable
from ruamel import yaml

from calm.dsl.api import get_api_client
from calm.dsl.builtins import file_exists, get_valid_identifier
from calm.dsl.builtins.models.cloud_provider import CloudProvider, CloudProviderType
from calm.dsl.builtins.models.cloud_provider_payload import (
    create_cloud_provider_payload,
)
from calm.dsl.builtins.models.helper.common import get_provider_uuid
from calm.dsl.config import get_context
from calm.dsl.constants import ENTITY_KIND, VARIABLE, CACHE
from calm.dsl.db.table_config import ResourceTypeCache, ProviderCache
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache
from calm.dsl.tools import get_module_from_file

from calm.dsl.decompile.decompile_render import create_provider_dir
from calm.dsl.decompile.file_handler import get_provider_dir

# TODO: Test various supported flags for decompile command
from calm.dsl.decompile.bp_file_helper import decrypt_decompiled_secrets_file
from calm.dsl.decompile.main import init_decompile_context

from .constants import PROVIDER, ENTITY
from .utils import (
    get_name_query,
    get_states_filter,
    highlight_text,
    insert_uuid,
    Display,
    import_var_from_file,
)
from .runbooks import poll_action, watch_runbook, abort_runbook_execution
from .runlog import get_runlog_status

LOG = get_logging_handle(__name__)
ICON_ALREADY_EXISTS = "Image with same name already exists"
ICON_ALREADY_EXISTS_WITH_NAME = "Image with name '{}' already exists"


def _prepare_var_dict(var_dict, cred_name_uuid_map):
    """
    Helper function to prepare variable dict as per API format.
    Does the following:
    - generate and insert uuid
    - for secret variables, modifies the attrs to ensure the value configured in var_dict["value"] is honored
    """
    if not var_dict.get("uuid"):
        var_dict["uuid"] = str(uuid.uuid4())

    if var_dict["type"] in VARIABLE.SECRET_TYPES:
        var_dict["attrs"] = {
            "is_secret_modified": True,
            "type": VARIABLE.SECRET_ATTRS_TYPE,
        }

    # Handle shell/powershell dynamic variables
    cred_ref = None
    options_type = var_dict.get("options", {}).get("type")
    if options_type == VARIABLE.OPTIONS.TYPE.EXEC:
        cred_ref = var_dict["options"]["attrs"].get("login_credential_local_reference")

    elif options_type == VARIABLE.OPTIONS.TYPE.HTTP:
        http_attrs = var_dict["options"]["attrs"]
        cred_ref = http_attrs.get("authentication", {}).get(
            "credential_local_reference"
        )

        # Insert uuids to header variables
        headers = http_attrs.get("headers", [])
        for header_dict in headers:
            _prepare_var_dict(header_dict, cred_name_uuid_map)

    if cred_ref:
        cred_ref["uuid"] = cred_name_uuid_map[cred_ref["name"]]


def create_or_fetch_icon_info(icon_name=None, icon_file=None, client=None):
    """
    If icon_file is not None, upload the icon file
        If icon_name is provided, use that name for uploading.
        Else, extract & use the file name as icon name
    Else
        Check if icon with provided name exists
        If so, fetch the icon reference

    Args:
        icon_name (String): Name of the icon
        icon_file (String): Icon file
        client (Object): API client handle
    Returns:
        (Dict) Icon reference
    Raises:
        Exception if icon_file is not provided & icon with provided icon_name
        does not exist
    """
    if icon_name or icon_file:
        if not client:
            from calm.dsl.api import get_api_client

            client = get_api_client()

        icon_name = icon_name or os.path.splitext(os.path.basename(icon_file))[0]
        if icon_file:
            _, err = client.app_icon.upload(icon_name, icon_file)
            if err and ICON_ALREADY_EXISTS in str(err):
                LOG.warning(
                    ICON_ALREADY_EXISTS_WITH_NAME.format(icon_name)
                    + " & will be reused here. "
                    + "Instead, if the provided icon MUST be uploaded, "
                    + "use a different icon name for it & retry the operation"
                )

        icons_name_uuid_map = client.app_icon.get_name_uuid_map(
            params={"filter": "name=={}".format(icon_name)}
        )
        icon_uuid = icons_name_uuid_map.get(icon_name, None)
        if not icon_uuid:
            LOG.error("Icon named '{}' not found".format(icon_name))
            sys.exit(-1)

        return {"kind": ENTITY_KIND.APP_ICON, "name": icon_name, "uuid": icon_uuid}


def _prepare_resource_type_dict(resource_type_dict, name_uuid_map, for_create):
    """
    Helper function to prepare resource_type dict as per API format.
    Does the following:
    - generate and insert uuids in variable & action dictionaries
    """
    if not resource_type_dict:
        return

    resource_type_dict["uuid"] = str(uuid.uuid4())
    schema_variables = resource_type_dict.get("schema_list", [])
    for var in schema_variables:
        _prepare_var_dict(var, name_uuid_map)

    variables = resource_type_dict.get("variable_list", [])
    for var in variables:
        _prepare_var_dict(var, name_uuid_map)

    action_list = resource_type_dict.get("action_list")
    if action_list:
        action_list_with_uuid = copy.deepcopy(action_list)
        modified_name_uuid_map = {
            name: {"non_action": uuid} for name, uuid in name_uuid_map.items()
        }
        for index, action in enumerate(action_list):
            insert_uuid(
                action=action,
                name_uuid_map=copy.deepcopy(modified_name_uuid_map),
                action_list_with_uuid=action_list_with_uuid[index],
            )
        resource_type_dict["action_list"] = action_list_with_uuid

    if for_create:
        icon_name = resource_type_dict.pop("icon_name", None)
        icon_file = resource_type_dict.pop("icon_file", None)
        icon_reference = create_or_fetch_icon_info(
            icon_name=icon_name, icon_file=icon_file
        )
        if icon_reference:
            resource_type_dict["icon_reference"] = icon_reference


def get_provider(name, provider_uuid=None, is_bulk_get=False):
    """returns provider get call data"""

    client = get_api_client()
    if not provider_uuid:
        provider_uuid = get_provider_uuid(name=name)

    if is_bulk_get:
        res, err = client.provider.bulk_read(provider_uuid)
    else:
        res, err = client.provider.read(provider_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    return res.json()


def update_provider(provider_payload, name=None, updated_name=None, is_bulk_save=False):
    """Updates a provider"""

    client = get_api_client()
    provider_payload.pop("status", None)

    provider_payload["spec"]["name"] = updated_name or name
    provider_payload["metadata"]["name"] = (
        updated_name or provider_payload["spec"]["name"]
    )

    provider_resources = provider_payload["spec"]["resources"]
    provider_name = provider_payload["spec"]["name"]

    provider = get_provider(name=name)
    uuid = provider["metadata"]["uuid"]
    spec_version = provider["metadata"]["spec_version"]

    provider_payload = {
        "spec": {"name": provider_name, "resources": provider_resources},
        "metadata": {
            "use_categories_mapping": False,
            "spec_version": spec_version,
            "name": provider_name,
            "kind": "provider",
        },
        "api_version": "3.0",
    }

    if is_bulk_save:
        return client.provider.bulk_update(uuid, provider_payload)
    return client.provider.update(uuid, provider_payload)


def create_provider(
    provider_payload,
    name,
    force_create=False,
    icon_name=None,
    icon_file=None,
    is_bulk_save=False,
    passphrase=None,
    decompiled_secrets=None,
):
    """
    creates provider

    Args:
        provider_payload(dict): payload for provider creation
    """

    client = get_api_client()

    if name:
        provider_payload["spec"]["name"] = name
        provider_payload["spec"]["resources"].get("test_account", {})["type"] = name

    icon_reference = create_or_fetch_icon_info(
        icon_name=icon_name, icon_file=icon_file, client=client
    )
    if icon_reference:
        provider_payload["spec"]["resources"]["icon_reference"] = icon_reference

    provider_name = provider_payload["spec"]["name"]
    provider, err = client.provider.check_if_provider_already_exists(provider_name)
    if err:
        LOG.error(
            "Error checking if a provider with same name already exists: {}".format(
                err["error"]
            )
        )
        sys.exit(-1)
    if provider:
        if not force_create:
            LOG.error(
                "Provider {} already exists. Use --force to first delete existing provider before create.".format(
                    provider_name
                )
            )
            sys.exit(-1)

        # --force option used in create. Delete existing provider with same name.
        provider_uuid = provider["metadata"]["uuid"]
        _, err = client.provider.delete(provider_uuid)
        if err:
            LOG.error("Error deleting existing provider: {}".format(err["error"]))
            sys.exit(-1)
        delete_provider_and_associated_rts_from_cache(provider_name, provider_uuid)
        LOG.debug(
            "Existing provider with name '{}' force deleted".format(provider_name)
        )

    LOG.info("Creating User provider '{}'".format(provider_name))
    if passphrase and decompiled_secrets:
        res, err = client.provider.upload_with_decompiled_secrets(
            provider_payload, passphrase, decompiled_secrets=decompiled_secrets
        )
    elif is_bulk_save:
        res, err = client.provider.bulk_create(provider_payload)
    else:
        res, err = client.provider.create(provider_payload)

    if not err:
        response_json = res.json()
        LOG.info("Adding provider to cache ...")
        ProviderCache.add_one_by_entity_dict(response_json)
        resource_type_list = response_json["status"]["resources"].get(
            "resource_type_list", []
        )
        if resource_type_list:
            LOG.info("Adding resource types to cache ...")
            for resource_type in resource_type_list:
                ResourceTypeCache.add_one_by_entity_dict(
                    {
                        "status": {
                            "state": resource_type["state"],
                            "name": resource_type["name"],
                            "resources": resource_type,
                        },
                        "metadata": {"uuid": resource_type["uuid"]},
                    }
                )
    return res, err


def describe_provider(provider_name, out):
    """Displays provider data"""

    provider = get_provider(provider_name, is_bulk_get=True)

    if out == "json":
        provider.pop("status", None)
        click.echo(json.dumps(provider, indent=4, separators=(",", ": ")))
        return

    click.echo("\n----Provider Summary----\n")

    click.echo(
        "Name: "
        + highlight_text(provider_name)
        + " (uuid: "
        + highlight_text(provider["metadata"]["uuid"])
        + ")"
    )
    click.echo("Status: " + highlight_text(provider["status"]["state"]))
    click.echo(
        "Owner: " + highlight_text(provider["metadata"]["owner_reference"]["name"])
    )
    created_on = int(provider["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    provider_resources = provider.get("status").get("resources", {})
    click.echo("Infra Type: " + highlight_text(provider_resources["infra_type"]))
    click.echo("Provider Type: " + highlight_text(provider_resources["type"]))

    if provider_resources.get("action_list", []):
        click.echo(
            "Verify Action: "
            + highlight_text("Configured")
            + " (uuid: {})".format(
                highlight_text(provider_resources["action_list"][0]["uuid"])
            )
        )
    else:
        click.echo("Verify Action: " + highlight_text("Not Configured"))

    test_account = provider_resources.get("test_account")
    if test_account:
        click.echo(
            "Test Account: "
            + highlight_text(test_account["name"])
            + " (uuid: {})".format(highlight_text(test_account["uuid"]))
        )
    else:
        click.echo("Test Account: " + highlight_text("Not Configured"))

    if provider_resources.get("icon_reference"):
        click.echo(
            "Icon Name: "
            + highlight_text(provider_resources["icon_reference"].get("name", ""))
            + " (uuid: {})".format(
                highlight_text(provider_resources["icon_reference"]["uuid"])
            )
        )
    else:
        click.echo("Icon: " + highlight_text("Not Configured"))

    if provider_resources.get("credential_definition_list", []):
        click.echo("\nCredentials: " + highlight_text("Configured"))
        for cred in provider_resources["credential_definition_list"]:
            click.echo(
                "\tName: {}, Type: {}, Username: {} (uuid: {})".format(
                    highlight_text(cred["name"]),
                    highlight_text(cred["type"]),
                    highlight_text(cred["username"]),
                    highlight_text(cred["uuid"]),
                )
            )
    else:
        click.echo("Credentials: " + highlight_text("Not Configured"))

    def print_var_info(var_dict, tab_spaces=0):
        click.echo(
            "\t" * tab_spaces
            + "{}".format(
                highlight_text(
                    "{} ({}, {}, {})".format(
                        var_dict["label"] or var_dict["name"],
                        var_dict["val_type"],
                        var_dict["type"],
                        "Mandatory" if var_dict["is_mandatory"] else "Not Mandatory",
                    )
                )
            )
        )

    if provider_resources.get("endpoint_schema"):
        click.echo("\n" + "Endpoint Schema")
        click.echo(
            "\tType: " + highlight_text(provider_resources["endpoint_schema"]["type"])
        )
        endpoint_schema_variables = provider_resources["endpoint_schema"].get(
            "variable_list", []
        )
        if endpoint_schema_variables:
            click.echo("\tVariables")
            for schema_variable in endpoint_schema_variables:
                print_var_info(schema_variable, tab_spaces=2)

    auth_schema_list = provider["spec"]["resources"]["auth_schema_list"]
    click.echo("\nAuth Schema Variables")
    for schema_variable in auth_schema_list:
        if (provider_name == "NDB") and (schema_variable["name"] == "ndb__insecure"):
            continue
        print_var_info(schema_variable, tab_spaces=1)

    click.echo("\n----Resource Types Summary----")

    resource_types = provider_resources.get("resource_type_list")
    if resource_types:
        click.echo("\n" + "Resource Types")
        for resource_type in resource_types:
            click.echo(
                "\tName: {} (uuid: {})".format(
                    highlight_text(resource_type["name"]),
                    highlight_text(resource_type["uuid"]),
                )
            )
            tags = resource_type.get("tags")
            if tags:
                click.echo("\tResource Kind: {}".format(highlight_text(tags[0])))
            icon_reference = resource_type.get("icon_reference")
            if icon_reference:
                click.echo(
                    "\tIcon Name: "
                    + highlight_text(icon_reference.get("name", ""))
                    + " (uuid: {})".format(highlight_text(icon_reference["uuid"]))
                )
            else:
                click.echo("\tIcon: " + highlight_text("Not Configured"))
            actions = resource_type.get("action_list")
            if actions:
                click.echo(
                    "\tActions: {}".format(
                        highlight_text(", ".join([act["name"] for act in actions]))
                    )
                )
            schema_variables = resource_type.get("schema_list")
            if schema_variables:
                click.echo(
                    "\tSchema variables: {}".format(
                        highlight_text(
                            ", ".join([var["name"] for var in schema_variables])
                        )
                    )
                )
            variables = resource_type.get("variable_list")
            if variables:
                click.echo(
                    "\tVariables: {}".format(
                        highlight_text(", ".join([var["name"] for var in variables]))
                    )
                )
            click.echo()
    else:
        click.echo("\nResource Types: " + highlight_text("Not Configured") + "\n")


def create_provider_from_dsl(
    provider_file,
    name=None,
    force_create=False,
    icon_name=None,
    icon_file=None,
    passphrase=None,
):

    provider_payload = compile_provider(provider_file, for_create=True)

    if provider_payload is None:
        err_msg = "User provider not found in {}".format(provider_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    decompiled_secrets = decrypt_decompiled_secrets_file(
        pth=provider_file.rsplit("/", 1)[0]
    )
    if passphrase and not decompiled_secrets:
        LOG.warning("Decompiled secrets metadata not found. No need to pass passphrase")
    elif not passphrase and decompiled_secrets:
        LOG.warning(
            "Decompiled secrets metadata found. Use `--passphrase/-ps` cli option to create provider with decompiled secrets"
        )

    return create_provider(
        provider_payload,
        name=name,
        force_create=force_create,
        icon_name=icon_name,
        icon_file=icon_file,
        is_bulk_save=True,
        passphrase=passphrase,
        decompiled_secrets=decompiled_secrets,
    )


def compile_provider(provider_file, for_create=False):
    """Returns the compiled payload from an provider_file"""

    provider_module = get_provider_module_from_file(provider_file)
    CloudProviderClass = get_provider_class_from_module(provider_module)
    if CloudProviderClass is None:
        return None

    CloudProviderPayload = create_cloud_provider_payload(CloudProviderClass)
    cloud_provider_dict = CloudProviderPayload.get_dict()
    cloud_provider_resources_dict = cloud_provider_dict.get("spec", {}).get(
        "resources", {}
    )

    cred_name_uuid_map = {}
    credential_list = cloud_provider_resources_dict.get(
        "credential_definition_list", []
    )
    for cred in credential_list:
        if not cred.get("uuid"):
            cred["uuid"] = str(uuid.uuid4())
        cred_name_uuid_map[cred["name"]] = cred["uuid"]

    auth_schema_list = cloud_provider_resources_dict.get("auth_schema_list", [])
    for auth_schema_var in auth_schema_list:
        _prepare_var_dict(auth_schema_var, cred_name_uuid_map)

    variable_list = cloud_provider_resources_dict.get("variable_list", [])
    for variable in variable_list:
        _prepare_var_dict(variable, cred_name_uuid_map)

    test_account = cloud_provider_resources_dict.pop("test_account", None)
    if test_account:
        test_account["uuid"] = str(uuid.uuid4())
        test_account["type"] = cloud_provider_dict["spec"]["name"]
        for acc_var in test_account.get("data", {}).get("variable_list", []):
            _prepare_var_dict(acc_var, cred_name_uuid_map)
        cloud_provider_resources_dict["test_account"] = test_account

    endpoint_schema = cloud_provider_resources_dict.get("endpoint_schema")
    if endpoint_schema:
        for variable in endpoint_schema.get("variable_list", []):
            _prepare_var_dict(variable, cred_name_uuid_map)
    else:
        cloud_provider_resources_dict.pop("endpoint_schema", None)

    consolidated_action_list = []
    action_list = cloud_provider_resources_dict.get("action_list", [])
    if len(action_list) == 1:
        action_list_with_uuid = copy.deepcopy(action_list)
        modified_name_uuid_map = {
            name: {"non_action": uuid} for name, uuid in cred_name_uuid_map.items()
        }
        insert_uuid(  # Inserting uuids in action_list
            action=action_list[0],
            name_uuid_map=copy.deepcopy(modified_name_uuid_map),
            action_list_with_uuid=action_list_with_uuid[0],
        )
        cloud_provider_dict["spec"]["resources"]["action_list"] = action_list_with_uuid
        consolidated_action_list.extend(action_list_with_uuid)

    resource_type_list = cloud_provider_resources_dict.get("resource_type_list", [])
    for resource_type in resource_type_list:
        _prepare_resource_type_dict(
            resource_type,
            copy.deepcopy(cred_name_uuid_map),
            for_create=for_create,
        )
        consolidated_action_list.extend(resource_type["action_list"])

    for action in consolidated_action_list:
        for variable in action.get("runbook", {}).get("variable_list", []):
            _prepare_var_dict(variable, cred_name_uuid_map)

    return cloud_provider_dict


def get_provider_module_from_file(provider_file):
    """Returns Provider module given a provider dsl file (.py)"""
    return get_module_from_file("calm.dsl.cloud_provider", provider_file)


def get_provider_class_from_module(cloud_provider_module):
    """Returns provider class given a module"""

    CloudProviderClass = None
    for item in dir(cloud_provider_module):
        obj = getattr(cloud_provider_module, item)
        if isinstance(obj, (type(CloudProvider))):
            CloudProviderClass = obj

    return CloudProviderClass


def compile_provider_command(provider_file, out):

    provider_payload = compile_provider(provider_file)

    if provider_payload is None:
        LOG.error("User provider not found in {}".format(provider_file))
        return

    if out == "json":
        click.echo(json.dumps(provider_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(provider_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def get_providers(name, filter_by, limit, offset, quiet, all_items, out=None):
    """Get the providers, optionally filtered by a string"""

    client = get_api_client()
    ContextObj = get_context()

    params = {"length": limit, "offset": offset}

    filter_query = ""

    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if all_items:
        filter_query += get_states_filter(PROVIDER.STATES)

    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.provider.list(params)

    if err:
        server_config = ContextObj.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch providers from {}".format(pc_ip))
        return

    res = res.json()
    total_matches = res["metadata"]["total_matches"]
    if total_matches > limit:
        LOG.warning(
            "Displaying {} out of {} entities. Please use --limit and --offset option for more results.".format(
                limit, total_matches
            )
        )

    if out == "json":
        click.echo(json.dumps(res, indent=4, separators=(",", ": ")))
        return

    json_rows = res["entities"]
    if not json_rows:
        click.echo(highlight_text("No provider found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "PROVIDER TYPE",
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
                highlight_text(row["state"]),
                highlight_text(owner_reference_name),
                highlight_text(time.ctime(creation_time)),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(metadata["uuid"]),
            ]
        )
    click.echo(table)


def delete_provider_and_associated_rts_from_cache(provider_name, provider_uuid):
    try:
        LOG.debug("Deleting provider '{}' from cache".format(provider_name))
        Cache.delete_one(entity_type=CACHE.ENTITY.PROVIDER, uuid=provider_uuid)
        LOG.debug("Done")
    except Exception as exp:
        LOG.warning(
            "Exception while trying to delete provider from cache: {}".format(str(exp))
        )

    try:
        LOG.debug(
            "Deleting resource types corresponding to provider '{}' from cache".format(
                provider_name
            )
        )
        num_deleted_entities = ResourceTypeCache.delete_by_provider(provider_name)
        LOG.debug("Deleted {} resource types from cache".format(num_deleted_entities))
    except Exception as exp:
        LOG.warning(
            "Exception while trying to delete resource types from cache: {}".format(
                str(exp)
            )
        )


def delete_providers(provider_names):
    """Deletes one or more provider"""

    client = get_api_client()

    for name in provider_names:
        provider_uuid = get_provider_uuid(name=name)
        res, err = client.provider.delete(provider_uuid)
        if err:
            LOG.error("Delete of '{}' failed with error: {}".format(name, err["error"]))
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        LOG.debug("Response JSON: {0}".format(res.json()))
        LOG.info("{} deleted successfully".format(name))

        # Delete from cache too
        delete_provider_and_associated_rts_from_cache(name, provider_uuid)


def _render_action_execution(
    client, screen, provider_uuid, runlog_uuid, input_data=None, watch=True
):
    def poll_runlog_status():
        return client.provider.poll_action_run(provider_uuid, runlog_uuid)

    screen.refresh()
    should_continue = poll_action(poll_runlog_status, get_runlog_status(screen))
    if not should_continue:
        return

    res, err = client.provider.poll_action_run(provider_uuid, runlog_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    runbook = response["status"]["runbook_json"]["resources"]["runbook"]
    if watch:
        screen.refresh()

        def poll_func():
            return client.provider.list_child_runlogs(provider_uuid, runlog_uuid)

        def output_func(runlog_uuid, child_runlog_uuid):
            return client.provider.runlog_output(
                provider_uuid, runlog_uuid, child_runlog_uuid
            )

        watch_runbook(
            runlog_uuid,
            runbook,
            screen=screen,
            input_data=input_data,
            poll_function=poll_func,
            rerun_on_failure=False,
            output_function=output_func,
        )


def run_provider_or_resource_type_action(
    screen,
    entity_kind,
    entity_uuid,
    action,
    watch,
    payload={},
    provider_uuid=None,
):
    """Runs action confiugred on the provider or resource_type"""
    client = get_api_client()
    if entity_kind == ENTITY.KIND.PROVIDER:
        provider_uuid = entity_uuid
        run_fn = client.provider.run
    else:
        run_fn = client.resource_types.run
    res, err = run_fn(entity_uuid, action["uuid"], payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    runlog_uuid = response["status"]["runlog_uuid"]

    screen.clear()
    screen.print_at("Action '{}' queued for run".format(action["name"]), 0, 0)

    _render_action_execution(
        client,
        screen,
        provider_uuid,
        runlog_uuid,
        input_data=payload,
        watch=watch,
    )

    if not watch:
        server_config = get_context().get_server_config()
        provider_uuid = get_provider_uuid_from_runlog(client, runlog_uuid)
        run_url = (
            "https://{}:{}/dm/self_service/providers/runlogs/{}?entityId={}".format(
                server_config["pc_ip"],
                server_config["pc_port"],
                runlog_uuid,
                provider_uuid,
            )
        )
        screen.print_at(
            "Verify action execution url: {}".format(highlight_text(run_url)), 0, 0
        )
        action_type = (
            "provider-verify"
            if entity_kind == ENTITY.KIND.PROVIDER
            else "resource-type-action"
        )
        watch_cmd = "calm watch {}-execution {}".format(action_type, runlog_uuid)
        screen.print_at(
            "Command to watch the execution: {}".format(highlight_text(watch_cmd)), 0, 0
        )
    screen.refresh()


def parse_input_file(action, input_file):

    if file_exists(input_file) and input_file.endswith(".py"):
        input_variable_list = import_var_from_file(input_file, "variable_list", [])
    else:
        LOG.error("Invalid input_file passed! Must be a valid and existing.py file!")
        sys.exit(-1)

    args = []
    variable_list = action["runbook"].get("variable_list", [])
    for variable in variable_list:
        filtered_input_runtime_var = list(
            filter(lambda e: e["name"] == variable.get("name"), input_variable_list)
        )
        if len(filtered_input_runtime_var) == 1:
            new_val = filtered_input_runtime_var[0].get("value", "")
            if new_val:
                args.append(
                    {
                        "name": variable.get("name"),
                        "value": type(variable.get("value"))(new_val),
                    }
                )

    return {"spec": {"args": args}}


def prompt_and_set_input_values(action):
    args = []
    variable_list = action["runbook"].get("variable_list", [])
    for variable in variable_list:
        new_val = input(
            "Value for Variable {} in Runbook (default value={}): ".format(
                variable.get("name"), variable.get("value", "")
            )
        )
        if new_val:
            args.append(
                {
                    "name": variable.get("name"),
                    "value": type(variable.get("value"))(new_val),
                }
            )

    return {"spec": {"args": args}}


def get_payload(action, ignore_input_variables, input_file=None):
    payload = {}
    if input_file is None and not ignore_input_variables:
        payload = prompt_and_set_input_values(action)
    if input_file:
        payload = parse_input_file(action, input_file)
    return payload


def run_provider_verify_command(
    provider_name, watch, ignore_input_variables, input_file=None
):
    """Handle for run provier-verify command"""
    provider = get_provider(provider_name)
    provider_uuid = provider["metadata"]["uuid"]
    action_list = provider["status"]["resources"]["action_list"]
    if not action_list:
        LOG.error("Verify action not configured on the provider")
        sys.exit(-1)

    action = action_list[0]
    payload = get_payload(action, ignore_input_variables, input_file=input_file)

    def render_action_execution(screen):
        screen.clear()
        screen.refresh()
        run_provider_or_resource_type_action(
            screen, ENTITY.KIND.PROVIDER, provider_uuid, action, watch, payload=payload
        )
        screen.wait_for_input(10.0)

    Display.wrapper(render_action_execution, watch)


def watch_action_execution(runlog_uuid):
    """Watch test execution of a Provider/ResourceType action"""
    client = get_api_client()

    provider_uuid = get_provider_uuid_from_runlog(client, runlog_uuid)

    def render_execution_watch(screen):
        screen.clear()
        screen.refresh()
        _render_action_execution(client, screen, provider_uuid, runlog_uuid)
        screen.wait_for_input(10.0)

    Display.wrapper(render_execution_watch, True)


def abort_action_execution(runlog_uuid):
    """Abort test execution of a Provider/ResourceType action"""
    client = get_api_client()
    server_config = get_context().get_server_config()
    provider_uuid = get_provider_uuid_from_runlog(client, runlog_uuid)

    link = "https://{}:{}/dm/self_service/providers/runlogs/{}?entityId={}".format(
        server_config["pc_ip"], server_config["pc_port"], runlog_uuid, provider_uuid
    )

    def poll_func(runlog_uuid):
        return client.provider.poll_action_run(provider_uuid, runlog_uuid)

    def abort_func(runlog_uuid):
        return client.provider.abort(provider_uuid, runlog_uuid)

    abort_runbook_execution(
        runlog_uuid,
        poll_fn=poll_func,
        abort_fn=abort_func,
        link=link,
    )


def fetch_resource_type_by_name_and_provider_name(resource_type_name, provider_name):
    get_provider(provider_name)  # Validating if provider exists
    query_payload = {
        "filter": "name=={};provider_name=={};provider_type=={}".format(
            resource_type_name, provider_name, PROVIDER.TYPE.CUSTOM
        )
    }
    client = get_api_client()
    res, err = client.resource_types.list(payload=query_payload)
    if err:
        LOG.error("Error fetching resource_types: {}".format(err["error"]))
        sys.exit(-1)

    resource_types = res.json()["entities"]
    if not resource_types:
        LOG.error(
            "ResourceType '{}' not found under provider named '{}'".format(
                resource_type_name, provider_name
            )
        )
        sys.exit(-1)
    elif len(resource_types) > 1:
        LOG.error(
            "Multiple ResourceTypes named '{}' found under provider '{}'".format(
                resource_type_name, provider_name
            )
        )
        sys.exit(-1)
    return resource_types[0]


def run_resource_type_action_command(
    provider_name,
    resource_type_name,
    action_name,
    watch,
    ignore_input_variables,
    input_file=None,
):
    resource_type = fetch_resource_type_by_name_and_provider_name(
        resource_type_name, provider_name
    )
    provider_uuid = resource_type["status"]["resources"]["provider_reference"]["uuid"]
    resource_type_uuid = resource_type["metadata"]["uuid"]
    action_list = resource_type["status"]["action_list"]
    action = None
    for act in action_list:
        if act["name"] == action_name:
            action = act
            break
    if not action:
        LOG.error(
            "Action named '{}' not found under ResourceType '{}'".format(
                action_name, resource_type_name
            )
        )
        sys.exit(-1)

    payload = get_payload(action, ignore_input_variables, input_file=input_file)

    def render_action_execution(screen):
        screen.clear()
        screen.refresh()
        run_provider_or_resource_type_action(
            screen,
            ENTITY.KIND.RESOURCE_TYPE,
            resource_type_uuid,
            action,
            watch,
            payload=payload,
            provider_uuid=provider_uuid,
        )
        screen.wait_for_input(10.0)

    Display.wrapper(render_action_execution, watch)


def get_provider_from_cache(provider_name):
    """
    Attempts to fetch the provider entity from cache by name.
    If not found in existing cache, updates the cache implicitly & searches again
    """
    provider = Cache.get_entity_data(CACHE.ENTITY.PROVIDER, provider_name)
    if provider:
        return provider

    LOG.debug("Updating cache & attempting again")
    Cache.sync_table(CACHE.ENTITY.PROVIDER)
    return Cache.get_entity_data(CACHE.ENTITY.PROVIDER, provider_name)


def decompile_provider(
    name,
    provider_file,
    with_secrets=False,
    prefix="",
    provider_dir=None,
    passphrase=None,
    no_format=False,
):
    """helper to decompile provider"""

    if name and provider_file:
        LOG.error(
            "Please provide either provider file location or server provider name"
        )
        sys.exit(-1)

    if name:
        decompile_provider_from_server(
            name=name,
            with_secrets=with_secrets,
            prefix=prefix,
            provider_dir=provider_dir,
            passphrase=passphrase,
            no_format=no_format,
        )

    elif provider_file:
        decompile_provider_from_file(
            filename=provider_file,
            with_secrets=with_secrets,
            prefix=prefix,
            provider_dir=provider_dir,
            passphrase=passphrase,
            no_format=no_format,
        )

    else:
        LOG.error(
            "Please provide either provider file location or server provider name"
        )
        sys.exit(-1)


def decompile_provider_from_server(
    name,
    with_secrets=False,
    prefix="",
    provider_dir=None,
    passphrase=None,
    no_format=False,
):
    """decompiles the provider by fetching it from server, along with secrets"""

    client = get_api_client()
    provider = get_provider(name)
    provider_uuid = provider["metadata"]["uuid"]

    exported_provider_res, err = client.provider.export_file(
        provider_uuid, passphrase=passphrase
    )
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    exported_provider_res_payload = exported_provider_res.json()

    _decompile_provider(
        provider_payload=exported_provider_res_payload,
        with_secrets=with_secrets,
        prefix=prefix,
        provider_dir=provider_dir,
        contains_encrypted_secrets=True if passphrase else False,
        no_format=no_format,
    )


def decompile_provider_from_file(
    filename,
    with_secrets=False,
    prefix="",
    provider_dir=None,
    passphrase=None,
    no_format=False,
):
    """decompile provider from local provider file"""

    provider_payload = json.loads(open(filename).read())
    _decompile_provider(
        provider_payload=provider_payload,
        with_secrets=with_secrets,
        prefix=prefix,
        provider_dir=provider_dir,
        contains_encrypted_secrets=True if passphrase else False,
        no_format=no_format,
    )


def _decompile_provider(
    provider_payload,
    with_secrets=False,
    prefix="",
    provider_dir=None,
    contains_encrypted_secrets=False,
    no_format=False,
    **kwargs,
):
    """decompiles the provider from payload"""

    init_decompile_context()

    provider = provider_payload["spec"]["resources"]
    provider_name = provider_payload["spec"].get("name", "Dslprovider")
    provider_description = provider_payload["spec"].get("description", "")

    LOG.info("Decompiling provider {}".format(provider_name))

    prefix = get_valid_identifier(prefix)
    provider_cls = CloudProviderType.decompile(provider, prefix=prefix)
    provider_cls.__name__ = get_valid_identifier(provider_name)
    provider_cls.__doc__ = provider_description

    create_provider_dir(
        provider_cls=provider_cls,
        with_secrets=with_secrets,
        provider_dir=provider_dir,
        contains_encrypted_secrets=contains_encrypted_secrets,
        no_format=no_format,
    )
    click.echo(
        "\nSuccessfully decompiled. Directory location: {}. provider location: {}".format(
            get_provider_dir(), os.path.join(get_provider_dir(), "provider.py")
        )
    )


def get_provider_uuid_from_runlog(client, runlog_uuid):
    """
    Given a runlog_uuid, fetches the provider_uuid corresponding to it

    Args:
        client (Object): API Client object
        runlog_uuid (String): Runlog UUID
    Returns:
        (String) Provider UUID if a valid runlog
    Raises:
        Exception if runlog_uuid is not a valid provider/RT-action runlog
    """
    response, err = client.provider.list_runlogs(
        payload={
            "filter": "uuid=in={}".format(runlog_uuid)
        }  # workaround to use 'uuid=in=' instead of 'uuid==' mentioned in ENG-779820
    )
    if err:
        LOG.error("Error while fetching runlog info: {}".format(str(err)))
        sys.exit(-1)

    response_json = response.json()
    entities = response_json["entities"]
    if len(entities) != 1:
        LOG.error(
            "Runlog with UUID '{}' is not a valid provider/RT-Action runlog".format(
                runlog_uuid
            )
        )
        sys.exit(-1)
    return entities[0]["status"]["provider_reference"]["uuid"]


def format_provider_file(provider_file):
    path = pathlib.Path(provider_file)
    LOG.debug("Formatting provider {} using black".format(path))
    if format_file_in_place(
        path, fast=False, mode=FileMode(), write_back=WriteBack.DIFF
    ):
        LOG.info("Patching above diff to provider - {}".format(path))
        format_file_in_place(
            path, fast=False, mode=FileMode(), write_back=WriteBack.YES
        )
        LOG.info("All done!")
    else:
        LOG.info("Provider {} left unchanged.".format(path))
