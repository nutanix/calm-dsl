import sys
import json

from calm.dsl.db.table_config import ResourceTypeCache
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
from calm.dsl.constants import CACHE
from calm.dsl.store import Cache

from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)
KEY_SEPERATOR = "_"

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


def set_ndb_calm_reference(inarg_var_name, inarg_var_value):
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
        return {"value": inarg_var_value, "type": "Non_Ref"}


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
        if len(inarg["name"]) > len(rt_task) + 2:
            modified_var_name = inarg["name"][len(rt_task) + 2 :]

        if (
            modified_var_name in database_server_reverse_field_map
            and not database_server_reverse_field_map[modified_var_name].endswith(
                HIDDEN_SUFFIX
            )
        ):
            database_server_attrs[
                database_server_reverse_field_map[modified_var_name]
            ] = set_ndb_calm_reference(
                database_server_reverse_field_map[modified_var_name], inarg["value"]
            )
        elif (
            modified_var_name in database_reverse_field_map
            and not database_reverse_field_map[modified_var_name].endswith(
                HIDDEN_SUFFIX
            )
        ):
            database_attrs[
                database_reverse_field_map[modified_var_name]
            ] = set_ndb_calm_reference(
                database_reverse_field_map[modified_var_name], inarg["value"]
            )
        elif (
            modified_var_name in time_machine_reverse_field_map
            and not time_machine_reverse_field_map[modified_var_name].endswith(
                HIDDEN_SUFFIX
            )
        ):
            time_machine_attrs[
                time_machine_reverse_field_map[modified_var_name]
            ] = set_ndb_calm_reference(
                time_machine_reverse_field_map[modified_var_name], inarg["value"]
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


def get_schema_file_and_user_attrs(task_name, attrs, account_name):
    resource_type_name = attrs.get("resource_type_reference", {}).get("name", "")
    action_name = attrs.get("action_reference", {}).get("name", "")
    resource_type_cached_data = ResourceTypeCache.get_entity_data(
        name=resource_type_name, provider_name="NDB"
    )
    if not resource_type_cached_data:
        LOG.error("resource_type not found in NDB provider")
        sys.exit(
            "resource_type {} not found in NDB provider".format(resource_type_name)
        )

    for action in resource_type_cached_data["action_list"]:
        if action_name == action["name"]:
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

    LOG.error(
        "No action  {} found in resource type {}".format(
            action_name, resource_type_cached_data["name"]
        )
    )
    sys.exit(
        "No action {} found in resource type {}".format(
            action_name, resource_type_cached_data["name"]
        )
    )
