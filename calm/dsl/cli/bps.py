import time
import json
import sys
import os
from pprint import pprint
import pathlib

from ruamel import yaml
import arrow
import click
from prettytable import PrettyTable
from black import format_file_in_place, WriteBack, FileMode

from calm.dsl.builtins import (
    Blueprint,
    SimpleBlueprint,
    VmBlueprint,
    create_blueprint_payload,
    BlueprintType,
    MetadataType,
    get_valid_identifier,
    file_exists,
    get_dsl_metadata_map,
    init_dsl_metadata_map,
)
from calm.dsl.builtins.models.metadata_payload import get_metadata_payload
from calm.dsl.config import get_context
from calm.dsl.api import get_api_client
from calm.dsl.store import Cache
from calm.dsl.decompile.decompile_render import create_bp_dir
from calm.dsl.decompile.file_handler import get_bp_dir

from .utils import (
    get_name_query,
    get_states_filter,
    highlight_text,
    import_var_from_file,
)
from .secrets import find_secret, create_secret
from .constants import BLUEPRINT
from calm.dsl.tools import get_module_from_file
from calm.dsl.builtins import Brownfield as BF
from calm.dsl.providers import get_provider
from calm.dsl.constants import CACHE
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def get_blueprint_list(name, filter_by, limit, offset, quiet, all_items, out):
    """Get the blueprints, optionally filtered by a string"""

    client = get_api_client()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if all_items:
        filter_query += get_states_filter(BLUEPRINT.STATES)
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.blueprint.list(params=params)

    if err:
        context = get_context()
        server_config = context.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch blueprints from {}".format(pc_ip))
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
        click.echo(highlight_text("No blueprint found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "BLUEPRINT TYPE",
        "APPLICATION COUNT",
        "PROJECT",
        "STATE",
        "CREATED ON",
        "LAST UPDATED",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]
        bp_type = (
            "Single VM"
            if "categories" in metadata
            and "TemplateType" in metadata["categories"]
            and metadata["categories"]["TemplateType"] == "Vm"
            else "Multi VM/Pod"
        )

        project = (
            metadata["project_reference"]["name"]
            if "project_reference" in metadata
            else None
        )

        creation_time = int(metadata["creation_time"]) // 1000000
        last_update_time = int(metadata["last_update_time"]) // 1000000

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(bp_type),
                highlight_text(row["application_count"]),
                highlight_text(project),
                highlight_text(row["state"]),
                highlight_text(time.ctime(creation_time)),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(row["uuid"]),
            ]
        )
    click.echo(table)


def describe_bp(blueprint_name, out):
    """Displays blueprint data"""

    client = get_api_client()
    bp = get_blueprint(client, blueprint_name, all=True)

    res, err = client.blueprint.read(bp["metadata"]["uuid"])
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    bp = res.json()

    if out == "json":
        bp.pop("status", None)
        click.echo(json.dumps(bp, indent=4, separators=(",", ": ")))
        return

    click.echo("\n----Blueprint Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(blueprint_name)
        + " (uuid: "
        + highlight_text(bp["metadata"]["uuid"])
        + ")"
    )
    click.echo("Description: " + highlight_text(bp["status"]["description"]))
    click.echo("Status: " + highlight_text(bp["status"]["state"]))
    click.echo(
        "Owner: " + highlight_text(bp["metadata"]["owner_reference"]["name"]), nl=False
    )
    click.echo(
        " Project: " + highlight_text(bp["metadata"]["project_reference"]["name"])
    )

    created_on = int(bp["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    bp_resources = bp.get("status").get("resources", {})
    profile_list = bp_resources.get("app_profile_list", [])
    click.echo("Application Profiles [{}]:".format(highlight_text(len(profile_list))))
    for profile in profile_list:
        profile_name = profile["name"]
        click.echo("\t" + highlight_text(profile_name))

        substrate_ids = [
            dep.get("substrate_local_reference", {}).get("uuid")
            for dep in profile.get("deployment_create_list", [])
        ]
        substrate_types = [
            sub.get("type")
            for sub in bp_resources.get("substrate_definition_list")
            if sub.get("uuid") in substrate_ids
        ]
        click.echo("\tSubstrates[{}]:".format(highlight_text(len(substrate_types))))
        click.echo("\t\t{}".format(highlight_text(", ".join(substrate_types))))

        click.echo("\tActions[{}]:".format(highlight_text(len(profile["action_list"]))))
        for action in profile["action_list"]:
            action_name = action["name"]
            if action_name.startswith("action_"):
                prefix_len = len("action_")
                action_name = action_name[prefix_len:]
            click.echo("\t\t" + highlight_text(action_name))

    service_list = (
        bp.get("status").get("resources", {}).get("service_definition_list", [])
    )
    click.echo("Services [{}]:".format(highlight_text(len(service_list))))
    for service in service_list:
        service_name = service["name"]
        click.echo("\t" + highlight_text(service_name))
        # click.echo("\tActions:")


def get_blueprint_module_from_file(bp_file):
    """Returns Blueprint module given a user blueprint dsl file (.py)"""
    return get_module_from_file("calm.dsl.user_bp", bp_file)


def get_blueprint_class_from_module(user_bp_module):
    """Returns blueprint class given a module"""

    UserBlueprint = None
    for item in dir(user_bp_module):
        obj = getattr(user_bp_module, item)
        if isinstance(obj, (type(Blueprint), type(SimpleBlueprint), type(VmBlueprint))):
            if obj.__bases__[0] in (Blueprint, SimpleBlueprint, VmBlueprint):
                UserBlueprint = obj

    return UserBlueprint


def get_brownfield_deployment_classes(brownfield_deployment_file=None):
    """Get brownfield deployment classes"""

    bf_deployments = []
    if not brownfield_deployment_file:
        return []

    bd_module = get_module_from_file(
        "calm.dsl.brownfield_deployment", brownfield_deployment_file
    )
    for item in dir(bd_module):
        obj = getattr(bd_module, item)
        if isinstance(obj, type(BF.Deployment)):
            if obj.__bases__[0] == (BF.Deployment):
                bf_deployments.append(obj)

    return bf_deployments


def compile_blueprint(bp_file, brownfield_deployment_file=None):

    # Constructing metadata payload
    # Note: This should be constructed before loading bp module. As metadata will be used while getting bp_payload
    metadata_payload = get_metadata_payload(bp_file)

    user_bp_module = get_blueprint_module_from_file(bp_file)
    UserBlueprint = get_blueprint_class_from_module(user_bp_module)
    if UserBlueprint is None:
        return None

    # Fetching bf_deployments
    bf_deployments = get_brownfield_deployment_classes(brownfield_deployment_file)
    if bf_deployments:
        bf_dep_map = {bd.__name__: bd for bd in bf_deployments}
        for pf in UserBlueprint.profiles:
            for ind, dep in enumerate(pf.deployments):
                if dep.__name__ in bf_dep_map:
                    bf_dep = bf_dep_map[dep.__name__]
                    # Add the packages and substrates from deployment
                    bf_dep.packages = dep.packages
                    bf_dep.substrate = dep.substrate

                    # If name attribute not exists in brownfield deployment file and given in blueprint file,
                    # Use the one that is given in blueprint file
                    if dep.name and (not bf_dep.name):
                        bf_dep.name = dep.name

                    # Replacing new deployment in profile.deployments
                    pf.deployments[ind] = bf_dep

    bp_payload = None
    if isinstance(UserBlueprint, type(SimpleBlueprint)):
        bp_payload = UserBlueprint.make_bp_dict()
    else:
        if isinstance(UserBlueprint, type(VmBlueprint)):
            UserBlueprint = UserBlueprint.make_bp_obj()

        UserBlueprintPayload, _ = create_blueprint_payload(
            UserBlueprint, metadata=metadata_payload
        )
        bp_payload = UserBlueprintPayload.get_dict()

        # Adding the display map to client attr
        display_name_map = get_dsl_metadata_map()
        bp_payload["spec"]["resources"]["client_attrs"] = {"None": display_name_map}

        # Note - Install/Uninstall runbooks are not actions in Packages.
        # Remove package actions after compiling.
        cdict = bp_payload["spec"]["resources"]
        for package in cdict["package_definition_list"]:
            if "action_list" in package:
                del package["action_list"]

    return bp_payload


def create_blueprint(
    client, bp_payload, name=None, description=None, force_create=False
):

    bp_payload.pop("status", None)

    credential_list = bp_payload["spec"]["resources"]["credential_definition_list"]
    for cred in credential_list:
        if cred["secret"].get("secret", None):
            secret = cred["secret"].pop("secret")

            try:
                value = find_secret(secret)

            except ValueError:
                click.echo(
                    "\nNo secret corresponding to '{}' found !!!\n".format(secret)
                )
                value = click.prompt("Please enter its value", hide_input=True)

                choice = click.prompt(
                    "\n{}(y/n)".format(highlight_text("Want to store it locally")),
                    default="n",
                )
                if choice[0] == "y":
                    create_secret(secret, value)

            cred["secret"]["value"] = value

    if name:
        bp_payload["spec"]["name"] = name
        bp_payload["metadata"]["name"] = name

    if description:
        bp_payload["spec"]["description"] = description

    bp_resources = bp_payload["spec"]["resources"]
    bp_name = bp_payload["spec"]["name"]
    bp_desc = bp_payload["spec"]["description"]
    bp_metadata = bp_payload["metadata"]

    return client.blueprint.upload_with_secrets(
        bp_name,
        bp_desc,
        bp_resources,
        bp_metadata=bp_metadata,
        force_create=force_create,
    )


def create_blueprint_from_json(
    client, path_to_json, name=None, description=None, force_create=False
):
    """
    creates blueprint from the bp json supplied.
    NOTE: Project mentioned in the json file remains unchanged
    """

    with open(path_to_json, "r") as f:
        bp_payload = json.loads(f.read())

    ContextObj = get_context()
    project_config = ContextObj.get_project_config()
    configured_project = project_config["name"]

    # If no project is given in payload, it is created with default project
    bp_project_name = "default"

    if (
        bp_payload.get("metadata")
        and bp_payload["metadata"].get("project_reference")
        and bp_payload["metadata"]["project_reference"].get("uuid")
    ):
        bp_project_uuid = bp_payload["metadata"]["project_reference"]["uuid"]
        if bp_project_uuid:
            bp_project_data = Cache.get_entity_data_using_uuid(
                entity_type=CACHE.ENTITY.PROJECT, uuid=bp_project_uuid
            )
            if bp_project_data:
                bp_project_name = bp_project_data["name"]

    if bp_project_name != configured_project:
        LOG.warning(
            "Project in supplied json is different from configured project('{}')".format(
                configured_project
            )
        )

    return create_blueprint(
        client,
        bp_payload,
        name=name,
        description=description,
        force_create=force_create,
    )


def create_blueprint_from_dsl(
    client, bp_file, name=None, description=None, force_create=False
):

    bp_payload = compile_blueprint(bp_file)
    if bp_payload is None:
        err_msg = "User blueprint not found in {}".format(bp_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    # Brownfield blueprints creation should be blocked using dsl file
    if bp_payload["spec"]["resources"].get("type", "") == "BROWNFIELD":
        LOG.error(
            "Command not allowed for brownfield blueprints. Please use 'calm create app -f <bp_file_location>' for creating brownfield application"
        )
        sys.exit(-1)

    return create_blueprint(
        client,
        bp_payload,
        name=name,
        description=description,
        force_create=force_create,
    )


def decompile_bp(name, bp_file, with_secrets=False, prefix="", bp_dir=None):
    """helper to decompile blueprint"""

    if name and bp_file:
        LOG.error(
            "Please provide either blueprint file location or server blueprint name"
        )
        sys.exit(-1)

    if name:
        decompile_bp_from_server(
            name=name, with_secrets=with_secrets, prefix=prefix, bp_dir=bp_dir
        )

    elif bp_file:
        decompile_bp_from_file(
            filename=bp_file, with_secrets=with_secrets, prefix=prefix, bp_dir=bp_dir
        )

    else:
        LOG.error(
            "Please provide either blueprint file location or server blueprint name"
        )
        sys.exit(-1)


def decompile_bp_from_server(name, with_secrets=False, prefix="", bp_dir=None):
    """decompiles the blueprint by fetching it from server"""

    client = get_api_client()
    blueprint = get_blueprint(client, name)
    bp_uuid = blueprint["metadata"]["uuid"]

    res, err = client.blueprint.export_file(bp_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    _decompile_bp(
        bp_payload=res, with_secrets=with_secrets, prefix=prefix, bp_dir=bp_dir
    )


def decompile_bp_from_file(filename, with_secrets=False, prefix="", bp_dir=None):
    """decompile blueprint from local blueprint file"""

    # ToDo - Fix this
    bp_payload = json.loads(open(filename).read())
    # bp_payload = read_spec(filename)
    _decompile_bp(
        bp_payload=bp_payload, with_secrets=with_secrets, prefix=prefix, bp_dir=bp_dir
    )


def _decompile_bp(bp_payload, with_secrets=False, prefix="", bp_dir=None):
    """decompiles the blueprint from payload"""

    blueprint = bp_payload["spec"]["resources"]
    blueprint_name = bp_payload["spec"].get("name", "DslBlueprint")
    blueprint_description = bp_payload["spec"].get("description", "")

    blueprint_metadata = bp_payload["metadata"]

    # POP unnecessary keys
    blueprint_metadata.pop("creation_time", None)
    blueprint_metadata.pop("last_update_time", None)

    metadata_obj = MetadataType.decompile(blueprint_metadata)

    # Copying dsl_name_map to global client_attrs
    if bp_payload["spec"]["resources"]["client_attrs"].get("None", {}):
        init_dsl_metadata_map(bp_payload["spec"]["resources"]["client_attrs"]["None"])

    LOG.info("Decompiling blueprint {}".format(blueprint_name))

    for sub_obj in blueprint.get("substrate_definition_list"):
        sub_type = sub_obj.get("type", "") or "AHV_VM"
        if sub_type == "K8S_POD":
            raise NotImplementedError(
                "Decompilation for k8s pod is not supported right now"
            )
        elif sub_type != "AHV_VM":
            LOG.warning(
                "Decompilation support for providers other than AHV is experimental."
            )
            break

    prefix = get_valid_identifier(prefix)
    bp_cls = BlueprintType.decompile(blueprint, prefix=prefix)
    bp_cls.__name__ = get_valid_identifier(blueprint_name)
    bp_cls.__doc__ = blueprint_description

    create_bp_dir(
        bp_cls=bp_cls,
        with_secrets=with_secrets,
        metadata_obj=metadata_obj,
        bp_dir=bp_dir,
    )
    click.echo(
        "\nSuccessfully decompiled. Directory location: {}. Blueprint location: {}".format(
            get_bp_dir(), os.path.join(get_bp_dir(), "blueprint.py")
        )
    )


def compile_blueprint_command(bp_file, brownfield_deployment_file, out):

    bp_payload = compile_blueprint(
        bp_file, brownfield_deployment_file=brownfield_deployment_file
    )
    if bp_payload is None:
        LOG.error("User blueprint not found in {}".format(bp_file))
        return

    credential_list = bp_payload["spec"]["resources"]["credential_definition_list"]
    is_secret_avl = False
    for cred in credential_list:
        if cred["secret"].get("secret", None):
            cred["secret"].pop("secret")
            is_secret_avl = True
            # At compile time, value will be empty
            cred["secret"]["value"] = ""

    if is_secret_avl:
        LOG.warning("Secrets are not shown in payload !!!")

    if out == "json":
        click.echo(json.dumps(bp_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(bp_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def format_blueprint_command(bp_file):
    path = pathlib.Path(bp_file)
    LOG.debug("Formatting blueprint {} using black".format(path))
    if format_file_in_place(
        path, fast=False, mode=FileMode(), write_back=WriteBack.DIFF
    ):
        LOG.info("Patching above diff to blueprint - {}".format(path))
        format_file_in_place(
            path, fast=False, mode=FileMode(), write_back=WriteBack.YES
        )
        LOG.info("All done!")
    else:
        LOG.info("Blueprint {} left unchanged.".format(path))


def get_blueprint(client, name, all=False, is_brownfield=False):

    # find bp
    params = {"filter": "name=={}".format(name)}
    if not all:
        params["filter"] += ";state!=DELETED"

    if is_brownfield:
        params["filter"] += ";type==BROWNFIELD"

    res, err = client.blueprint.list(params=params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    blueprint = None
    if entities:
        if len(entities) != 1:
            raise Exception("More than one blueprint found - {}".format(entities))

        LOG.info("{} found ".format(name))
        blueprint = entities[0]
    else:
        raise Exception("No blueprint found with name {} found".format(name))
    return blueprint


def get_blueprint_runtime_editables(client, blueprint):

    bp_uuid = blueprint.get("metadata", {}).get("uuid", None)
    if not bp_uuid:
        LOG.debug("Blueprint UUID not present in metadata")
        raise Exception("Invalid blueprint provided {} ".format(blueprint))
    res, err = client.blueprint._get_editables(bp_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    return response.get("resources", [])


def get_variable_value(variable, bp_data, launch_runtime_vars):
    """return variable value from launch_params/cli_prompt"""

    var_context = variable["context"]
    var_name = variable.get("name", "")

    # If launch_runtime_vars is given, return variable vlaue from it
    if launch_runtime_vars:
        return get_val_launch_runtime_var(
            launch_runtime_vars=launch_runtime_vars,
            field="value",  # Only 'value' attribute is editable
            path=var_name,
            context=var_context,
        )

    # Fetch the options for value of dynamic variables
    if variable["type"] in ["HTTP_LOCAL", "EXEC_LOCAL", "HTTP_SECRET", "EXEC_SECRET"]:
        choices, err = get_variable_value_options(
            bp_uuid=bp_data["metadata"]["uuid"], var_uuid=variable["uuid"]
        )
        if err:
            click.echo("")
            LOG.warning(
                "Exception occured while fetching value of variable '{}': {}".format(
                    var_name, err
                )
            )

        # Stripping out new line character from options
        choices = [_c.strip() for _c in choices]

    else:
        # Extract options for predefined variables from bp payload
        var_data = get_variable_data(
            bp_data=bp_data["status"]["resources"],
            context_data=bp_data["status"]["resources"],
            var_context=var_context,
            var_name=var_name,
        )
        choices = var_data.get("options", {}).get("choices", [])

    click.echo("")
    if choices:
        click.echo("Choose from given choices: ")
        for choice in choices:
            click.echo("\t{}".format(highlight_text(repr(choice))))

    # CASE for `type` in ['SECRET', 'EXEC_SECRET', 'HTTP_SECRET']
    hide_input = variable.get("type").split("_")[-1] == "SECRET"
    var_default_val = variable["value"].get("value", None)
    new_val = click.prompt(
        "Value for '{}' in {} [{}]".format(
            var_name, var_context, highlight_text(repr(var_default_val))
        ),
        default=var_default_val,
        show_default=False,
        hide_input=hide_input,
    )

    return new_val


def get_variable_data(bp_data, context_data, var_context, var_name):
    """return variable data from blueprint payload"""

    context_map = {
        "app_profile": "app_profile_list",
        "deployment": "deployment_create_list",
        "package": "package_definition_list",
        "service": "service_definition_list",
        "substrate": "substrate_definition_list",
        "action": "action_list",
        "runbook": "runbook",
    }

    # Converting to list
    context_list = var_context.split(".")
    i = 0

    # Iterate the list
    while i < len(context_list):
        entity_type = context_list[i]

        if entity_type in context_map:
            entity_type_val = context_map[entity_type]
            if entity_type_val in context_data:
                context_data = context_data[entity_type_val]
            else:
                context_data = bp_data[entity_type_val]
        elif entity_type == "variable":
            break

        else:
            LOG.error("Unknown entity type {}".format(entity_type))
            sys.exit(-1)

        entity_name = context_list[i + 1]
        if isinstance(context_data, list):
            for entity in context_data:
                if entity["name"] == entity_name:
                    context_data = entity
                    break

        # Increment iterator by two positions
        i = i + 2

    # Checking for the variable data
    for var in context_data["variable_list"]:
        if var_name == var["name"]:
            return var

    LOG.error("No data found with variable name {}".format(var_name))
    sys.exit(-1)


def get_val_launch_runtime_var(launch_runtime_vars, field, path, context):
    """Returns value of variable from launch_runtime_vars(Non-interactive)"""

    filtered_launch_runtime_vars = list(
        filter(
            lambda e: is_launch_runtime_vars_context_matching(e["context"], context)
            and e["name"] == path,
            launch_runtime_vars,
        )
    )
    if len(filtered_launch_runtime_vars) > 1:
        LOG.error(
            "Unable to populate runtime editables: Multiple matches for name {} and context {}".format(
                path, context
            )
        )
        sys.exit(-1)
    if len(filtered_launch_runtime_vars) == 1:
        return filtered_launch_runtime_vars[0].get("value", {}).get(field, None)
    return None


def get_val_launch_runtime_substrate(launch_runtime_substrates, path, context=None):
    """Returns value of substrate from launch_runtime_substrates(Non-interactive)"""

    filtered_launch_runtime_substrates = list(
        filter(lambda e: e["name"] == path, launch_runtime_substrates)
    )
    if len(filtered_launch_runtime_substrates) > 1:
        LOG.error(
            "Unable to populate runtime editables: Multiple matches for name {} and context {}".format(
                path, context
            )
        )
        sys.exit(-1)
    if len(filtered_launch_runtime_substrates) == 1:
        return filtered_launch_runtime_substrates[0].get("value", {})
    return None


def get_val_launch_runtime_deployment(launch_runtime_deployments, path, context=None):
    """Returns value of deployment from launch_runtime_deployments(Non-interactive)"""

    launch_runtime_deployments = list(
        filter(lambda e: e["name"] == path, launch_runtime_deployments)
    )
    if len(launch_runtime_deployments) > 1:
        LOG.error(
            "Unable to populate runtime editables: Multiple matches for name {} and context {}".format(
                path, context
            )
        )
        sys.exit(-1)
    if len(launch_runtime_deployments) == 1:
        return launch_runtime_deployments[0].get("value", {})
    return None


def get_val_launch_runtime_credential(launch_runtime_credentials, path, context=None):
    """Returns value of credential from launch_runtime_credentials(Non-interactive)"""

    launch_runtime_credentials = list(
        filter(lambda e: e["name"] == path, launch_runtime_credentials)
    )
    if len(launch_runtime_credentials) > 1:
        LOG.error(
            "Unable to populate runtime editables: Multiple matches for name {} and context {}".format(
                path, context
            )
        )
        sys.exit(-1)
    if len(launch_runtime_credentials) == 1:
        return launch_runtime_credentials[0].get("value", {})
    return None


def is_launch_runtime_vars_context_matching(launch_runtime_var_context, context):
    """Used for matching context of variables"""

    context_list = context.split(".")
    if len(context_list) > 1 and context_list[-1] == "variable":
        return context_list[-2] == launch_runtime_var_context or (
            is_launch_runtime_var_action_match(launch_runtime_var_context, context_list)
        )
    return False


def is_launch_runtime_var_action_match(launch_runtime_var_context, context_list):
    """Used for matching context of variable under action"""

    launch_runtime_var_context_list = launch_runtime_var_context.split(".")

    # Note: As variables under profile level actions can be marked as runtime_editable only
    # Context ex: app_profile.<profile_name>.action.<action_name>.runbook.<runbook_name>.variable
    if len(launch_runtime_var_context_list) == 2 and len(context_list) >= 4:
        if (
            context_list[1] == launch_runtime_var_context_list[0]
            and context_list[3] == launch_runtime_var_context_list[1]
        ):
            return True
    return False


def parse_launch_params_attribute(launch_params, parse_attribute):
    """Parses launch params and return value of parse_attribute i.e. variable_list, substrate_list, deployment_list, credenetial_list in file"""

    if launch_params:
        if file_exists(launch_params) and launch_params.endswith(".py"):
            return import_var_from_file(launch_params, parse_attribute, [])
        else:
            LOG.error(
                "Invalid launch_params passed! Must be a valid and existing.py file!"
            )
            sys.exit(-1)
    return []


def parse_launch_runtime_vars(launch_params):
    """Returns variable_list object from launch_params file"""

    return parse_launch_params_attribute(
        launch_params=launch_params, parse_attribute="variable_list"
    )


def parse_launch_runtime_substrates(launch_params):
    """Returns substrate_list object from launch_params file"""

    return parse_launch_params_attribute(
        launch_params=launch_params, parse_attribute="substrate_list"
    )


def parse_launch_runtime_deployments(launch_params):
    """Returns deployment_list object from launch_params file"""

    return parse_launch_params_attribute(
        launch_params=launch_params, parse_attribute="deployment_list"
    )


def parse_launch_runtime_credentials(launch_params):
    """Returns credential_list object from launch_params file"""

    return parse_launch_params_attribute(
        launch_params=launch_params, parse_attribute="credential_list"
    )


def get_variable_value_options(bp_uuid, var_uuid, poll_interval=10):
    """returns dynamic variable values and api exception if occured"""

    client = get_api_client()
    res, _ = client.blueprint.variable_values(uuid=bp_uuid, var_uuid=var_uuid)

    var_task_data = res.json()

    # req_id and trl_id are necessary
    req_id = var_task_data["request_id"]
    trl_id = var_task_data["trl_id"]

    # Poll till completion of epsilon task
    maxWait = 5 * 60
    count = 0
    while count < maxWait:
        res, err = client.blueprint.variable_values_from_trlid(
            uuid=bp_uuid, var_uuid=var_uuid, req_id=req_id, trl_id=trl_id
        )

        # If there is exception during variable api call, it would be silently ignored
        if err:
            return list(), err

        var_val_data = res.json()
        if var_val_data["state"] == "SUCCESS":
            return var_val_data["values"], None

        count += poll_interval
        time.sleep(poll_interval)

    LOG.error("Waited for 5 minutes for dynamic variable evaludation")
    sys.exit(-1)


def launch_blueprint_simple(
    blueprint_name=None,
    app_name=None,
    blueprint=None,
    profile_name=None,
    patch_editables=True,
    launch_params=None,
    is_brownfield=False,
):
    client = get_api_client()

    if app_name:
        LOG.info("Searching for existing applications with name {}".format(app_name))

        res, err = client.application.list(
            params={"filter": "name=={}".format(app_name)}
        )
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        total_matches = res["metadata"]["total_matches"]
        if total_matches:
            LOG.debug(res)
            LOG.error("Application Name ({}) is already used.".format(app_name))
            sys.exit(-1)

        LOG.info("No existing application found with name {}".format(app_name))

    if not blueprint:
        if is_brownfield:
            blueprint = get_blueprint(client, blueprint_name, is_brownfield=True)
        else:
            blueprint = get_blueprint(client, blueprint_name)

    blueprint_uuid = blueprint.get("metadata", {}).get("uuid", "")
    blueprint_name = blueprint_name or blueprint.get("metadata", {}).get("name", "")

    project_ref = blueprint["metadata"].get("project_reference", {})
    project_uuid = project_ref.get("uuid")
    bp_status = blueprint["status"]["state"]
    if bp_status != "ACTIVE":
        LOG.error("Blueprint is in {} state. Unable to launch it".format(bp_status))
        sys.exit(-1)

    LOG.info("Fetching runtime editables in the blueprint")
    profiles = get_blueprint_runtime_editables(client, blueprint)
    profile = None
    if profile_name is None:
        profile = profiles[0]
    else:
        for app_profile in profiles:
            app_prof_ref = app_profile.get("app_profile_reference", {})
            if app_prof_ref.get("name") == profile_name:
                profile = app_profile

                break
        if not profile:
            raise Exception("No profile found with name {}".format(profile_name))

    runtime_editables = profile.pop("runtime_editables", [])

    launch_payload = {
        "spec": {
            "app_name": app_name
            if app_name
            else "App-{}-{}".format(blueprint_name, int(time.time())),
            "app_description": "",
            "app_profile_reference": profile.get("app_profile_reference", {}),
            "runtime_editables": runtime_editables,
        }
    }

    if runtime_editables and patch_editables:
        runtime_editables_json = json.dumps(
            runtime_editables, indent=4, separators=(",", ": ")
        )
        click.echo("Blueprint editables are:\n{}".format(runtime_editables_json))

        # Check user input
        prompt_cli = bool(not launch_params)
        launch_runtime_vars = parse_launch_runtime_vars(launch_params)
        launch_runtime_substrates = parse_launch_runtime_substrates(launch_params)
        launch_runtime_deployments = parse_launch_runtime_deployments(launch_params)
        launch_runtime_credentials = parse_launch_runtime_credentials(launch_params)

        res, err = client.blueprint.read(blueprint_uuid)
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(-1)

        bp_data = res.json()

        substrate_list = runtime_editables.get("substrate_list", [])
        if substrate_list:
            if not launch_params:
                click.echo("\n\t\t\t", nl=False)
                click.secho("SUBSTRATE LIST DATA", underline=True, bold=True)

            substrate_definition_list = bp_data["status"]["resources"][
                "substrate_definition_list"
            ]
            package_definition_list = bp_data["status"]["resources"][
                "package_definition_list"
            ]
            substrate_name_data_map = {}
            for substrate in substrate_definition_list:
                substrate_name_data_map[substrate["name"]] = substrate

            vm_img_map = {}
            for package in package_definition_list:
                if package["type"] == "SUBSTRATE_IMAGE":
                    vm_img_map[package["name"]] = package["uuid"]

            for substrate in substrate_list:
                if launch_params:
                    new_val = get_val_launch_runtime_substrate(
                        launch_runtime_substrates=launch_runtime_substrates,
                        path=substrate.get("name"),
                        context=substrate.get("context", None),
                    )
                    if new_val:
                        substrate["value"] = new_val

                else:
                    provider_type = substrate["type"]
                    provider_cls = get_provider(provider_type)
                    provider_cls.get_runtime_editables(
                        substrate,
                        project_uuid,
                        substrate_name_data_map[substrate["name"]],
                        vm_img_map,
                    )

        bp_runtime_variables = runtime_editables.get("variable_list", [])

        # POP out action variables(Day2 action variables) bcz they cann't be given at bp launch time
        variable_list = []
        for _var in bp_runtime_variables:
            _var_context = _var["context"]
            context_list = _var_context.split(".")

            # If variable is defined under runbook(action), ignore it
            if len(context_list) >= 3 and context_list[-3] == "runbook":
                continue

            variable_list.append(_var)

        if variable_list:
            if not launch_params:
                click.echo("\n\t\t\t", nl=False)
                click.secho("VARIABLE LIST DATA", underline=True, bold=True)

            # NOTE: We are expecting only value in variables is editable (Ideal case)
            # If later any attribute added to editables, pls change here accordingly
            LOG.warning(
                "Values fetched from API/ESCRIPT will not have a default. User will have to select an option at launch."
            )
            for variable in variable_list:
                new_val = get_variable_value(
                    variable=variable,
                    bp_data=bp_data,
                    launch_runtime_vars=launch_runtime_vars,
                )
                if new_val:
                    variable["value"]["value"] = new_val

        deployment_list = runtime_editables.get("deployment_list", [])
        # deployment can be only supplied via non-interactive way for now
        if deployment_list and launch_params:
            for deployment in deployment_list:
                new_val = get_val_launch_runtime_deployment(
                    launch_runtime_deployments=launch_runtime_deployments,
                    path=deployment.get("name"),
                    context=deployment.get("context", None),
                )
                if new_val:
                    deployment["value"] = new_val

        credential_list = runtime_editables.get("credential_list", [])
        # credential can be only supplied via non-interactive way for now
        if credential_list and launch_params:
            for credential in credential_list:
                new_val = get_val_launch_runtime_credential(
                    launch_runtime_credentials=launch_runtime_credentials,
                    path=credential.get("name"),
                    context=credential.get("context", None),
                )
                if new_val:
                    credential["value"] = new_val

        runtime_editables_json = json.dumps(
            runtime_editables, indent=4, separators=(",", ": ")
        )
        LOG.info("Updated blueprint editables are:\n{}".format(runtime_editables_json))

    res, err = client.blueprint.launch(blueprint_uuid, launch_payload)
    if not err:
        LOG.info("Blueprint {} queued for launch".format(blueprint_name))
    else:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    response = res.json()
    launch_req_id = response["status"]["request_id"]

    poll_launch_status(client, blueprint_uuid, launch_req_id)


def poll_launch_status(client, blueprint_uuid, launch_req_id):
    # Poll every 10 seconds on the app status, for 5 mins
    maxWait = 5 * 60
    count = 0
    while count < maxWait:
        # call status api
        LOG.info("Polling status of Launch")
        res, err = client.blueprint.poll_launch(blueprint_uuid, launch_req_id)
        response = res.json()
        app_state = response["status"]["state"]
        pprint(response)
        if app_state == "success":
            app_uuid = response["status"]["application_uuid"]

            context = get_context()
            server_config = context.get_server_config()
            pc_ip = server_config["pc_ip"]
            pc_port = server_config["pc_port"]

            click.echo("Successfully launched. App uuid is: {}".format(app_uuid))

            LOG.info(
                "App url: https://{}:{}/console/#page/explore/calm/applications/{}".format(
                    pc_ip, pc_port, app_uuid
                )
            )
            break
        elif app_state == "failure":
            LOG.debug("API response: {}".format(response))
            LOG.error("Failed to launch blueprint. Check API response above.")
            break
        elif err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        LOG.info(app_state)
        count += 10
        time.sleep(10)


def delete_blueprint(blueprint_names):

    client = get_api_client()

    for blueprint_name in blueprint_names:
        blueprint = get_blueprint(client, blueprint_name)
        blueprint_id = blueprint["metadata"]["uuid"]
        res, err = client.blueprint.delete(blueprint_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        LOG.info("Blueprint {} deleted".format(blueprint_name))
