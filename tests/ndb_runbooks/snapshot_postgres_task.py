"""
Calm Runbook Sample for ndb postgres snapshot operations
"""
import json

from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.builtins.models.ndb import Database, PostgresDatabaseOutputVariables
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.builtins.models.utils import read_local_file
from calm.dsl.constants import STRATOS

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
ACCOUNTS = DSL_CONFIG["ACCOUNTS"]


@runbook
def nutanixdb_postgres_snapshot():
    """Runbook to create snapshot of a NDB Postgres Database Instance"""

    # NDB Postgres Snapshot Action Runbook
    Task.NutanixDB.PostgresDatabase.CreateSnapshot(
        name="postgres_create_snapshot",
        account=Ref.Account(
            ACCOUNTS.get(STRATOS.PROVIDER.NDB, [{"NAME": ""}])[0]["NAME"]
        ),
        instance_config=Database.Postgres.CreateSnapshot(
            snapshot_name="@@{snapshot_uuid}@@",
            remove_schedule_in_days=2,
            time_machine="@@{tm_uuid}@@",
            database="@@{db_uuid}@@",
        ),
        outargs=PostgresDatabaseOutputVariables.CreateSnapshot(
            platform_data="myplatformdata"
        ),
    )
