from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.builtins.models.ndb import (
    Database,
    PostgresDatabaseOutputVariables,
)
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task


def postgresinstance_params():
    """Get the postgres instance config for postgres Restore From Time Machine action"""
    return Database.Postgres.RestoreFromTimeMachine(
        database=Ref.NutanixDB.Database("test-pg-inst"),
        point_in_time="2023-02-12 10:01:40",
    )


def output_variables():
    """Get the defined output variable mapping for postgres Restore From Time Machine action"""
    return PostgresDatabaseOutputVariables.RestoreFromTimeMachine(
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
def nutanixdb_postgres_restore_with_point_in_time():
    """NDB Postgres Restore From Time Machine Action Runbook"""
    Task.NutanixDB.PostgresDatabase.RestoreFromTimeMachine(
        name="postgres_restore_task_name",
        account=Ref.Account("ndb-account"),
        instance_config=postgresinstance_params(),
        outargs=output_variables(),
    )
