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
from calm.dsl.runbooks import RunbookVariable as Variable
from calm.dsl.runbooks import CalmEndpoint as Endpoint, ref
from calm.dsl.builtins import read_local_file

DATABASE_PASSWORD = read_local_file("database_password")
endpoint = ref(Endpoint.use_existing("PostgresClientVM"))


def create_postgres_database_server_params():
    """Get the Database server config for postgres create action"""
    return DatabaseServer.Postgres.Create(
        name="SS_NDB_VM_@@{calm_random}@@",
        cluster=Ref.NutanixDB.Cluster(name="auto_cluster_prod_1a6d724a3f30"),
        software_profile=Ref.NutanixDB.Profile.Software(name="POSTGRES_10.4_OOB"),
        software_profile_version=Ref.NutanixDB.Profile.Software_Version(
            name="POSTGRES_10.4_OOB (1.0)"
        ),
        compute_profile=Ref.NutanixDB.Profile.Compute(name="CUSTOM_COMPUTE_PROFILE"),
        network_profile=Ref.NutanixDB.Profile.Network(name="VLAN_STATIC_PROFILE"),
        ip_address="@@{user_provided_static_ip}@@",
        ssh_public_key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC5GGnkZH75LzRFxOh4LcM0owSLn+1nvxP8tcw2PeXmdi82N1Fe8RZ3m5SkJqxJO2BvC39McyovNFIXC2LN2HeXuvovB6C0v1PGNb7oq2I5QrnRRUp1Tm4OJQN9cNZZ8MYaAcd0LokodrXgwpUQ4zlDdmlza1sDGQxXg4Dxvh5N/Y+rMjYdFbRSYmzzqI5aSHty8Shg9rbrqebFhTVCvzyQJzE/0PS3WUnCAbhLovLI/sdnTyM0CAm+Y6ui+1EFQkyg2VkbjJ6Y2foFRPJufqrnQS6S/njUeD5US3W4r8nMOxRZutRlFoado/yR+9MOkGn57NhIkMhji8wTH6SVtq2m09P+3/1Z9P+rASIS0rmH80XwwUVhfSyJ/J5dN0Axu8Bfqa9T40VDRRsoVKs79BRFr/5XRayS/O6jfGw6biYKJLeU9vV7OxtjzIuMDlbnsshuCcGtNMfI9W73F9VlKfKdQx2n547KEx79DlEJg4mtoaxkguvDo/aTH+0IJTF2BMh2iqL23ie6BkRVjHfhwWFM2WDRdHhDLcuAYSPP/sTuOEZgkElzK+ODahAXoglgTkqJeq2MiJ3tAmi39k9EKuTDR2xn1BLo/B4dMq1jkQJwVfEP+jD4eRTrlhZ8ZycIZgeY4c5MGqUNW9WfFuKOHogWEWMbuM3C8LLUFB4T1H5yDQ== mitesh.madaan@nutanix.com",
    )


def create_postgresinstance_params():
    """Get the postgres instance config for postgres create action runbook update"""
    return Database.Postgres.Create(
        name="SS_NDB_VM_INSTANCE_@@{calm_random}@@",
        database_parameter_profile=Ref.NutanixDB.Profile.Database_Parameter(
            name="DEFAULT_POSTGRES_PARAMS"
        ),
        initial_database_name="@@{initial_database_name}@@",
        initial_database_password="@@{database_password}@@",
        listener_port="5432",
        size="70",
    )


def create_postgres_timemachine_params():
    """Get the Time Machine config for postgres create action"""
    return TimeMachine.Postgres.Create(
        name="SS_NDB_Timemachine_@@{calm_random}@@",
        sla=Ref.NutanixDB.SLA(name="DEFAULT_OOB_BRONZE_SLA"),
        snapshottimeofday__hours=5,
        snapshottimeofday__minutes=0,
        snapshottimeofday__seconds=0,
        snapshots_perday=1,
        logbackup_interval=30,
        weeklyschedule__dayofweek="MONDAY",
        monthlyschedule__dayofmonth=1,
    )


@runbook
def nutanixdb_postgres_demo(default=endpoint):
    """
    This Runbook showcases an example where IP address can be reserved from an IPAM(Simulated in the example) and assigned to the DB server VM in NDB.
    This runbook leverages the Database operation tasks introduced in NCM Self Service 3.7.0.
    In addition, after the DB is created in NDB another placeholder tasks to run additional automation/tasks on that DB is provided.
    Two additional tasks - one to create a snapshot and the other to delete the DB is also provided.
    """

    database_password = Variable.Simple.Secret(
        value=DATABASE_PASSWORD,
        label="Database User's password",
        runtime=False,
        is_hidden=True,
        description="Password for accessing the postgres instance via any postgres clients like psql etc..,.",
    )
    database_user = Variable.Simple(
        value="postgres",
        label="Database User",
        runtime=False,
        is_hidden=True,
        description="Username for accessing the postgres instance via any postgres clients like psql etc..,.",
    )
    initial_database_name = Variable.Simple(
        value="ss_ndb_db",
        label="Database Name",
        runtime=False,
        is_hidden=True,
        description="Name of database to create, when DB instance gets created",
    )
    user_provided_static_ip = Variable.Simple(
        value="10.44.9.130",
        label="IP Address",
        is_mandatory=True,
        description="Please provide a static IP address to simulate the IPAM IP reservation. Preferably, choose between \n10.44.9.131 and 10.44.9.158",
    )

    # Reserve IP address for postgres VM
    Task.Exec.escript(
        filename="scripts/ReserveanIPAddress.py", name="Reserve an IP Address"
    )

    # Create PostgresSQL db in database
    Task.NutanixDB.PostgresDatabase.Create(
        name="Create PostgreSQL DB in NDB",
        account=Ref.Account("dnd_era_primary_account"),
        database_server_config=create_postgres_database_server_params(),
        instance_config=create_postgresinstance_params(),
        timemachine_config=create_postgres_timemachine_params(),
    )

    # Create a Table in Database created above
    Task.Exec.ssh(
        filename="scripts/CreateTableinthedatabase.sh",
        name="Create Table in the database",
    )

    # Get Time Machine ID for database created above
    Task.SetVariable.escript(
        filename="scripts/GetTimemachineID.py",
        name="Get Time machine ID",
        variables=["time_machine_id"],
    )

    # Create a Snapshot in Database created above
    Task.NutanixDB.PostgresDatabase.CreateSnapshot(
        name="Create Snapshot",
        account=Ref.Account("dnd_era_primary_account"),
        instance_config=Database.Postgres.CreateSnapshot(
            snapshot_name="ss_ndb_snap",
            remove_schedule_in_days=1,
            time_machine="@@{time_machine_id}@@",
        ),
        outargs=PostgresDatabaseOutputVariables.CreateSnapshot(),
    )

    # Delete the Database Create above
    Task.NutanixDB.PostgresDatabase.Delete(
        name="Delete DB",
        account=Ref.Account("dnd_era_primary_account"),
        instance_config=Database.Postgres.Delete(name="@@{database_instance_id}@@"),
    )
