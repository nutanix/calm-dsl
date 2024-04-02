from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.builtins.models.ndb import (Database, PostgresDatabaseOutputVariables)
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import RunbookVariable as Variable


@runbook
def NDBSnapshotCreate():
    """ Runbook to create snapshot of a NDB Postgres Database Instance """

    tm_uuid = Variable.Simple.string("70ab57f4-1692-46c9-b762-f08f5d0edecf", runtime=True)

    # NDB Postgres Snapshot Action Runbook
    Task.NutanixDB.PostgresDatabase.CreateSnapshot(
        name="postgres_create_snapshot",
        account=Ref.Account("era-account"),
        instance_config=Database.Postgres.CreateSnapshot(
            snapshot_name="snap-from-dsl", remove_schedule_in_days=2,
            # time_machine="@@{tm_uuid}@@",
            time_machine=Ref.NutanixDB.TimeMachine(name="dnd-nirbhay-pg_TM"),
            database=Ref.NutanixDB.Database(name="dnd-nirbhay-pg"),
        ),
        outargs=PostgresDatabaseOutputVariables.CreateSnapshot(platform_data='myplatformdata'),
    )

    # Escript task to print output variables from above snapshot action
    Task.Exec.escript.py3(name="Print Outputs", script="print ('@@{myplatformdata}@@')")