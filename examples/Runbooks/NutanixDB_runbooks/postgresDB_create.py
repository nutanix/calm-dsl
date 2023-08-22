from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.builtins.models.ndb import (
    DatabaseServer,
    Database,
    TimeMachine,
    PostgresDatabaseOutputVariables,
    Tag,
)
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task

DatabaseTag = Ref.NutanixDB.Tag.Database
TimemachineTag = Ref.NutanixDB.Tag.TimeMachine


def database_server_params():
    """Get the Database server config for postgres create action"""
    return DatabaseServer.Postgres.Create(
        name="new_db_@@{calm_time}@@",
        password="abc123",
        cluster=Ref.NutanixDB.Cluster(name="EraCluster"),
        software_profile=Ref.NutanixDB.Profile.Software(name="POSTGRES_10.4_OOB"),
        software_profile_version=Ref.NutanixDB.Profile.Software_Version(
            name="POSTGRES_10.4_OOB (1.0)"
        ),
        compute_profile=Ref.NutanixDB.Profile.Compute(name="DEFAULT_OOB_COMPUTE"),
        network_profile=Ref.NutanixDB.Profile.Network(
            name="DEFAULT_OOB_POSTGRESQL_NETWORK"
        ),
        # ip_address="10.44.76.141", # is added when network profile supports it.
        ssh_public_key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC5GGnkZH75LzRFxOh4LcM0owSLn+1nvxP8tcw2PeXmdi82N1Fe8RZ3m5SkJqxJO2BvC39McyovNFIXC2LN2HeXuvovB6C0v1PGNb7oq2I5QrnRRUp1Tm4OJQN9cNZZ8MYaAcd0LokodrXgwpUQ4zlDdmlza1sDGQxXg4Dxvh5N/Y+rMjYdFbRSYmzzqI5aSHty8Shg9rbrqebFhTVCvzyQJzE/0PS3WUnCAbhLovLI/sdnTyM0CAm+Y6ui+1EFQkyg2VkbjJ6Y2foFRPJufqrnQS6S/njUeD5US3W4r8nMOxRZutRlFoado/yR+9MOkGn57NhIkMhji8wTH6SVtq2m09P+3/1Z9P+rASIS0rmH80XwwUVhfSyJ/J5dN0Axu8Bfqa9T40VDRRsoVKs79BRFr/5XRayS/O6jfGw6biYKJLeU9vV7OxtjzIuMDlbnsshuCcGtNMfI9W73F9VlKfKdQx2n547KEx79DlEJg4mtoaxkguvDo/aTH+0IJTF2BMh2iqL23ie6BkRVjHfhwWFM2WDRdHhDLcuAYSPP/sTuOEZgkElzK+ODahAXoglgTkqJeq2MiJ3tAmi39k9EKuTDR2xn1BLo/B4dMq1jkQJwVfEP+jD4eRTrlhZ8ZycIZgeY4c5MGqUNW9WfFuKOHogWEWMbuM3C8LLUFB4T1H5yDQ== mitesh.madaan@nutanix.com",
        description="Sample description of db server",
    )


def postgresinstance_params():
    """Get the postgres instance config for postgres create action runbook update"""
    return Database.Postgres.Create(
        name="post_inst_@@{calm_time}@@",
        description="Sample description of postgres instances",
        database_parameter_profile=Ref.NutanixDB.Profile.Database_Parameter(
            name="DEFAULT_POSTGRES_PARAMS"
        ),
        initial_database_name="TEST_DB_01",
        initial_database_password="DB_PASS",
        listener_port="5432",
        size="200",
        pre_create_script="",
        post_create_script="",
    )


def timemachine_params():
    """Get the Time Machine config for postgres create action"""
    return TimeMachine.Postgres.Create(
        name="inst_@@{calm_time}@@_TM",
        description="This is time machine's description",
        sla=Ref.NutanixDB.SLA(name="DEFAULT_OOB_GOLD_SLA"),
        snapshottimeofday__hours=12,
        snapshottimeofday__minutes=0,
        snapshottimeofday__seconds=0,
        snapshots_perday=1,
        logbackup_interval=60,
        weeklyschedule__dayofweek="WEDNESDAY",
        monthlyschedule__dayofmonth=17,
        quartelyschedule__startmonth="FEBRUARY",
    )


def tag_params():
    """Get the Tag config for postgres create action"""
    return Tag.Create(
        database_tags=[
            DatabaseTag("testing 23545", "12345 value"),
            DatabaseTag("testing", "testing value"),
        ],
        time_machine_tags=[
            TimemachineTag("testing timemachine", ""),
            TimemachineTag("testing", "testing TM value"),
        ],
    )


def output_variables():
    """Get the defined output variable mapping for postgres create action"""
    return PostgresDatabaseOutputVariables.Create(
        database_name="postgres_database_name",
        database_instance_id="",
        tags="",
        properties="",
        time_machine="postgres_time_machine",
        time_machine_id="",
        metric="",
        type="",
        platform_data="",
    )


@runbook
def nutanixdb_postgres_create():
    """NDB Postgres Create Action Runbook"""
    Task.NutanixDB.PostgresDatabase.Create(
        name="postgres_create_task_name",
        account=Ref.Account("era"),
        database_server_config=database_server_params(),
        instance_config=postgresinstance_params(),
        timemachine_config=timemachine_params(),
        tag_config=tag_params(),
        outargs=output_variables(),
    )
