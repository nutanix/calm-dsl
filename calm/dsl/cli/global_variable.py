import json
import os
import time
import sys

from ruamel import yaml
import arrow
import click
from prettytable import PrettyTable

from calm.dsl.builtins import (
    MetadataType,
    get_valid_identifier,
)
from calm.dsl.decompile.decompile_render import create_global_variable_dir
from calm.dsl.decompile.file_handler import get_global_variable_dir
from calm.dsl.decompile.main import init_decompile_context

from calm.dsl.builtins.models.metadata_payload import get_metadata_payload
from calm.dsl.builtins.models.global_variable import GlobalVariableType

from calm.dsl.config import get_context
from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.constants import CACHE, DSL_CONFIG, VARIABLE
from calm.dsl.store import Cache
from calm.dsl.tools import get_module_from_file
from calm.dsl.cli.helper.common import get_variable_value_options

from .utils import (
    get_name_query,
    highlight_text,
    get_states_filter,
    _get_nested_messages,
)
from .constants import GLOBAL_VARIABLE

LOG = get_logging_handle(__name__)


def get_global_variable_list(name, filter_by, limit, offset, quiet, all_items, out):
    """Get the global variables, optionally filtered by a string"""

    client = get_api_client()
    context = get_context()
    server_config = context.get_server_config()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";" + filter_by

    # Check the states queryable
    if all_items:
        filter_query += get_states_filter(GLOBAL_VARIABLE.STATES)
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.global_variable.list(params=params)

    if err:
        pc_ip = server_config["pc_ip"]
        LOG.warning("Cannot fetch global variables from {}".format(pc_ip))
        return

    if out == "json":
        click.echo(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No global variables found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "DESCRIPTION",
        "STATE",
        "TYPE",
        "VALUE",
        "OWNER_PROJECT",
        "PROJECTS SHARED WITH",
        "CREATED BY",
        "LAST UPDATED",
        "UUID",
    ]

    EXEC_SCRIPT_TYPE_TO_DISPLAY_MAP = {
        "sh": "Shell",
        "npsscript": "Powershell",
        "static_py3": "eScript",
    }
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        created_by = metadata.get("owner_reference", {}).get("name", "-")
        last_update_time = int(metadata["last_update_time"]) // 1000000
        projects = []
        for project in row["resources"]["project_reference_list"]:
            projects.append(project["name"])
        owner_project = (
            row["resources"].get("owner_project_reference", {}).get("name", "")
        )
        var_type = row["resources"]["type"]
        var_options = row["resources"].get("options", {})
        display_var_type = ""
        if var_options:
            if (
                var_options.get("type", VARIABLE.OPTIONS.TYPE.PREDEFINED)
                == VARIABLE.OPTIONS.TYPE.PREDEFINED
            ):
                display_var_type = (
                    "Predefined"
                    if len(var_options.get("choices", [])) > 0
                    else "Simple"
                )
            elif (
                var_options.get("type", VARIABLE.OPTIONS.TYPE.PREDEFINED)
                == VARIABLE.OPTIONS.TYPE.EXEC
            ):
                script_type = var_options.get("attrs", {}).get("script_type", "")
                display_var_type = (
                    EXEC_SCRIPT_TYPE_TO_DISPLAY_MAP[script_type]
                    if script_type
                    else "EXEC"
                )
            else:
                display_var_type = "HTTP"

        if var_type in [
            VARIABLE.TYPE.SECRET,
            VARIABLE.TYPE.EXEC_SECRET,
            VARIABLE.TYPE.HTTP_SECRET,
        ]:
            display_var_type = display_var_type + " (SECRET)"

        value = row["resources"]["value"]
        if var_type in VARIABLE.DYNAMIC_TYPES:
            value = "DYNAMIC VALUE"

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["description"]),
                highlight_text(row["state"]),
                highlight_text(display_var_type),
                highlight_text(value),
                highlight_text(owner_project),
                highlight_text(",".join(projects)),
                highlight_text(created_by),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(metadata["uuid"]),
            ]
        )
    click.echo(table)


def get_global_variable(client, name, all=False):
    """Get the global variable with the given name"""

    params = {"filter": "name=={}".format(name)}
    if not all:
        params["filter"] += ";deleted==FALSE"
    else:
        params["filter"] += get_states_filter(GLOBAL_VARIABLE.STATES)

    res, err = client.global_variable.list(params=params)

    if err:
        return None, err

    response = res.json()
    entities = response.get("entities", None)

    global_variable = None
    if entities:
        if len(entities) != 1:
            LOG.error("More than one global variable found - {}".format(entities))
            sys.exit("More than one global variable found")
        LOG.info("{} found ".format(name))
        global_variable = entities[0]
    else:
        LOG.error("No global variable found with name {}".format(name))
        sys.exit("No global variable found with name {}".format(name))

    return global_variable


def create_update_global_variable(
    client,
    global_variable_payload,
    name=None,
    description=None,
    is_create=False,
    force_create=False,
):
    global_variable_payload.pop("status", None)
    global_variable_payload.get("metadata").pop("uuid", None)
    global_variable_payload.get("metadata").pop("last_update_time", None)
    global_variable_payload.get("metadata").pop("owner_reference", None)
    global_variable_payload.get("metadata").pop("creation_time", None)

    if name:
        global_variable_payload["spec"]["name"] = name
    else:
        name = global_variable_payload.get("spec", {}).get("name", "")

    if description:
        global_variable_payload["spec"]["description"] = description

    global_variable_payload["metadata"]["name"] = name

    if is_create:
        # check if variable with the given name already exists
        params = {"filter": "name=={}".format(name)}
        res, err = client.global_variable.list(params=params)

        if err:
            return None, err

        response = res.json()
        entities = response.get("entities", None)

        if entities:
            if len(entities) > 0:
                if not force_create:
                    err_msg = "Global variable item {} already exists. Use --force to delete existing global variable item before create.".format(
                        name
                    )

                    err = {"error": err_msg, "code": -1}
                    return None, err

                # --force option used in create. Delete existing task library item with same name.
                gv_uuid = entities[0]["metadata"]["uuid"]
                _, err = client.global_variable.delete(gv_uuid)
                if err:
                    return None, err

        res, err = client.global_variable.create(global_variable_payload)
        if err:
            LOG.error("Failed to create Global variable item {}".format(name))
            sys.exit("[{}] - {}".format(err["code"], err["error"]))

    else:
        global_variable = get_global_variable(client, name)
        gv_uuid = global_variable["metadata"]["uuid"]
        global_variable_payload["metadata"]["spec_version"] = global_variable[
            "metadata"
        ]["spec_version"]

        res, err = client.global_variable.update(gv_uuid, global_variable_payload)
        if err:
            LOG.error("Failed to update Global variable item {}".format(name))
            sys.exit("[{}] - {}".format(err["code"], err["error"]))

    return res, err


def get_global_variable_classes(global_variable_file=None):
    """Get global variable deployment classes"""

    global_variable_item = None
    if not global_variable_file:
        return []

    tl_module = get_module_from_file("calm.dsl.global_variable", global_variable_file)
    for item in dir(tl_module):
        obj = getattr(tl_module, item)
        if isinstance(obj, type(GlobalVariableType)):
            if type(obj) == (GlobalVariableType):
                global_variable_item = obj
                if getattr(global_variable_item.definition, "name", None) is None:
                    setattr(global_variable_item.definition, "name", item)

    return global_variable_item


def create_global_variable_payload(gv_dict, metadata_payload):
    """Create Global variable payload"""

    name = gv_dict.pop("name", "")

    if not name:
        LOG.error("Global variable name is required")
        sys.exit("Global variable name is required")

    description = gv_dict.pop("description", "")

    if gv_dict["type"] in VARIABLE.SECRET_TYPES:
        gv_dict["attrs"] = {
            "is_secret_modified": True,
            "type": VARIABLE.SECRET_ATTRS_TYPE,
        }

    if gv_dict["type"] in [
        VARIABLE.TYPE.EXEC_LOCAL,
        VARIABLE.TYPE.HTTP_LOCAL,
        VARIABLE.TYPE.EXEC_SECRET,
        VARIABLE.TYPE.HTTP_SECRET,
    ]:
        ep = gv_dict["options"].get("exec_target_reference", None)
        if ep:
            endpoint = fetch_endpoint(ep.get("name", ""))
            ep["uuid"] = endpoint["metadata"]["uuid"]

    if (
        gv_dict["type"] in [VARIABLE.TYPE.LOCAL, VARIABLE.TYPE.SECRET]
        and "options" not in gv_dict
    ):
        gv_dict["options"] = {}
        gv_dict["options"]["type"] = VARIABLE.OPTIONS.TYPE.PREDEFINED
        gv_dict["options"]["choices"] = []

    gv_payload = {
        "spec": {
            "name": name,
            "description": description,
            "resources": gv_dict,
        },
        "metadata": metadata_payload,
        "api_version": "3.0",
    }

    return gv_payload


def remove_invalid_keys(var_dict):
    invalid_keys = ["is_hidden", "is_mandatory", "editables"]

    for invalid_key in invalid_keys:
        if invalid_key in var_dict:
            del var_dict[invalid_key]


def compile_global_variable(global_variable_file):
    metadata_payload = get_metadata_payload(global_variable_file)

    gv_dict = None
    GlobalVariableItem = get_global_variable_classes(global_variable_file)
    gv_dict = GlobalVariableItem.get_dict()

    definition = gv_dict.get("definition", {})
    projects = gv_dict.get("project_reference_list", [])
    project_reference_list = []

    for name in projects:
        project_cache_data = Cache.get_entity_data(
            entity_type=CACHE.ENTITY.PROJECT, name=name
        )
        if not project_cache_data:
            LOG.error(
                "Project {} not found. Please run: calm update cache".format(name)
            )
            sys.exit("Project {} not found. Please run: calm update cache".format(name))

        project_reference_list.append(project_cache_data["uuid"])

    definition["project_reference_list"] = project_reference_list
    remove_invalid_keys(definition)

    metadata_payload["kind"] = "global_variable"
    metadata_payload["name"] = definition.get("name", "")

    ContextObj = get_context()
    project_config = ContextObj.get_project_config()

    if "project_reference" not in metadata_payload:
        project_name = project_config["name"]
        if project_name == DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME:
            LOG.error(DSL_CONFIG.EMPTY_PROJECT_MESSAGE)
            sys.exit("Invalid project configuration")

        metadata_payload["project_reference"] = Ref.Project(project_name)

    gv_payload = create_global_variable_payload(definition, metadata_payload)

    return gv_payload


def create_update_global_variable_from_json(
    client,
    global_variable_file,
    name=None,
    description=None,
    is_create=False,
    force_create=False,
):
    """Create global variable from json"""

    with open(global_variable_file, "r") as f:
        global_variable_payload = json.loads(f.read())

    metadata_payload = global_variable_payload.get("metadata", {})
    ContextObj = get_context()
    project_config = ContextObj.get_project_config()

    if "project_reference" not in metadata_payload:
        project_name = project_config["name"]
        if project_name == DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME:
            LOG.error(DSL_CONFIG.EMPTY_PROJECT_MESSAGE)
            sys.exit("Invalid project configuration")

        metadata_payload["project_reference"] = Ref.Project(project_name)

    return create_update_global_variable(
        client,
        global_variable_payload,
        name=name,
        description=description,
        is_create=is_create,
        force_create=force_create,
    )


def create_update_global_variable_from_dsl(
    client,
    global_variable_file,
    name=None,
    description=None,
    is_create=False,
    force_create=False,
):
    global_variable_payload = compile_global_variable(global_variable_file)

    return create_update_global_variable(
        client,
        global_variable_payload,
        name=name,
        description=description,
        is_create=is_create,
        force_create=force_create,
    )


def display_global_variable_details(response, is_create=False):
    """Display global variable details as per api response"""

    global_variable = response.json()
    global_variable_uuid = global_variable["metadata"]["uuid"]
    global_variable_name = global_variable["metadata"]["name"]
    global_variable_status = global_variable.get("status", {})
    global_variable_state = global_variable_status.get("state", "DRAFT")
    LOG.debug(
        "Global variable {} has state: {}".format(
            global_variable_name, global_variable_state
        )
    )

    action = "created" if is_create else "updated"

    if global_variable_state != "ACTIVE":
        msg_list = []
        _get_nested_messages("", global_variable_status, msg_list)

        if not msg_list:
            LOG.error(
                "Global variable {} {} with errors.".format(
                    global_variable_name, action
                )
            )
            LOG.debug(json.dumps(global_variable_status))
            sys.exit(
                "Global variable {} {} with errors.".format(
                    global_variable_name, action
                )
            )

        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        LOG.error(
            "Global variable {} {} with {} error(s): {}".format(
                global_variable_name, action, len(msg_list), msgs
            )
        )
        sys.exit(
            "Global variable {} {} with {} error(s): {}".format(
                global_variable_name, action, len(msg_list), msgs
            )
        )

    LOG.info("Global variable {} {} successfully.".format(global_variable_name, action))
    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    link = "https://{}:{}/dm/self_service/variables/{}".format(
        pc_ip, pc_port, global_variable_uuid
    )
    stdout_dict = {
        "name": global_variable_name,
        "link": link,
        "state": global_variable_state,
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))


def create_global_variable_command(global_variable_file, name, description, force):
    """Creates a global variable"""

    client = get_api_client()

    if global_variable_file.endswith(".json"):
        res, err = create_update_global_variable_from_json(
            client,
            global_variable_file,
            name=name,
            description=description,
            is_create=True,
            force_create=force,
        )
    elif global_variable_file.endswith(".py"):
        res, err = create_update_global_variable_from_dsl(
            client,
            global_variable_file,
            name=name,
            description=description,
            is_create=True,
            force_create=force,
        )
    else:
        LOG.error("Unknown file format {}".format(global_variable_file))
        return

    if err:
        LOG.error(err["error"])
        return

    display_global_variable_details(res, is_create=True)


def update_global_variable_command(global_variable_file, name, description):
    """Updates a global variable"""

    client = get_api_client()

    if global_variable_file.endswith(".json"):
        res, err = create_update_global_variable_from_json(
            client, global_variable_file, name=name, description=description
        )
    elif global_variable_file.endswith(".py"):
        res, err = create_update_global_variable_from_dsl(
            client, global_variable_file, name=name, description=description
        )
    else:
        LOG.error("Unknown file format {}".format(global_variable_file))
        return

    if err:
        LOG.error(err["error"])
        return

    display_global_variable_details(res)


def delete_global_variable(gv_names):

    client = get_api_client()

    for gv_name in gv_names:
        global_variable = get_global_variable(client, gv_name)
        gv_uuid = global_variable["metadata"]["uuid"]
        res, err = client.global_variable.delete(gv_uuid)
        if err:
            LOG.error("Global variable delete failed")
            sys.exit("[{}] - {}".format(err["code"], err["error"]))
        LOG.info("Global variable item {} deleted".format(gv_name))


def describe_global_variable(gv_name, out):
    """Displays global variable data"""

    client = get_api_client()
    global_variable = get_global_variable(client, gv_name, all=True)

    res, err = client.global_variable.read(global_variable["metadata"]["uuid"])
    if err:
        LOG.error("Global variable get failed")
        sys.exit("[{}] - {}".format(err["code"], err["error"]))

    global_variable = res.json()

    if out == "json":
        global_variable.pop("status", None)
        click.echo(json.dumps(global_variable, indent=4, separators=(",", ": ")))
        return

    click.echo("\n----Global variable summary----\n")
    click.echo(
        "Name: "
        + highlight_text(gv_name)
        + " (uuid: "
        + highlight_text(global_variable["metadata"]["uuid"])
        + ")"
    )
    click.echo(
        "Description: " + highlight_text(global_variable["status"]["description"])
    )
    click.echo("Status: " + highlight_text(global_variable["status"]["state"]))
    click.echo(
        "Type: " + highlight_text(global_variable["status"]["resources"]["type"])
    )
    click.echo(
        "Value: " + highlight_text(global_variable["status"]["resources"]["value"])
    )
    click.echo(
        "Owner: "
        + highlight_text(global_variable["metadata"]["owner_reference"]["name"])
    )
    project = global_variable["metadata"].get("project_reference", {})
    click.echo("Owner Project: " + highlight_text(project.get("name", "")))

    project_shared_list = global_variable["status"]["resources"].get(
        "project_reference_list", []
    )
    projects = []
    for project in project_shared_list:
        projects.append(project["name"])
    click.echo("Projects shared with: " + highlight_text(",".join(projects)))

    created_on = int(global_variable["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    last_updated = int(global_variable["metadata"]["last_update_time"]) // 1000000
    past = arrow.get(last_updated).humanize()
    click.echo(
        "Last Updated: {} ({})\n".format(
            highlight_text(time.ctime(last_updated)), highlight_text(past)
        )
    )


def compile_global_variable_command(global_variable_file, out):

    gv_payload = compile_global_variable(global_variable_file)
    if gv_payload is None:
        LOG.error("Global variable not found in {}".format(global_variable_file))
        return

    if out == "json":
        click.echo(json.dumps(gv_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(gv_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def _decompile_global_variable(
    global_variable_payload, global_variable_dir, prefix, no_format=False
):
    """decompiles the global variable from payload"""

    global_variable = global_variable_payload["status"]["resources"]
    global_variable_name = global_variable_payload["status"].get("name", "")
    global_variable_description = global_variable_payload["status"].get(
        "description", ""
    )
    gv_shared_projects = global_variable.get("project_reference_list", [])

    global_variable["name"] = global_variable_name
    global_variable["description"] = global_variable_description
    global_variable["project_reference_list"] = [
        proj["uuid"] for proj in gv_shared_projects
    ]

    LOG.info("Decompiling global variable {}".format(global_variable_name))

    prefix = get_valid_identifier(prefix)
    global_variable_cls = GlobalVariableType.decompile(global_variable, prefix=prefix)
    global_variable_cls.__name__ = get_valid_identifier(global_variable_name)
    global_variable_cls.__doc__ = global_variable_description

    gv_metadata = global_variable_payload["metadata"]
    # POP unnecessary keys
    gv_metadata.pop("creation_time", None)
    gv_metadata.pop("last_update_time", None)

    metadata_obj = MetadataType.decompile(gv_metadata)

    create_global_variable_dir(
        global_variable_cls=global_variable_cls,
        global_variable_dir=global_variable_dir,
        metadata_obj=metadata_obj,
        no_format=no_format,
    )
    click.echo(
        "\nSuccessfully decompiled. Directory location: {}. global variable location: {}".format(
            get_global_variable_dir(),
            os.path.join(get_global_variable_dir(), "global_variable.py"),
        )
    )


def decompile_global_variable_from_server(
    name, global_variable_dir, prefix, no_format=False
):
    """decompiles the global variable by fetching it from server"""

    client = get_api_client()
    global_variable = get_global_variable(client, name)
    global_variable_uuid = global_variable["status"]["uuid"]
    res, err = client.global_variable.read(global_variable_uuid)
    if err:
        LOG.error("Global variable read failed")
        sys.exit("[{}] - {}".format(err["code"], err["error"]))

    global_variable = res.json()
    _decompile_global_variable(
        global_variable_payload=global_variable,
        global_variable_dir=global_variable_dir,
        prefix=prefix,
        no_format=no_format,
    )


def decompile_global_variable_from_file(
    filename, global_variable_dir, prefix, no_format=False
):
    """decompile global variable from local global variable file"""

    if filename.endswith(".json"):
        global_variable_payload = json.loads(open(filename).read())
    else:
        LOG.error("File - {} format is not of type json".format(filename))
        sys.exit("File - {} format is not of type json".format(filename))

    _decompile_global_variable(
        global_variable_payload=global_variable_payload,
        global_variable_dir=global_variable_dir,
        prefix=prefix,
        no_format=no_format,
    )


def decompile_global_variable_command(
    name, global_variable_file, prefix="", global_variable_dir=None, no_format=False
):
    """helper to decompile global variable"""
    if name and global_variable_file:
        LOG.error(
            "Please provide either global variable file location or server global variable name"
        )
        sys.exit("Both global variable name and file location provided.")
    init_decompile_context()
    if name:
        decompile_global_variable_from_server(
            name=name,
            global_variable_dir=global_variable_dir,
            prefix=prefix,
            no_format=no_format,
        )
    elif global_variable_file:
        decompile_global_variable_from_file(
            filename=global_variable_file,
            global_variable_dir=global_variable_dir,
            prefix=prefix,
            no_format=no_format,
        )
    else:
        LOG.error(
            "Please provide either global variable file location or server global variable name"
        )
        sys.exit("Global variable name or file location not provided.")


def get_global_variable_usage(name):
    """Get global variable usage"""

    client = get_api_client()
    global_variable = get_global_variable(client, name)
    gv_uuid = global_variable["metadata"]["uuid"]
    res, err = client.global_variable.usage(gv_uuid)
    if err:
        LOG.error("Global variable usage call failed")
        sys.exit("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()

    if any(count > 0 for count in response["status"]["usage"].values()):
        table = PrettyTable()
        table.field_names = [
            "ENTITY TYPE",
            "ENTITY NAME(S)",
        ]
        table.add_row(
            [
                highlight_text("Runbook"),
                highlight_text(
                    ", ".join(
                        [
                            item["name"]
                            for item in response["status"]["resources"]["runbook_list"]
                        ]
                    )
                ),
            ]
        )
        table.add_row(
            [
                highlight_text("Blueprint"),
                highlight_text(
                    ", ".join(
                        [
                            item["name"]
                            for item in response["status"]["resources"][
                                "blueprint_list"
                            ]
                        ]
                    )
                ),
            ]
        )
        table.add_row(
            [
                highlight_text("Marketplace Item"),
                highlight_text(
                    ", ".join(
                        [
                            item["name"]
                            for item in response["status"]["resources"][
                                "marketplace_item_list"
                            ]
                        ]
                    )
                ),
            ]
        )
        table.add_row(
            [
                highlight_text("Application"),
                highlight_text(
                    ", ".join(
                        [
                            item["name"]
                            for item in response["status"]["resources"]["app_list"]
                        ]
                    )
                ),
            ]
        )
        click.echo(table)
    else:
        click.echo("Global variable {} is not used in any entity.".format(name))


def fetch_endpoint(name):

    client = get_api_client()

    params = {}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])

    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.endpoint.list(params=params)

    if err:
        ContextObj = get_context()
        server_config = ContextObj.get_server_config()
        pc_ip = server_config["pc_ip"]
        LOG.warning("Cannot fetch endpoints from {}".format(pc_ip))
        return

    json_rows = res.json()["entities"]

    if len(json_rows) == 0:
        LOG.error("No endpoint found with name {}".format(name))
        sys.exit("No endpoint found with name {}".format(name))
    if len(json_rows) > 1:
        LOG.error("More than one endpoint found with name {}".format(name))
        sys.exit("More than one endpoint found with name {}".format(name))

    return json_rows[0]


def get_global_variable_list_by_names(names):
    """Fetch global variable list by names"""
    client = get_api_client()

    filter_query = get_name_query(names)
    params = {"filter": filter_query}

    res, err = client.global_variable.list(params=params)
    if err:
        LOG.warning(
            "Cannot fetch global variables from server for names {}".format(names)
        )
        return []

    response = res.json()
    entities = response.get("entities", [])
    return entities


def fetch_dynamic_global_variable_values(entity_type, entity_uuid, names):
    """Fetch dynamic global variable values by names"""

    global_args = []
    gv_list = get_global_variable_list_by_names(names)
    for gv in gv_list:
        name = gv.get("metadata", {}).get("name", "")
        var_type = gv["status"]["resources"]["type"]
        if name not in names:
            continue

        if var_type in GLOBAL_VARIABLE.DYNAMIC_VARIABLE_TYPES:
            if entity_type in ["blueprint", "runbook", "marketplace_item"]:
                choices, err = get_variable_value_options(
                    entity_type=entity_type,
                    entity_uuid=entity_uuid,
                    var_uuid=gv["metadata"]["uuid"],
                    is_global=True,
                )
                if err:
                    click.echo("")
                    LOG.warning(
                        "Exception occured while fetching value of variable '{}': {}".format(
                            name, err
                        )
                    )

                # Stripping out new line character from options
                choices = [_c.strip() for _c in choices]
        else:
            choices = gv["status"]["resources"].get("options", {}).get("choices", [])

        click.echo("")
        if choices:
            click.echo("Choose from given choices: ")
            for choice in choices:
                click.echo("\t{}".format(highlight_text(repr(choice))))

            hide_input = var_type.split("_")[-1] == "SECRET"
            new_val = click.prompt(
                "Value for Global Variable '{}' ".format(name),
                hide_input=hide_input,
            )
            if new_val:
                global_args.append(
                    {
                        "name": name,
                        "value": type(gv["status"]["resources"].get("value", ""))(
                            new_val
                        ),
                    }
                )

    return global_args
