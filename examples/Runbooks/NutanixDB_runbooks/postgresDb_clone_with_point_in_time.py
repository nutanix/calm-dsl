from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.builtins.models.ndb import (
    DatabaseServer,
    Database,
    PostgresDatabaseOutputVariables,
    TimeMachine,
    Tag,
)
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task

CloneTag = Ref.NutanixDB.Tag.Clone


def database_server_params():
    """Get the Database server config for postgres clone action"""
    return DatabaseServer.Postgres.Clone(
        name="new_db_@@{calm_time}@@",
        password="abc123",
        cluster=Ref.NutanixDB.Cluster(name="EraCluster"),
        compute_profile=Ref.NutanixDB.Profile.Compute(name="DEFAULT_OOB_COMPUTE"),
        network_profile=Ref.NutanixDB.Profile.Network(
            name="DEFAULT_OOB_POSTGRESQL_NETWORK"
        ),
        ssh_public_key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC5GGnkZH75LzRFxOh4LcM0owSLn+1nvxP8tcw2PeXmdi82N1Fe8RZ3m5SkJqxJO2BvC39McyovNFIXC2LN2HeXuvovB6C0v1PGNb7oq2I5QrnRRUp1Tm4OJQN9cNZZ8MYaAcd0LokodrXgwpUQ4zlDdmlza1sDGQxXg4Dxvh5N/Y+rMjYdFbRSYmzzqI5aSHty8Shg9rbrqebFhTVCvzyQJzE/0PS3WUnCAbhLovLI/sdnTyM0CAm+Y6ui+1EFQkyg2VkbjJ6Y2foFRPJufqrnQS6S/njUeD5US3W4r8nMOxRZutRlFoado/yR+9MOkGn57NhIkMhji8wTH6SVtq2m09P+3/1Z9P+rASIS0rmH80XwwUVhfSyJ/J5dN0Axu8Bfqa9T40VDRRsoVKs79BRFr/5XRayS/O6jfGw6biYKJLeU9vV7OxtjzIuMDlbnsshuCcGtNMfI9W73F9VlKfKdQx2n547KEx79DlEJg4mtoaxkguvDo/aTH+0IJTF2BMh2iqL23ie6BkRVjHfhwWFM2WDRdHhDLcuAYSPP/sTuOEZgkElzK+ODahAXoglgTkqJeq2MiJ3tAmi39k9EKuTDR2xn1BLo/B4dMq1jkQJwVfEP+jD4eRTrlhZ8ZycIZgeY4c5MGqUNW9WfFuKOHogWEWMbuM3C8LLUFB4T1H5yDQ== mitesh.madaan@nutanix.com",
        description="Sample description of db server",
    )


def instance_params():
    """Get the postgres instance config for postgres clone action runbook update"""
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
    """Get the Time Machine config for postgres clone action"""
    return TimeMachine.Postgres.Clone(
        time_machine_name=Ref.NutanixDB.TimeMachine("dnd-tm2"),
        point_in_time="2023-02-12 10:01:40",
    )


def tag_params():
    """Get the Tag config for postgres clone action"""
    return Tag.Clone(tags=[CloneTag("tag name", "")])


def output_variables():
    """Get the defined output variable mapping for postgres clone action"""
    return PostgresDatabaseOutputVariables.Clone()


@runbook
def nutanixdb_postgres_clone():
    """NDB Postgres Clone Action Runbook"""
    Task.NutanixDB.PostgresDatabase.Clone(
        name="postgres_clone_task_name",
        account=Ref.Account("era"),
        database_server_config=database_server_params(),
        instance_config=instance_params(),
        timemachine_config=timemachine_params(),
        tag_config=tag_params(),
        outargs=output_variables(),
    )
