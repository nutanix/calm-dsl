import uuid

from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.builtins.models.ndb import (
    Database,
)
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task


def postgresinstance_params():
    """ "Get the postgres instance config for postgres create action"""
    return Database.Postgres.Delete(
        name=Ref.NutanixDB.Database(name="bekkam-pg-dnd")
    )


@runbook
def NDB_postgressDB_delete():
    """NDB Postgres Delete Action Runbook"""
    Task.NutanixDB.PostgresDatabase.Delete(
        name="task_name",
        account=Ref.Account("era1"),
        instance_config=postgresinstance_params()
    )
