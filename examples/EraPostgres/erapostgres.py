"""
Calm DSL Era Postgres Provision Blueprint

author: michael@nutanix.com
date:   2019-08-08
"""

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import action, parallel
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmVariable
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import provider_spec, read_local_file


CENTOS_PASSWD = read_local_file("passwd")
DB_PASSWD = read_local_file("db_passwd")

DefaultCred = basic_cred("admin", CENTOS_PASSWD, name="era_creds", default=True)


class Postgres(Service):
    pass


class PostgresPackage(Package):

    services = [ref(Postgres)]


class Era_PostgreSQL_DB(Substrate):
    """Postgres VM provisioned by Era"""

    provider_type = "EXISTING_VM"
    provider_spec = provider_spec({"address": "@@{DB_SERVER_IP}@@"})
    readiness_probe = {
        "disabled": True,
        "delay_secs": "0",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }

    @action
    def __pre_create__():

        CalmTask.SetVariable.escript.py3(
            name="1GetClusterID",
            filename="scripts/postgres/precreate/1GetClusterID.py",
            variables=["CLUSTER_ID"],
        )
        CalmTask.SetVariable.escript.py3(
            name="2GetProfileIDs",
            filename="scripts/postgres/precreate/2GetProfileIDs.py",
            variables=[
                "SOFTWARE_PROF_ID",
                "COMPUTE_PROF_ID",
                "NETWORK_PROF_ID",
                "DB_PARAM_ID",
            ],
        )
        CalmTask.SetVariable.escript.py3(
            name="3GetSLAID",
            filename="scripts/postgres/precreate/3GetSLAID.py",
            variables=["SLA_ID"],
        )
        CalmTask.SetVariable.escript.py3(
            name="4ProvisionDB",
            filename="scripts/postgres/precreate/4ProvisionDB.py",
            variables=["CREATE_OPERATION_ID"],
        )
        CalmTask.SetVariable.escript.py3(
            name="5MonitorOperation",
            filename="scripts/postgres/precreate/5MonitorOperation.py",
            variables=["DB_ENTITY_NAME"],
        )
        CalmTask.SetVariable.escript.py3(
            name="6GetDatabaseInfo",
            filename="scripts/postgres/precreate/6GetDatabaseInfo.py",
            variables=["DB_SERVER_IP", "DB_ID", "DB_SERVER_ID"],
        )

    @action
    def __post_delete__():

        CalmTask.SetVariable.escript.py3(
            name="1CleanupDB",
            filename="scripts/postgres/postdelete/1CleanupDB.py",
            variables=["CLEANUP_OPERATION_ID"],
        )
        CalmTask.Exec.escript.py3(
            name="2MonitorCleanupOp",
            filename="scripts/postgres/postdelete/2MonitorCleanupOp.py",
        )
        CalmTask.SetVariable.escript.py3(
            name="3DeregisterDBServer",
            filename="scripts/postgres/postdelete/3DeregisterDBServer.py",
            variables=["DEREGISTER_OPERATION_ID"],
        )
        CalmTask.Exec.escript.py3(
            name="4MonitorDeregOp",
            filename="scripts/postgres/postdelete/4MonitorDeregOp.py",
        )


class PostgresDeployment(Deployment):

    packages = [ref(PostgresPackage)]
    substrate = ref(Era_PostgreSQL_DB)


class Default(Profile):

    deployments = [PostgresDeployment]

    compute_profile = CalmVariable.WithOptions.Predefined.string(
        ["DEFAULT_OOB_COMPUTE", "SMALL_COMPUTE", "LARGE_COMPUTE"],
        default="DEFAULT_OOB_COMPUTE",
        is_mandatory=True,
        runtime=True,
    )

    database_parameter = CalmVariable.Simple(
        "DEFAULT_POSTGRES_PARAMS", is_mandatory=True, runtime=True
    )

    db_name = CalmVariable.Simple(
        'psql_@@{calm_time("%Y%m%d%H%M")}@@', is_mandatory=True, runtime=True
    )

    db_password = CalmVariable.Simple(
        DB_PASSWD, is_hidden=True, is_mandatory=True, runtime=True
    )

    db_public_key = CalmVariable.Simple(
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDUm18acWv344TgOXBuOnozuSXytDuqKFVE0+x7CK/dZ6Y331lBF+f8AE/Ng3tzxvCDUeth3pa7XO/Y95zc+hTLGROBmWdgidfykBi2FeQ6hZOcsUDslPUL3Ig8UpPzbOva276YP3266+1BGjLi14neBSJvpSV2DvXQovMb57mhAWs9BlVj3UIviHBMQYXc9RUiyoTBYphqQi5THsQafEFEA+3EJ/NLhqF4CTRZoxMk+VDZbQCCYk0SNEDvDnhEUCIQW1KDg8HDaHrCcRE8DKwi1dgDjASwcUeDuaFto0WrUaj8FdOvaIwjLKYC9DUgsPel+FOLNkg0cPi0vuXb1CGZ era@domain.com",
        is_mandatory=True,
        runtime=True,
    )

    era_ip = CalmVariable.Simple(
        "",
        regex=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
        is_mandatory=True,
        runtime=True,
    )

    network_profile = CalmVariable.Simple(
        "DEFAULT_OOB_NETWORK", is_mandatory=True, runtime=True
    )

    sla_name = CalmVariable.Simple("GOLD", is_mandatory=True, runtime=True)

    software_profile = CalmVariable.Simple(
        "POSTGRES_10.4_OOB", is_mandatory=True, runtime=True
    )


class EraPostgresDslBlueprint(Blueprint):
    """ Era Postgres Provisioning DSL Blueprint """

    credentials = [DefaultCred]
    services = [Postgres]
    packages = [PostgresPackage]
    substrates = [Era_PostgreSQL_DB]
    profiles = [Default]


def main():
    print(EraPostgresDslBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
