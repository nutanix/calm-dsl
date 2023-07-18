"""
Calm Runbook Sample for ndb postgres restore operations
"""
import json

from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.builtins.models.ndb import (
    Database,
    PostgresDatabaseOutputVariables,
)
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.builtins.models.utils import read_local_file
from calm.dsl.constants import STRATOS

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
ACCOUNTS = DSL_CONFIG["ACCOUNTS"]


def postgresinstance_params():
    """Get the postgres instance config for postgres Restore From Time Machine action"""
    return Database.Postgres.RestoreFromTimeMachine(
        database="@@{db_uuid}@@",
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
def nutanixdb_postgres_restore():
    """NDB Postgres Restore From Time Machine Action Runbook"""
    Task.NutanixDB.PostgresDatabase.RestoreFromTimeMachine(
        name="postgres_restore_task_name",
        account=Ref.Account(
            ACCOUNTS.get(STRATOS.PROVIDER.NDB, [{"NAME": ""}])[0]["NAME"]
        ),
        instance_config=postgresinstance_params(),
        outargs=output_variables(),
    )
