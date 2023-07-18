"""
Calm Runbook Sample for ndb postgres delete
"""
import json


from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.builtins.models.ndb import (
    Database,
)
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.builtins.models.utils import read_local_file
from calm.dsl.constants import STRATOS

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
ACCOUNTS = DSL_CONFIG["ACCOUNTS"]


def postgresinstance_params():
    """ "Get the postgres instance config for postgres create action"""
    return Database.Postgres.Delete(name="@@{db_uuid}@@")


@runbook
def nutanixdb_postgres_delete():
    """NDB Postgres Delete Action Runbook"""
    Task.NutanixDB.PostgresDatabase.Delete(
        name="task_name",
        account=Ref.Account(
            ACCOUNTS.get(STRATOS.PROVIDER.NDB, [{"NAME": ""}])[0]["NAME"]
        ),
        instance_config=postgresinstance_params(),
    )
