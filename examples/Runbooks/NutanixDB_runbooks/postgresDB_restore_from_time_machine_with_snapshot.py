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
        snapshot_with_timeStamp=Ref.NutanixDB.Snapshot(
            "era_auto_snapshot (2023-03-01 14:46:17)"
        ),
        time_zone="America/Resolute",
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
def nutanixdb_postgres_restore_with_snapshot():
    """NDB Postgres Restore From Time Machine Action Runbook"""
    Task.NutanixDB.PostgresDatabase.RestoreFromTimeMachine(
        name="postgres_restore_task_name",
        account=Ref.Account("ndb-account"),
        instance_config=postgresinstance_params(),
        outargs=output_variables(),
    )
