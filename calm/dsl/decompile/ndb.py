import sys
import json
import os

from calm.dsl.db.table_config import ResourceTypeCache, AccountCache
from calm.dsl.builtins.models.ndb import (
    DatabaseServer,
    Database,
    TimeMachine,
    PostgresDatabaseOutputVariables,
    Tag,
)
from calm.dsl.builtins.models.constants import (
    NutanixDB as NutanixDBConst,
    HIDDEN_SUFFIX,
)
from calm.dsl.builtins.models.helper import common as common_helper
from calm.dsl.builtins.models.variable import VariableType
from calm.dsl.constants import CACHE
from calm.dsl.store import Cache
from calm.dsl.tools import get_escaped_quotes_string
from calm.dsl.decompile.file_handler import get_local_dir
from calm.dsl.decompile.decompile_helpers import modify_var_format

from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)
KEY_SEPERATOR = "_"
NDB_FILES = []

entities_map = {
    NutanixDBConst.Attrs.DATABASE: {
        "cache": CACHE.NDB_ENTITY.DATABASE,
        "ref": "Ref.NutanixDB.Database",
    },
    NutanixDBConst.Attrs.SLA: {
        "cache": CACHE.NDB_ENTITY.SLA,
        "ref": "Ref.NutanixDB.SLA",
    },
    NutanixDBConst.Attrs.CLUSTER: {
        "cache": CACHE.NDB_ENTITY.CLUSTER,
        "ref": "Ref.NutanixDB.Cluster",
    },
    NutanixDBConst.Attrs.SNAPSHOT_WITH_TIMESTAMP: {
        "cache": CACHE.NDB_ENTITY.SNAPSHOT,
        "ref": "Ref.NutanixDB.Snapshot",
    },
    NutanixDBConst.Attrs.TIME_MACHINE: {
        "cache": CACHE.NDB_ENTITY.TIME_MACHINE,
        "ref": "Ref.NutanixDB.TimeMachine",
    },
    # Profiles
    NutanixDBConst.Attrs.Profile.COMPUTE_PROFILE: {
        "cache": CACHE.NDB_ENTITY.PROFILE,
        "ref": "Ref.NutanixDB.Profile.Compute",
    },
    NutanixDBConst.Attrs.Profile.NETWORK_PROFILE: {
        "cache": CACHE.NDB_ENTITY.PROFILE,
        "ref": "Ref.NutanixDB.Profile.Network",
    },
    NutanixDBConst.Attrs.Profile.DATABASE_PARAMETER_PROFILE: {
        "cache": CACHE.NDB_ENTITY.PROFILE,
        "ref": "Ref.NutanixDB.Profile.Database_Parameter",
    },
    NutanixDBConst.Attrs.Profile.SOFTWARE_PROFILE: {
        "cache": CACHE.NDB_ENTITY.PROFILE,
        "ref": "Ref.NutanixDB.Profile.Software",
    },
    NutanixDBConst.Attrs.Profile.SOFTWARE_PROFILE_VERSION: {
        "cache": CACHE.NDB_ENTITY.PROFILE,
        "ref": "Ref.NutanixDB.Profile.Software_Version",
    },
}

# Tag options
tags_map = {
    NutanixDBConst.Attrs.TAGS
    + KEY_SEPERATOR
    + NutanixDBConst.Attrs.Tag.DATABASE: "Ref.NutanixDB.Tag.Database",
    NutanixDBConst.Attrs.TAGS
    + KEY_SEPERATOR
    + NutanixDBConst.Attrs.Tag.DATABASE_SERVER: "Ref.NutanixDB.Tag.DatabaseServer",
    NutanixDBConst.Attrs.TAGS
    + KEY_SEPERATOR
    + NutanixDBConst.Attrs.Tag.TIME_MACHINE: "Ref.NutanixDB.Tag.TimeMachine",
    NutanixDBConst.Attrs.TAGS
    + KEY_SEPERATOR
    + NutanixDBConst.Attrs.Tag.CLONE: "Ref.NutanixDB.Tag.Clone",
}


def set_ndb_calm_reference(inarg_var_name, inarg_var_value, secret_file_name=""):

    # Adding backslash if quotes present in string
    inarg_var_value = get_escaped_quotes_string(inarg_var_value)
    if not common_helper.is_not_macro(inarg_var_value):
        return {"value": inarg_var_value, "type": "Non_Ref"}

    if inarg_var_name in entities_map:
        entity_map = entities_map[inarg_var_name]
        obj = Cache.get_entity_data_using_uuid(
            CACHE.NDB + CACHE.KEY_SEPARATOR + entity_map["cache"], inarg_var_value
        )
        if inarg_var_name == NutanixDBConst.Attrs.SNAPSHOT_WITH_TIMESTAMP:
            return {
                "value": obj.get("name", "")
                + " ("
                + obj.get("snapshot_timestamp", "")
                + ")",
                "type": "Ref",
                "ref": entity_map["ref"],
            }
        return {"value": obj.get("name", ""), "type": "Ref", "ref": entity_map["ref"]}
    if inarg_var_name in tags_map:
        try:
            tags = json.loads(inarg_var_value)
            tag_values = []
            for tag in tags:
                tag_cache_data = Cache.get_entity_data_using_uuid(
                    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.TAG,
                    tag.get("tag_id", ""),
                )
                tag_values.append(
                    {
                        "name": tag_cache_data.get("name", ""),
                        "value": tag.get("value", ""),
                    }
                )

            return {
                "value": tag_values,
                "type": "Tag_Ref",
                "ref": tags_map[inarg_var_name],
            }
        except Exception as exc:
            LOG.error(
                "tag load failed for the value: {} with error {}".format(tags, exc)
            )
            return {"value": [], "type": "Non_Ref"}
    else:
        _type = "Non_Ref"
        if secret_file_name:
            create_file_from_file_name(secret_file_name)
            inarg_var_value = secret_file_name
            _type = "Non_Ref_Secret"
        return {"value": inarg_var_value, "type": _type}


def create_ndb_task_user_attrs(
    task_name,
    account_name,
    rt_task,
    inarg_list,
    output_variable,
    database_server_map=None,
    database_map=None,
    time_machine_map=None,
    tag_map=None,
    output_variable_map=None,
):

    output_var_attrs = {}
    database_server_attrs = {}
    database_attrs = {}
    time_machine_attrs = {}
    tag_attrs = {}

    database_server_reverse_field_map = (
        {v: k for k, v in database_server_map.items()} if database_server_map else {}
    )
    database_reverse_field_map = (
        {v: k for k, v in database_map.items()} if database_map else {}
    )
    time_machine_reverse_field_map = (
        {v: k for k, v in time_machine_map.items()} if time_machine_map else {}
    )
    tag_reverse_field_map = {v: k for k, v in tag_map.items()} if tag_map else {}
    output_vars_reverse_field_map = (
        {v: k for k, v in output_variable_map.items()} if output_variable_map else {}
    )

    for inarg in inarg_list:
        modified_var_name = ""
        secret_file_name = ""
        modified_task_name = task_name.lower().replace(" ", "_")
        if len(inarg["name"]) > len(rt_task) + 2:
            modified_var_name = inarg["name"][len(rt_task) + 2 :]

        if (
            modified_var_name in database_server_reverse_field_map
            and not database_server_reverse_field_map[modified_var_name].endswith(
                HIDDEN_SUFFIX
            )
        ):
            if inarg.get("type", "") == "SECRET":
                secret_file_name = "{}_{}_{}_{}".format(
                    NutanixDBConst.NDB,
                    modified_task_name,
                    DatabaseServer.name,
                    database_server_reverse_field_map[modified_var_name],
                )
            database_server_attrs[
                database_server_reverse_field_map[modified_var_name]
            ] = set_ndb_calm_reference(
                database_server_reverse_field_map[modified_var_name],
                inarg["value"],
                secret_file_name,
            )
        elif (
            modified_var_name in database_reverse_field_map
            and not database_reverse_field_map[modified_var_name].endswith(
                HIDDEN_SUFFIX
            )
        ):
            if inarg.get("type", "") == "SECRET":
                secret_file_name = "{}_{}_{}_{}".format(
                    NutanixDBConst.NDB,
                    modified_task_name,
                    Database.name,
                    database_reverse_field_map[modified_var_name],
                )
            database_attrs[
                database_reverse_field_map[modified_var_name]
            ] = set_ndb_calm_reference(
                database_reverse_field_map[modified_var_name],
                inarg["value"],
                secret_file_name,
            )
        elif (
            modified_var_name in time_machine_reverse_field_map
            and not time_machine_reverse_field_map[modified_var_name].endswith(
                HIDDEN_SUFFIX
            )
        ):
            if inarg.get("type", "") == "SECRET":
                secret_file_name = "{}_{}_{}_{}".format(
                    NutanixDBConst.NDB,
                    modified_task_name,
                    TimeMachine.name,
                    time_machine_reverse_field_map[modified_var_name],
                )
            time_machine_attrs[
                time_machine_reverse_field_map[modified_var_name]
            ] = set_ndb_calm_reference(
                time_machine_reverse_field_map[modified_var_name],
                inarg["value"],
                secret_file_name,
            )
        elif modified_var_name in tag_reverse_field_map and not tag_reverse_field_map[
            modified_var_name
        ].endswith(HIDDEN_SUFFIX):
            tag_attrs[
                tag_reverse_field_map[modified_var_name]
            ] = set_ndb_calm_reference(
                NutanixDBConst.Attrs.TAGS
                + KEY_SEPERATOR
                + tag_reverse_field_map[modified_var_name],
                inarg["value"],
            )
    if time_machine_attrs.get(NutanixDBConst.Attrs.SNAPSHOT_WITH_TIMESTAMP, None):
        time_machine_attrs[NutanixDBConst.Attrs.TIME_ZONE] = {
            "value": "UTC",
            "type": "Non_Ref",
        }

    if database_attrs.get(NutanixDBConst.Attrs.SNAPSHOT_WITH_TIMESTAMP, None):
        database_attrs[NutanixDBConst.Attrs.TIME_ZONE] = {
            "value": "UTC",
            "type": "Non_Ref",
        }

    if database_server_attrs.get(NutanixDBConst.Attrs.SNAPSHOT_WITH_TIMESTAMP, None):
        database_server_attrs[NutanixDBConst.Attrs.TIME_ZONE] = {
            "value": "UTC",
            "type": "Non_Ref",
        }

    for value, output_var in output_variable.items():
        if output_var in output_vars_reverse_field_map:
            output_var_attrs[output_vars_reverse_field_map[output_var]] = value

    return {
        "name": task_name,
        "account": account_name,
        "output_vars": output_var_attrs,
        "database_server": database_server_attrs,
        "database": database_attrs,
        "time_machine": time_machine_attrs,
        "tag": tag_attrs,
    }


def get_schema_file_and_user_attrs_for_postgres_create(
    task_name, account_name, rt_task, inarg_list, output_vars
):
    user_attrs = create_ndb_task_user_attrs(
        task_name,
        account_name,
        rt_task,
        inarg_list,
        output_vars,
        DatabaseServer.Postgres.Create.FIELD_MAP,
        Database.Postgres.Create.FIELD_MAP,
        TimeMachine.Postgres.Create.FIELD_MAP,
        Tag.Create.FIELD_MAP,
        PostgresDatabaseOutputVariables.Create.FIELD_MAP,
    )

    return "ndb_postgres_create.py.jinja2", user_attrs


def get_schema_file_and_user_attrs_for_postgres_clone(
    task_name, account_name, rt_task, inarg_list, output_vars
):
    user_attrs = create_ndb_task_user_attrs(
        task_name,
        account_name,
        rt_task,
        inarg_list,
        output_vars,
        DatabaseServer.Postgres.Clone.FIELD_MAP,
        Database.Postgres.Clone.FIELD_MAP,
        TimeMachine.Postgres.Clone.FIELD_MAP,
        Tag.Clone.FIELD_MAP,
        PostgresDatabaseOutputVariables.Clone.FIELD_MAP,
    )

    return "ndb_postgres_clone.py.jinja2", user_attrs


def get_schema_file_and_user_attrs_for_postgres_delete(
    task_name, account_name, rt_task, inarg_list, output_vars
):
    user_attrs = create_ndb_task_user_attrs(
        task_name,
        account_name,
        rt_task,
        inarg_list,
        output_vars,
        None,
        Database.Postgres.Delete.FIELD_MAP,
    )

    return "ndb_postgres_delete.py.jinja2", user_attrs


def get_schema_file_and_user_attrs_for_postgres_restore(
    task_name, account_name, rt_task, inarg_list, output_vars
):
    user_attrs = create_ndb_task_user_attrs(
        task_name,
        account_name,
        rt_task,
        inarg_list,
        output_vars,
        None,
        Database.Postgres.RestoreFromTimeMachine.FIELD_MAP,
        None,
        None,
        PostgresDatabaseOutputVariables.RestoreFromTimeMachine.FIELD_MAP,
    )

    return "ndb_postgres_restore.py.jinja2", user_attrs


def get_schema_file_and_user_attrs_for_postgres_create_snapshot(
    task_name, account_name, rt_task, inarg_list, output_vars
):
    user_attrs = create_ndb_task_user_attrs(
        task_name,
        account_name,
        rt_task,
        inarg_list,
        output_vars,
        None,
        Database.Postgres.CreateSnapshot.FIELD_MAP,
        None,
        None,
        PostgresDatabaseOutputVariables.CreateSnapshot.FIELD_MAP,
    )

    return "ndb_postgres_create_snapshot.py.jinja2", user_attrs


rt_action_class_map = {
    (
        NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
        NutanixDBConst.ACTION_TYPE.CREATE,
    ): get_schema_file_and_user_attrs_for_postgres_create,
    (
        NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
        NutanixDBConst.ACTION_TYPE.CLONE,
    ): get_schema_file_and_user_attrs_for_postgres_clone,
    (
        NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
        NutanixDBConst.ACTION_TYPE.DELETE,
    ): get_schema_file_and_user_attrs_for_postgres_delete,
    (
        NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
        NutanixDBConst.ACTION_TYPE.RESTORE_FROM_TIME_MACHINE,
    ): get_schema_file_and_user_attrs_for_postgres_restore,
    (
        NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
        NutanixDBConst.ACTION_TYPE.CREATE_SNAPSHOT,
    ): get_schema_file_and_user_attrs_for_postgres_create_snapshot,
}


def get_schema_file_and_user_attrs_for_rtop_task(
    task_name,
    resource_type_name,
    account_name,
    action_name,
    provider_name,
    inarg_list,
    output_variable_map,
    credentials_list=[],
    rendered_credential_list=[],
):
    input_variables = []
    from .variable import render_variable_template

    for variable in inarg_list:
        var_cls = VariableType.decompile(variable)
        var_template = render_variable_template(
            var_cls,
            "Task_" + task_name,
            credentials_list=credentials_list,
            rendered_credential_list=rendered_credential_list,
            ignore_cred_dereference_error=True,  # CALM-47256
        )
        input_variables.append(modify_var_format(var_template))

    user_attrs = {
        "name": task_name,
        "resource_type_name": resource_type_name,
        "account_name": account_name,
        "action_name": action_name,
        "provider_name": provider_name,
        "inarg_list": input_variables,
        "output_variables": output_variable_map,
    }
    return "task_resource_type_action.py.jinja2", user_attrs


def get_schema_file_and_user_attrs(
    task_name, attrs, credentials_list=[], rendered_credential_list=[]
):
    account_ref_dict = attrs.get("account_reference", {})
    account_uuid = account_ref_dict.get("uuid", "")
    account_name = account_ref_dict.get("name", "")
    account_data = AccountCache.get_entity_data_using_uuid(account_uuid)

    # NOTE: Commenting out the following condition as of today,
    # decompile for runbooks not in "ACTIVE" state is also supported
    # if not account_data:
    #     msg = "Account with name: '{}', uuid: '{}' not found".format(
    #         account_name, account_uuid
    #     )
    #     LOG.error(msg)
    #     sys.exit(msg)

    rt_ref_dict = attrs.get("resource_type_reference", {})
    resource_type_uuid = rt_ref_dict.get("uuid", "")
    resource_type_name = rt_ref_dict.get("name", "")
    resource_type_cached_data = ResourceTypeCache.get_entity_data_using_uuid(
        resource_type_uuid
    )

    # NOTE: Commenting out the following condition as of today,
    # decompile for runbooks not in "ACTIVE" state is also supported
    # if not resource_type_cached_data:
    #     msg = "Resource Type with name: '{}', uuid: '{}' not found for account '{}'".format(
    #         resource_type_name, resource_type_uuid, account_data['name']
    #     )
    #     LOG.error(msg)
    #     sys.exit(msg)

    provider_name = account_data.get("provider_type", "")
    action_name = attrs.get("action_reference", {}).get("name", "")
    for action in resource_type_cached_data.get("action_list", []):
        if action_name == action["name"]:
            if provider_name == "NDB":
                rt_task = action["runbook"]["task_definition_list"][1]["name"]
                modified_rt_task = "-".join(rt_task.lower().split())
                if (
                    resource_type_cached_data["name"],
                    action["name"],
                ) not in rt_action_class_map.keys():
                    LOG.error(
                        "decompile for resource type {} and action {} not in rt_action_class_map".format(
                            resource_type_cached_data["name"], action["name"]
                        )
                    )
                    sys.exit("Decompile failed for RT_Operation task")
                return rt_action_class_map[
                    (resource_type_cached_data["name"], action["name"])
                ](
                    task_name=task_name,
                    account_name=account_name,
                    rt_task=modified_rt_task,
                    inarg_list=attrs["inarg_list"],
                    output_vars=attrs["output_variables"],
                )
            else:
                return get_schema_file_and_user_attrs_for_rtop_task(
                    task_name,
                    resource_type_name,
                    account_name,
                    action_name,
                    provider_name,
                    attrs.get("inarg_list", []),
                    attrs.get("output_variables", None),
                    credentials_list=credentials_list,
                    rendered_credential_list=rendered_credential_list,
                )

    msg = "Action '{}' not found on resource type '{}'".format(
        action_name, resource_type_name
    )
    LOG.error(msg)
    sys.exit(msg)


def create_file_from_file_name(file_name):
    """create a file on local directory and add to global file stack for given file name"""
    file_loc = os.path.join(get_local_dir(), file_name)

    # Storing empty value in the file
    with open(file_loc, "w+") as fd:
        fd.write("")

    NDB_FILES.append(file_name)


def get_NDB_files():
    """Returns the NDB files created for NDB secrets value"""

    global NDB_FILES
    return NDB_FILES


def init_NDB_globals():
    """Reinitialises global vars used for NDB secrets value"""

    global NDB_FILES
    NDB_FILES = []
