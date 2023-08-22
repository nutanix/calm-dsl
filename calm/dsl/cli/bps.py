from re import sub
import time
import json
import sys
import os
import uuid
from pprint import pprint
import pathlib

from ruamel import yaml
import arrow
import click
from prettytable import PrettyTable
from copy import deepcopy
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
from calm.dsl.decompile.bp_file_helper import decrypt_decompiled_secrets_file
from calm.dsl.decompile.main import init_decompile_context

from .utils import (
    get_name_query,
    get_states_filter,
    highlight_text,
    import_var_from_file,
)
from .secrets import find_secret, create_secret
from .constants import BLUEPRINT
from .environments import get_project_environment
from calm.dsl.tools import get_module_from_file
from calm.dsl.builtins import Brownfield as BF
from calm.dsl.providers import get_provider
from calm.dsl.providers.plugins.ahv_vm.main import AhvNew
from calm.dsl.constants import CACHE, DSL_CONFIG
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins.models.calm_ref import Ref

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
    bp = get_blueprint(blueprint_name, all=True)

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

        bp_deployments = profile.get("deployment_create_list", [])
        click.echo("\tDeployments[{}]:".format(highlight_text(len(bp_deployments))))
        for dep in bp_deployments:
            click.echo("\t\t{}".format(highlight_text(dep["name"])))

            dep_substrate = None
            for sub in bp_resources.get("substrate_definition_list"):
                if sub.get("uuid") == dep.get("substrate_local_reference", {}).get(
                    "uuid"
                ):
                    dep_substrate = sub

            sub_type = dep_substrate.get("type", "")
            account = None
            if sub_type != "EXISTING_VM":
                account_uuid = dep_substrate["create_spec"]["resources"]["account_uuid"]
                account_cache_data = Cache.get_entity_data_using_uuid(
                    entity_type=CACHE.ENTITY.ACCOUNT, uuid=account_uuid
                )
                if sub_type == "AHV_VM":
                    account_uuid = account_cache_data["data"]["pc_account_uuid"]
                    account_cache_data = Cache.get_entity_data_using_uuid(
                        entity_type=CACHE.ENTITY.ACCOUNT, uuid=account_uuid
                    )

                account = account_cache_data["name"]

            click.echo("\t\tSubstrate:")
            click.echo("\t\t\t{}".format(highlight_text(dep_substrate["name"])))
            click.echo("\t\t\tType: {}".format(highlight_text(sub_type)))
            if account:
                click.echo("\t\t\tAccount: {}".format(highlight_text(account)))

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

    ContextObj = get_context()
    project_config = ContextObj.get_project_config()

    bp_payload = None
    if isinstance(UserBlueprint, type(SimpleBlueprint)):
        bp_payload = UserBlueprint.make_bp_dict()
        if "project_reference" in metadata_payload:
            bp_payload["metadata"]["project_reference"] = metadata_payload[
                "project_reference"
            ]
        else:
            project_name = project_config["name"]
            if project_name == DSL_CONFIG.EMPTY_PROJECT_NAME:
                LOG.error(DSL_CONFIG.EMPTY_PROJECT_MESSAGE)
                sys.exit("Invalid project configuration")

            bp_payload["metadata"]["project_reference"] = Ref.Project(project_name)
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

    decompiled_secrets = decrypt_decompiled_secrets_file(pth=bp_file.rsplit("/", 1)[0])
    if decompiled_secrets:
        LOG.warning(
            "Decompiled secrets metadata found. Use `--passphrase/-ps` cli option to create blueprint with decompiled secrets"
        )

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


def create_blueprint_from_dsl_with_encrypted_secrets(
    client, bp_file, passphrase, name=None, description=None, force_create=False
):
    """
    creates blueprint from the bp python file supplied using import_file API.
    NOTE: Project mentioned remains unchanged
    """

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

    decompiled_secrets = decrypt_decompiled_secrets_file(pth=bp_file.rsplit("/", 1)[0])
    if not decompiled_secrets:
        LOG.warning("Decompiled secrets metadata not found. No need to pass passphrase")

    if name:
        bp_payload["spec"]["name"] = name
        bp_payload["metadata"]["name"] = name

    if description:
        bp_payload["spec"]["description"] = description

    bp_resources = bp_payload["spec"]["resources"]
    project_uuid = bp_payload["metadata"]["project_reference"]["uuid"]
    bp_name = bp_payload["metadata"]["name"]

    return client.blueprint.upload_with_decompiled_secrets(
        bp_payload,
        bp_resources,
        project_uuid,
        bp_name,
        passphrase,
        force_create=force_create,
        decompiled_secrets=decompiled_secrets,
    )


def decompile_bp(
    name, bp_file, with_secrets=False, prefix="", bp_dir=None, passphrase=None
):
    """helper to decompile blueprint"""

    if name and bp_file:
        LOG.error(
            "Please provide either blueprint file location or server blueprint name"
        )
        sys.exit(-1)

    if name:
        if passphrase:
            decompile_bp_from_server_with_secrets(
                name=name,
                with_secrets=with_secrets,
                prefix=prefix,
                bp_dir=bp_dir,
                passphrase=passphrase,
            )
        else:
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
    blueprint = get_blueprint(name)
    bp_uuid = blueprint["metadata"]["uuid"]

    res, err = client.blueprint.export_file(bp_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    _decompile_bp(
        bp_payload=res, with_secrets=with_secrets, prefix=prefix, bp_dir=bp_dir
    )


def decompile_bp_from_server_with_secrets(
    name, with_secrets=False, prefix="", bp_dir=None, passphrase=None
):
    """decompiles the blueprint by fetching it from server"""

    client = get_api_client()
    blueprint = get_blueprint(name)
    bp_uuid = blueprint["metadata"]["uuid"]

    res, err = client.blueprint.export_file(bp_uuid, passphrase)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()

    _decompile_bp(
        bp_payload=res,
        with_secrets=with_secrets,
        prefix=prefix,
        bp_dir=bp_dir,
        contains_encrypted_secrets=True,
    )


def decompile_bp_from_file(filename, with_secrets=False, prefix="", bp_dir=None):
    """decompile blueprint from local blueprint file"""

    # ToDo - Fix this
    bp_payload = json.loads(open(filename).read())
    # bp_payload = read_spec(filename)
    _decompile_bp(
        bp_payload=bp_payload, with_secrets=with_secrets, prefix=prefix, bp_dir=bp_dir
    )


def _decompile_bp(
    bp_payload,
    with_secrets=False,
    prefix="",
    bp_dir=None,
    contains_encrypted_secrets=False,
):
    """decompiles the blueprint from payload"""

    init_decompile_context()

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
        contains_encrypted_secrets=contains_encrypted_secrets,
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


def get_blueprint_uuid(name, all=False, is_brownfield=False):
    """returns blueprint uuid if present else raises error"""

    client = get_api_client()
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
            LOG.error("More than one blueprint found - {}".format(entities))
            sys.exit(-1)

        LOG.info("{} found ".format(name))
        blueprint = entities[0]
    else:
        LOG.error("No blueprint found with name {} found".format(name))
        sys.exit("No blueprint found with name {} found".format(name))

    return blueprint["metadata"]["uuid"]


def get_blueprint(name, all=False, is_brownfield=False):
    """returns blueprint get call data"""

    client = get_api_client()
    bp_uuid = get_blueprint_uuid(name=name, all=all, is_brownfield=is_brownfield)
    res, err = client.blueprint.read(bp_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    return res.json()


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


def parse_launch_runtime_configs(launch_params, config_type):
    """Returns snapshot or restore config_list obj frorm launch_params file"""
    return parse_launch_params_attribute(
        launch_params=launch_params, parse_attribute=config_type + "_config_list"
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


def get_protection_policy_rule(
    protection_policy_uuid,
    protection_rule_uuid,
    snapshot_config_uuid,
    app_profile,
    protection_policies,
    subnet_cluster_map,
    substrate_list,
):
    """returns protection policy, protection rule tuple from cli_prompt"""

    snapshot_config = next(
        (
            config
            for config in app_profile["snapshot_config_list"]
            if config["uuid"] == snapshot_config_uuid
        ),
        None,
    )
    if not snapshot_config:
        LOG.err(
            "No snapshot config with uuid {} found in App Profile {}".format(
                snapshot_config_uuid, app_profile["name"]
            )
        )
        sys.exit("Snapshot config {} not found".format(snapshot_config_uuid))
    is_local_snapshot = (
        snapshot_config["attrs_list"][0]["snapshot_location_type"].lower() == "local"
    )
    config_target = snapshot_config["attrs_list"][0]["target_any_local_reference"]
    target_substrate_reference = next(
        (
            deployment["substrate_local_reference"]
            for deployment in app_profile["deployment_create_list"]
            if deployment["uuid"] == config_target["uuid"]
        ),
        None,
    )
    if not target_substrate_reference:
        LOG.error(
            "No deployment with uuid {} found under app profile {}".format(
                config_target, app_profile["name"]
            )
        )
        sys.exit("Deployment {} not found".format(config_target))
    target_subnet_uuid = next(
        (
            substrate["create_spec"]["resources"]["nic_list"][0]["subnet_reference"][
                "uuid"
            ]
            for substrate in substrate_list
            if substrate["uuid"] == target_substrate_reference["uuid"]
        ),
        None,
    )
    if not target_subnet_uuid:
        LOG.error(
            "No substrate {} with uuid {} found".format(
                target_substrate_reference.get("name", ""),
                target_substrate_reference["uuid"],
            )
        )
        sys.exit("Substrate {} not found".format(target_substrate_reference["uuid"]))

    default_policy = ""
    policy_choices = {}
    for policy in protection_policies:
        if (
            is_local_snapshot and policy["resources"]["rule_type"].lower() != "remote"
        ) or (
            not is_local_snapshot
            and policy["resources"]["rule_type"].lower() != "local"
        ):
            policy_choices[policy["name"]] = policy
        if (not default_policy and policy["resources"]["is_default"]) or (
            protection_policy_uuid == policy["uuid"]
        ):
            default_policy = policy["name"]
    if not policy_choices:
        LOG.error(
            "No protection policy found under this project. Please add one from the UI"
        )
        sys.exit("No protection policy found")
    if not default_policy or default_policy not in policy_choices:
        default_policy = list(policy_choices.keys())[0]
    click.echo("")
    click.echo("Choose from given choices: ")
    for choice in policy_choices.keys():
        click.echo("\t{}".format(highlight_text(repr(choice))))

    selected_policy_name = click.prompt(
        "Protection Policy for '{}' [{}]".format(
            snapshot_config["name"], highlight_text(repr(default_policy))
        ),
        default=default_policy,
        show_default=False,
    )
    if selected_policy_name not in policy_choices:
        LOG.error(
            "Invalid value '{}' for protection policy".format(selected_policy_name)
        )
        sys.exit("Invalid protection policy")
    selected_policy = policy_choices[selected_policy_name]
    ordered_site_list = selected_policy["resources"]["ordered_availability_site_list"]
    cluster_uuid = [
        sc["cluster_uuid"]
        for sc in subnet_cluster_map
        if sc["subnet_uuid"] == target_subnet_uuid
    ]
    if not cluster_uuid:
        LOG.error(
            "Cannot find the cluster associated with the subnet having uuid {}".format(
                target_subnet_uuid
            )
        )
        sys.exit("Cluster not found")
    cluster_uuid = cluster_uuid[0]
    cluster_idx = -1
    for i, site in enumerate(ordered_site_list):
        if (
            site["infra_inclusion_list"]["cluster_references"][0]["uuid"]
            == cluster_uuid
        ):
            cluster_idx = i
            break
    if cluster_idx < 0:
        LOG.error(
            "Unable to find cluster with uuid {} in protection policy {}".format(
                cluster_uuid, selected_policy_name
            )
        )
        sys.exit("Cluster not found")
    both_rules_present = selected_policy["resources"]["rule_type"].lower() == "both"

    def get_target_cluster_name(target_cluster_idx):
        target_cluster_uuid = ordered_site_list[target_cluster_idx][
            "infra_inclusion_list"
        ]["cluster_references"][0]["uuid"]
        target_cluster_name = next(
            (
                sc["cluster_name"]
                for sc in subnet_cluster_map
                if sc["cluster_uuid"] == target_cluster_uuid
            ),
            None,
        )
        if not target_cluster_name:
            LOG.error(
                "Unable to find the cluster with uuid {}".format(target_cluster_uuid)
            )
            sys.exit("Cluster not found")
        return target_cluster_name

    default_rule_idx, i = 1, 1
    rule_choices = {}
    for rule in selected_policy["resources"]["app_protection_rule_list"]:
        source_cluster_idx = rule["first_availability_site_index"]
        if source_cluster_idx == cluster_idx:
            expiry, categories = {}, ""
            if both_rules_present:
                if (
                    is_local_snapshot
                    and source_cluster_idx == rule["second_availability_site_index"]
                ):
                    expiry = rule["local_snapshot_retention_policy"][
                        "snapshot_expiry_policy"
                    ]
                elif (
                    not is_local_snapshot
                    and source_cluster_idx != rule["second_availability_site_index"]
                ):
                    categories = ", ".join(
                        [
                            "{}:{}".format(k, v[0])
                            for k, v in rule["category_filter"]["params"].items()
                        ]
                    )
                    expiry = rule["remote_snapshot_retention_policy"][
                        "snapshot_expiry_policy"
                    ]
            else:
                if is_local_snapshot:
                    expiry = rule["local_snapshot_retention_policy"][
                        "snapshot_expiry_policy"
                    ]
                else:
                    categories = ", ".join(
                        [
                            "{}:{}".format(k, v[0])
                            for k, v in rule["category_filter"]["params"].items()
                        ]
                    )
                    expiry = rule["remote_snapshot_retention_policy"][
                        "snapshot_expiry_policy"
                    ]
            if expiry:
                target_cluster_name = get_target_cluster_name(
                    rule["second_availability_site_index"]
                )
                if rule["uuid"] == protection_rule_uuid:
                    default_rule_idx = i
                label = (
                    "{}. Snapshot expires in {} {}. Target cluster: {}. Categories: {}".format(
                        i,
                        expiry["multiple"],
                        expiry["interval_type"].lower(),
                        target_cluster_name,
                        categories,
                    )
                    if categories
                    else "{}. Snapshot expires in {} {}. Target cluster: {}".format(
                        i,
                        expiry["multiple"],
                        expiry["interval_type"].lower(),
                        target_cluster_name,
                    )
                )
                rule_choices[i] = {"label": label, "rule": rule}
                i += 1

    if not rule_choices:
        LOG.error(
            "No matching protection rules found under protection policy {}. Please add the rules using UI to continue".format(
                selected_policy_name
            )
        )
        sys.exit("No protection rules found")
    click.echo("")
    click.echo("Choose from given choices: ")
    for choice in rule_choices.values():
        click.echo("\t{}".format(highlight_text(repr(choice["label"]))))

    selected_rule = click.prompt(
        "Protection Rule for '{}' [{}]".format(
            snapshot_config["name"], highlight_text(repr(default_rule_idx))
        ),
        default=default_rule_idx,
        show_default=False,
    )
    if selected_rule not in rule_choices:
        LOG.error("Invalid value '{}' for protection rule".format(selected_rule))
        sys.exit("Invalid protection rule")
    return selected_policy, rule_choices[selected_rule]["rule"]


def get_app(app_name):
    """
    This routine checks if app with give name exists or not.
    If exists then returns the app list resp
    args:
        app_name (str): app name
    returns:
        resp (dict): app response if app exists
    """
    client = get_api_client()

    LOG.info("Searching for existing applications with name {}".format(app_name))

    resp, err = client.application.list(params={"filter": "name=={}".format(app_name)})
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    resp = resp.json()
    if resp["metadata"]["total_matches"] > 0:
        LOG.info("Application found with name {}".format(app_name))
        return resp

    LOG.info("No existing application found with name {}".format(app_name))
    return None


def launch_blueprint_simple(
    blueprint_name=None,
    app_name=None,
    blueprint=None,
    profile_name=None,
    patch_editables=True,
    launch_params=None,
    is_brownfield=False,
    brownfield_deployment_file=None,
    skip_app_name_check=False,
):
    client = get_api_client()

    if app_name and not skip_app_name_check:
        res = get_app(app_name)
        if res:
            LOG.debug(res)
            LOG.error("Application Name ({}) is already used.".format(app_name))
            sys.exit(-1)

    if not blueprint:
        blueprint = get_blueprint(blueprint_name, is_brownfield=is_brownfield)

    bp_metadata = blueprint.get("metadata", {})
    bp_status_data = blueprint.get("status", {})

    blueprint_uuid = bp_metadata.get("uuid", "")
    blueprint_name = blueprint_name or blueprint.get("metadata", {}).get("name", "")

    project_ref = bp_metadata.get("project_reference", {})
    project_uuid = project_ref.get("uuid")
    bp_status = bp_status_data["state"]
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
            LOG.error("No profile found with name {}".format(profile_name))
            sys.exit(-1)

    runtime_bf_deployment_list = []
    if brownfield_deployment_file:
        bp_metadata = blueprint.get("metadata", {})
        project_uuid = bp_metadata.get("project_reference", {}).get("uuid", "")

        # Set bp project in dsl context
        ContextObj = get_context()
        project_config = ContextObj.get_project_config()
        project_name = project_config["name"]

        if project_uuid:
            project_data = Cache.get_entity_data_using_uuid(
                entity_type=CACHE.ENTITY.PROJECT, uuid=project_uuid
            )
            bp_project = project_data.get("name")

            if bp_project and bp_project != project_name:
                project_name = bp_project
                ContextObj.update_project_context(project_name=project_name)

        bf_deployments = get_brownfield_deployment_classes(brownfield_deployment_file)

        bp_profile_data = {}
        for _profile in bp_status_data["resources"]["app_profile_list"]:
            if _profile["name"] == profile["app_profile_reference"]["name"]:
                bp_profile_data = _profile

        # Get substrate-account map
        bp_subs_uuid_account_uuid_map = {}
        for _sub in bp_status_data["resources"]["substrate_definition_list"]:
            if _sub.get("type", "") == "EXISTING_VM":
                bp_subs_uuid_account_uuid_map[_sub["uuid"]] = ""
                continue

            account_uuid = _sub["create_spec"]["resources"]["account_uuid"]

            if _sub.get("type", "") == "AHV_VM":
                account_data = Cache.get_entity_data_using_uuid(
                    entity_type=CACHE.ENTITY.ACCOUNT, uuid=account_uuid
                )
                # replace pe account uuid by pc account uuid
                account_uuid = account_data["data"]["pc_account_uuid"]

            bp_subs_uuid_account_uuid_map[_sub["uuid"]] = account_uuid

        # Get dep name-uuid map and dep-account_uuid map
        bp_dep_name_uuid_map = {}
        bp_dep_name_account_uuid_map = {}
        for _dep in bp_profile_data.get("deployment_create_list", []):
            bp_dep_name_uuid_map[_dep["name"]] = _dep["uuid"]

            _dep_sub_uuid = _dep["substrate_local_reference"]["uuid"]
            bp_dep_name_account_uuid_map[_dep["name"]] = bp_subs_uuid_account_uuid_map[
                _dep_sub_uuid
            ]

        # Compile brownfield deployment after attaching valid account to instance
        for _bf_dep in bf_deployments:
            _bf_dep_name = getattr(_bf_dep, "name", "") or _bf_dep.__name__

            # Attaching correct account to brownfield instances
            for _inst in _bf_dep.instances:
                _inst.account_uuid = bp_dep_name_account_uuid_map[_bf_dep_name]

            _bf_dep = _bf_dep.get_dict()

            if _bf_dep_name in list(bp_dep_name_uuid_map.keys()):
                runtime_bf_deployment_list.append(
                    {
                        "uuid": bp_dep_name_uuid_map[_bf_dep_name],
                        "name": _bf_dep_name,
                        "value": {
                            "brownfield_instance_list": _bf_dep.get(
                                "brownfield_instance_list"
                            )
                            or []
                        },
                    }
                )

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
        launch_runtime_snapshot_configs = parse_launch_runtime_configs(
            launch_params, "snapshot"
        )

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

        snapshot_config_list = runtime_editables.get("snapshot_config_list", [])
        restore_config_list = runtime_editables.get("restore_config_list", [])
        restore_config_map = {config["uuid"]: config for config in restore_config_list}

        if snapshot_config_list and restore_config_list:
            click.echo("\n\t\t\t", nl=False)
            click.secho("SNAPSHOT CONFIG LIST DATA", underline=True, bold=True)
            app_profile = next(
                (
                    _profile
                    for _profile in bp_data["status"]["resources"]["app_profile_list"]
                    if _profile["uuid"] == profile["app_profile_reference"]["uuid"]
                ),
                None,
            )
            if not app_profile:
                LOG.error(
                    "App Profile {} with uuid {} not found".format(
                        profile.get("app_profile_reference", {}).get("name", ""),
                        profile.get("app_profile_reference", {}).get("uuid", ""),
                    )
                )
                sys.exit(-1)
            env_uuids = app_profile["environment_reference_list"]
            if not env_uuids:
                LOG.error(
                    "Cannot launch a blueprint with snapshot-restore configs without selecting an environment"
                )
                sys.exit("No environment selected")
            substrate_list = bp_data["status"]["resources"]["substrate_definition_list"]

            for snapshot_config in snapshot_config_list:
                if launch_runtime_snapshot_configs:
                    _config = next(
                        (
                            config
                            for config in launch_runtime_snapshot_configs
                            if config["name"] == snapshot_config["name"]
                        ),
                        None,
                    )
                    if _config:
                        snapshot_config_obj = next(
                            (
                                config
                                for config in app_profile["snapshot_config_list"]
                                if config["uuid"] == snapshot_config["uuid"]
                            ),
                            None,
                        )
                        snapshot_config["value"] = deepcopy(_config["value"])
                        restore_config_id = snapshot_config_obj[
                            "config_reference_list"
                        ][0]["uuid"]
                        restore_config = restore_config_map[restore_config_id]
                        restore_config["value"] = deepcopy(_config["value"])
                        continue

                res, err = client.blueprint.protection_policies(
                    blueprint_uuid,
                    app_profile["uuid"],
                    snapshot_config["uuid"],
                    env_uuids[0],
                )
                if err:
                    LOG.error("[{}] - {}".format(err["code"], err["error"]))
                    sys.exit("Unable to retrieve protection policies")
                protection_policies = [p["status"] for p in res.json()["entities"]]
                payload = {"filter": "uuid=={}".format(env_uuids[0])}
                res, err = client.environment.list(payload)
                if err:
                    LOG.error("[{}] - {}".format(err["code"], err["error"]))
                    sys.exit("Unable to retrieve environments")
                infra_list = next(
                    (
                        env["status"]["resources"]["infra_inclusion_list"]
                        for env in res.json()["entities"]
                        if env["metadata"]["uuid"] == env_uuids[0]
                    ),
                    None,
                )
                if not infra_list:
                    LOG.error("Cannot find accounts associated with the environment")
                    sys.exit("Unable to retrieve accounts")
                ntnx_acc = next(
                    (acc for acc in infra_list if acc["type"] == "nutanix_pc"), None
                )
                if not ntnx_acc:
                    LOG.error(
                        "No nutanix account found associated with the environment"
                    )
                    sys.exit("No nutanix account found in environment")
                ahv_new = AhvNew(client.connection)
                filter_query = "_entity_id_=in={}".format(
                    "|".join(subnet["uuid"] for subnet in ntnx_acc["subnet_references"])
                )
                subnets = ahv_new.subnets(
                    filter_query=filter_query,
                    account_uuid=ntnx_acc["account_reference"]["uuid"],
                )
                subnet_cluster_map = [
                    {
                        "cluster_name": subnet["status"]["cluster_reference"]["name"],
                        "cluster_uuid": subnet["status"]["cluster_reference"]["uuid"],
                        "subnet_name": subnet["status"]["name"],
                        "subnet_uuid": subnet["metadata"]["uuid"],
                    }
                    for subnet in subnets["entities"]
                ]
                protection_policy = snapshot_config["value"]["attrs_list"][0][
                    "app_protection_policy_reference"
                ]
                protection_rule = snapshot_config["value"]["attrs_list"][0][
                    "app_protection_rule_reference"
                ]

                protection_policy, protection_rule = get_protection_policy_rule(
                    protection_policy,
                    protection_rule,
                    snapshot_config["uuid"],
                    app_profile,
                    protection_policies,
                    subnet_cluster_map,
                    substrate_list,
                )

                snapshot_config_obj = next(
                    (
                        config
                        for config in app_profile["snapshot_config_list"]
                        if config["uuid"] == snapshot_config["uuid"]
                    ),
                    None,
                )
                if not snapshot_config_obj:
                    LOG.err(
                        "No snapshot config with uuid {} found in App Profile {}".format(
                            snapshot_config["uuid"], app_profile["name"]
                        )
                    )
                    sys.exit("Invalid snapshot config")
                updated_value = {
                    "attrs_list": [
                        {
                            "app_protection_rule_reference": protection_rule["uuid"],
                            "app_protection_policy_reference": protection_policy[
                                "uuid"
                            ],
                        }
                    ]
                }
                snapshot_config["value"] = updated_value
                restore_config_id = snapshot_config_obj["config_reference_list"][0][
                    "uuid"
                ]
                restore_config = restore_config_map[restore_config_id]
                restore_config["value"] = updated_value

        runtime_editables_json = json.dumps(
            runtime_editables, indent=4, separators=(",", ": ")
        )
        LOG.info("Updated blueprint editables are:\n{}".format(runtime_editables_json))

    if runtime_bf_deployment_list:
        bf_dep_names = [bfd["name"] for bfd in runtime_bf_deployment_list]
        runtime_deployments = launch_payload["spec"]["runtime_editables"].get(
            "deployment_list", []
        )
        for _rd in runtime_deployments:
            if _rd["name"] not in bf_dep_names:
                runtime_bf_deployment_list.append(_rd)

        launch_payload["spec"]["runtime_editables"][
            "deployment_list"
        ] = runtime_bf_deployment_list

        runtime_bf_deployment_list_json = json.dumps(
            runtime_bf_deployment_list, indent=4, separators=(",", ": ")
        )
        LOG.info(
            "Updated blueprint deployment editables are:\n{}".format(
                runtime_bf_deployment_list_json
            )
        )

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
        bp_uuid = get_blueprint_uuid(blueprint_name)
        _, err = client.blueprint.delete(bp_uuid)
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(-1)
        LOG.info("Blueprint {} deleted".format(blueprint_name))


def create_patched_blueprint(
    blueprint, project_data, environment_data, profile_name=None, with_secrets=False
):
    """Patch the blueprint with the given environment to create a new blueprint"""
    client = get_api_client()
    org_bp_name = blueprint["metadata"]["name"]
    org_bp_uuid = blueprint["metadata"]["uuid"]
    project_uuid = project_data["metadata"]["uuid"]
    env_uuid = environment_data["metadata"]["uuid"]

    new_bp_name = "{}-{}".format(org_bp_name, str(uuid.uuid4())[:8])
    request_spec = {
        "api_version": "3.0",
        "metadata": {
            "kind": "blueprint",
            "project_reference": {"kind": "project", "uuid": project_uuid},
        },
        "spec": {
            "environment_profile_pairs": [
                {
                    "environment": {"uuid": env_uuid},
                    "app_profile": {"name": profile_name},
                    "keep_secrets": with_secrets,
                }
            ],
            "new_blueprint": {"name": new_bp_name},
        },
    }

    msg = (
        "Creating Patched blueprint with secrets preserved"
        if with_secrets
        else "Creating Patched blueprint"
    )
    LOG.info(msg)
    bp_res, err = client.blueprint.patch_with_environment(org_bp_uuid, request_spec)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)

    bp_res = bp_res.json()
    bp_status = bp_res["status"]["state"]
    if bp_status != "ACTIVE":
        LOG.error("Blueprint went to {} state".format(bp_status))
        sys.exit(-1)

    return bp_res


def patch_bp_if_required(
    with_secrets=False, environment_name=None, blueprint_name=None, profile_name=None
):
    """Patch the blueprint with the given environment to create a new blueprint if the requested app profile
    is not already linked to the given environment"""
    if environment_name:
        bp = get_blueprint(blueprint_name)
        project_uuid = bp["metadata"]["project_reference"]["uuid"]
        environment_data, project_data = get_project_environment(
            name=environment_name, project_uuid=project_uuid
        )
        env_uuid = environment_data["metadata"]["uuid"]

        app_profiles = bp["spec"]["resources"]["app_profile_list"]
        if profile_name is None:
            profile_name = app_profiles[0]["name"]

        found_profile = None
        for app_profile in app_profiles:
            if app_profile["name"] == profile_name:
                found_profile = app_profile
                break

        if not found_profile:
            raise Exception("No profile found with name {}".format(profile_name))

        ref_env_uuid = next(
            iter(app_profile.get("environment_reference_list", [])), None
        )
        if ref_env_uuid != env_uuid:
            new_blueprint = create_patched_blueprint(
                bp, project_data, environment_data, profile_name, with_secrets
            )
            return new_blueprint["metadata"]["name"], new_blueprint

    return blueprint_name, None
