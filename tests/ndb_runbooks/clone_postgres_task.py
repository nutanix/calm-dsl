"""
Calm Runbook Sample for ndb postgres clone
"""
import json

from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.builtins.models.ndb import (
    DatabaseServer,
    Database,
    PostgresDatabaseOutputVariables,
    TimeMachine,
    Tag,
)
from calm.dsl.runbooks import runbook, RunbookTask as Task
from calm.dsl.builtins.models.utils import read_local_file
from calm.dsl.constants import STRATOS

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
ACCOUNTS = DSL_CONFIG["ACCOUNTS"]


def database_server_params():
    """Get the Database server config for postgres clone action"""
    return DatabaseServer.Postgres.Clone(
        name="new_db_@@{calm_time}@@",
        password="abc123",
        cluster="@@{cluster_uuid}@@",
        compute_profile=Ref.NutanixDB.Profile.Compute(name="DEFAULT_OOB_COMPUTE"),
        network_profile=Ref.NutanixDB.Profile.Network(
            name="DEFAULT_OOB_POSTGRESQL_NETWORK"
        ),
        ssh_public_key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC5GGnkZH75LzRFxOh4LcM0owSLn+1nvxP8tcw2PeXmdi82N1Fe8RZ3m5SkJqxJO2BvC39McyovNFIXC2LN2HeXuvovB6C0v1PGNb7oq2I5QrnRRUp1Tm4OJQN9cNZZ8MYaAcd0LokodrXgwpUQ4zlDdmlza1sDGQxXg4Dxvh5N/Y+rMjYdFbRSYmzzqI5aSHty8Shg9rbrqebFhTVCvzyQJzE/0PS3WUnCAbhLovLI/sdnTyM0CAm+Y6ui+1EFQkyg2VkbjJ6Y2foFRPJufqrnQS6S/njUeD5US3W4r8nMOxRZutRlFoado/yR+9MOkGn57NhIkMhji8wTH6SVtq2m09P+3/1Z9P+rASIS0rmH80XwwUVhfSyJ/J5dN0Axu8Bfqa9T40VDRRsoVKs79BRFr/5XRayS/O6jfGw6biYKJLeU9vV7OxtjzIuMDlbnsshuCcGtNMfI9W73F9VlKfKdQx2n547KEx79DlEJg4mtoaxkguvDo/aTH+0IJTF2BMh2iqL23ie6BkRVjHfhwWFM2WDRdHhDLcuAYSPP/sTuOEZgkElzK+ODahAXoglgTkqJeq2MiJ3tAmi39k9EKuTDR2xn1BLo/B4dMq1jkQJwVfEP+jD4eRTrlhZ8ZycIZgeY4c5MGqUNW9WfFuKOHogWEWMbuM3C8LLUFB4T1H5yDQ== mitesh.madaan@nutanix.com",
        description="Sample description of db server",
    )


def instance_params():
    """Get the postgres instance config for postgres create action runbook update"""
    return Database.Postgres.Clone(
        name="post_inst_@@{calm_time}@@",
        database_parameter_profile=Ref.NutanixDB.Profile.Database_Parameter(
            name="DEFAULT_POSTGRES_PARAMS"
        ),
        password="Nutanix.123",
        pre_clone_cmd="",
        post_clone_cmd="",
    )


def timemachine_params():
    """Get the Time Machine config for postgres create action"""
    return TimeMachine.Postgres.Clone(
        time_machine_name="@@{timemachine_uuid}@@",
        snapshot_with_timeStamp="@@{snapshot_uuid}@@",
        time_zone="UTC",
    )


def tag_params():
    """Get the Tag config for postgres clone action"""
    return Tag.Clone()


def output_variables():
    """Get the defined output variable mapping for postgres create action"""
    return PostgresDatabaseOutputVariables.Clone()


@runbook
def nutanixdb_postgres_clone():
    """NDB Postgres Clone Action Runbook"""
    Task.NutanixDB.PostgresDatabase.Clone(
        name="postgres_clone_task_name",
        account=Ref.Account(
            ACCOUNTS.get(STRATOS.PROVIDER.NDB, [{"NAME": ""}])[0]["NAME"]
        ),
        database_server_config=database_server_params(),
        instance_config=instance_params(),
        tag_config=tag_params(),
        timemachine_config=timemachine_params(),
    )
