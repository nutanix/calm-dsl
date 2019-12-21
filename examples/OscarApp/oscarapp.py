"""
Calm DSL Oscar App Blueprint

author: michael@nutanix.com
date:   2019-08-09
"""

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import action, parallel
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmVariable
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import provider_spec, read_provider_spec, read_local_file


ERA_PASSWD = read_local_file("era_passwd")
OBJECT_PASSWD = read_local_file("object_passwd")
CENTOS_PASSWD = read_local_file("centos_passwd")
PC_PASSWD = read_local_file("pc_passwd")
DB_PASSWD = read_local_file("db_passwd")

EraCreds = basic_cred("admin", ERA_PASSWD, name="era_creds")
ObjectsCreds = basic_cred("poseidon_access", OBJECT_PASSWD, name="objects_creds")
CentOsCreds = basic_cred("centos", CENTOS_PASSWD, name="centos_creds", default=True)
PCCreds = basic_cred("admin", PC_PASSWD, name="pc_creds")


class Postgres(Service):
    """Postgres Database Service"""

    pass


class Objects(Service):
    """Nutanix Objects Service"""

    pass


class Oscar(Service):
    """Oscar Web App Service"""

    dependencies = [ref(Postgres), ref(Objects)]

    CUSTOM_ALERT_UUID = CalmVariable.Simple(None)
    ALERT_TRIGGER_UUID = CalmVariable.Simple(None)
    ACTION_VMAMA_UUID = CalmVariable.Simple(None)
    ACTION_RA_UUID = CalmVariable.Simple(None)
    ACTION_EA_UUID = CalmVariable.Simple(None)
    ALERT_UUID = CalmVariable.Simple(None)
    ALERT_UID = CalmVariable.Simple(None)
    PLAYBOOK_UUID = CalmVariable.Simple(None)

    @action
    def __create__():

        CalmTask.Exec.ssh(
            name="01ConfigureSettings",
            filename="scripts/oscar/create/01ConfigureSettings.sh",
            cred=CentOsCreds,
        )
        CalmTask.Exec.ssh(
            name="02InitializeSite",
            filename="scripts/oscar/create/02InitializeSite.sh",
            cred=CentOsCreds,
        )

    @action
    def __start__():

        CalmTask.Exec.ssh(
            name="01StartWebServer",
            filename="scripts/oscar/start/01StartWebServer.sh",
            cred=CentOsCreds,
        )

    @action
    def __stop__():

        CalmTask.Exec.ssh(
            name="01StopWebServer",
            filename="scripts/oscar/stop/01StopWebServer.sh",
            cred=CentOsCreds,
        )


class Locust(Service):
    """Locust Load Generator Service"""

    load = CalmVariable.Simple.int("25")

    dependencies = [ref(Oscar)]

    @action
    def __start__():

        CalmTask.Exec.ssh(
            name="01GenerateLoad",
            filename="scripts/locust/start/GenerateLoad.sh",
            cred=CentOsCreds,
        )

    @action
    def __stop__():

        CalmTask.Exec.ssh(
            name="01StopLoad",
            filename="scripts/locust/stop/StopLoad.sh",
            cred=CentOsCreds,
        )


class PostgresPackage(Package):
    """Postgres Database Package"""

    services = [ref(Postgres)]


class ObjectsPackage(Package):
    """Nutanix Objects Package"""

    services = [ref(Objects)]


class OscarPackage(Package):
    """Oscar Web App Package"""

    services = [ref(Oscar)]

    @action
    def __install__():

        CalmTask.Exec.ssh(
            name="01InstallPython",
            filename="scripts/oscar/package_install/01InstallPython.sh",
            cred=CentOsCreds,
        )

        CalmTask.SetVariable.escript(
            name="02CreateAlert",
            filename="scripts/oscar/package_install/02CreateAlert.py",
            variables=["ALERT_UUID"],
        )

        CalmTask.SetVariable.escript(
            name="03GetAlertUid",
            filename="scripts/oscar/package_install/03GetAlertUid.py",
            variables=["ALERT_UID"],
        )

        CalmTask.SetVariable.escript(
            name="04GetTriggerTypes",
            filename="scripts/oscar/package_install/04GetTriggerTypes.py",
            variables=["ALERT_TRIGGER_UUID"],
        )

        CalmTask.SetVariable.escript(
            name="05GetActionTypes",
            filename="scripts/oscar/package_install/05GetActionTypes.py",
            variables=["ACTION_VMAMA_UUID", "ACTION_RA_UUID", "ACTION_EA_UUID"],
        )

        CalmTask.SetVariable.escript(
            name="06CreatePlaybook",
            filename="scripts/oscar/package_install/06CreatePlaybook.py",
            variables=["PLAYBOOK_UUID"],
        )

    @action
    def __uninstall__():

        CalmTask.Exec.ssh(
            name="01UninstallSoftware",
            filename="scripts/oscar/package_uninstall/01UninstallSoftware.sh",
            cred=CentOsCreds,
        )

        CalmTask.Exec.escript(
            name="02DeleteAlert",
            filename="scripts/oscar/package_uninstall/02DeleteAlert.py",
        )

        CalmTask.Exec.escript(
            name="03DeletePlaybook",
            filename="scripts/oscar/package_uninstall/03DeletePlaybook.py",
        )


class LocustPackage(Package):
    """Locust Load Generator Package"""

    services = [ref(Locust)]

    @action
    def __install__():

        CalmTask.Exec.ssh(
            name="01InstallLocust",
            filename="scripts/locust/package_install/01InstallLocust.sh",
            cred=CentOsCreds,
        )

        CalmTask.Exec.ssh(
            name="02CreateLocustFile",
            filename="scripts/locust/package_install/02CreateLocustFile.sh",
            cred=CentOsCreds,
        )


class Era_PostgreSQL_DB(Substrate):
    """Postgres VM provisioned by Era"""

    provider_type = "EXISTING_VM"
    provider_spec = provider_spec({"address": "@@{DB_SERVER_IP}@@"})
    readiness_probe = {
        "disabled": True,
        "delay_secs": "0",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(EraCreds),
    }

    @action
    def __pre_create__():

        CalmTask.SetVariable.escript(
            name="1GetClusterID",
            filename="scripts/postgres/precreate/1GetClusterID.py",
            variables=["CLUSTER_ID"],
        )
        CalmTask.SetVariable.escript(
            name="2GetProfileIDs",
            filename="scripts/postgres/precreate/2GetProfileIDs.py",
            variables=[
                "SOFTWARE_PROF_ID",
                "COMPUTE_PROF_ID",
                "NETWORK_PROF_ID",
                "DB_PARAM_ID",
                "TIMESTAMP",
            ],
        )
        CalmTask.SetVariable.escript(
            name="3GetSLAID",
            filename="scripts/postgres/precreate/3GetSLAID.py",
            variables=["SLA_ID", "DB_NAME"],
        )
        CalmTask.SetVariable.escript(
            name="4ProvisionDB",
            filename="scripts/postgres/precreate/4ProvisionDB.py",
            variables=["CREATE_OPERATION_ID"],
        )
        CalmTask.SetVariable.escript(
            name="5MonitorOperation",
            filename="scripts/postgres/precreate/5MonitorOperation.py",
            variables=["DB_ENTITY_NAME"],
        )
        CalmTask.SetVariable.escript(
            name="6GetDatabaseInfo",
            filename="scripts/postgres/precreate/6GetDatabaseInfo.py",
            variables=["DB_SERVER_IP", "DB_ID", "DB_SERVER_ID"],
        )

    @action
    def __post_delete__():

        CalmTask.SetVariable.escript(
            name="1CleanupDB",
            filename="scripts/postgres/postdelete/1CleanupDB.py",
            variables=["CLEANUP_OPERATION_ID"],
        )
        CalmTask.Exec.escript(
            name="2MonitorCleanupOp",
            filename="scripts/postgres/postdelete/2MonitorCleanupOp.py",
        )
        CalmTask.SetVariable.escript(
            name="3DeregisterDBServer",
            filename="scripts/postgres/postdelete/3DeregisterDBServer.py",
            variables=["DEREGISTER_OPERATION_ID"],
        )
        CalmTask.Exec.escript(
            name="4MonitorDeregOp",
            filename="scripts/postgres/postdelete/4MonitorDeregOp.py",
        )


class Object_Storage_Bucket(Substrate):
    """Nutanix Objects Storage Bucket Substrate"""

    provider_type = "EXISTING_VM"
    provider_spec = provider_spec({"address": "@@{objects_ip}@@"})
    readiness_probe = {
        "disabled": True,
        "delay_secs": "0",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(ObjectsCreds),
    }


class Oscar_AHV(Substrate):
    """Oscar Web App AHV Substrate"""

    provider_spec = read_provider_spec("ahv_spec.yaml")
    provider_spec.spec["name"] = "Oscar-@@{calm_time}@@"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "0",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(CentOsCreds),
    }


class Locust_AHV(Substrate):
    """Locust Load Generator AHV Substrate"""

    provider_spec = read_provider_spec("ahv_spec.yaml")
    provider_spec.spec["name"] = "Locust-@@{calm_time}@@"
    provider_spec.spec["resources"]["memory_size_mib"] = 2048
    readiness_probe = {
        "disabled": False,
        "delay_secs": "0",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(CentOsCreds),
    }


class PostgresDeployment(Deployment):
    """Postgres Database Deployment"""

    packages = [ref(PostgresPackage)]
    substrate = ref(Era_PostgreSQL_DB)


class ObjectsDeployment(Deployment):
    """Nutanix Objects Deployment"""

    packages = [ref(ObjectsPackage)]
    substrate = ref(Object_Storage_Bucket)


class OscarDeployment(Deployment):
    """Oscar Web App Deployment"""

    packages = [ref(OscarPackage)]
    substrate = ref(Oscar_AHV)


class LocustDeployment(Deployment):
    """Locust Load Generator Deployment"""

    packages = [ref(LocustPackage)]
    substrate = ref(Locust_AHV)


class Default(Profile):

    deployments = [
        PostgresDeployment,
        ObjectsDeployment,
        OscarDeployment,
        LocustDeployment,
    ]

    bucket_name = CalmVariable.Simple("oscarstatic", is_mandatory=True, runtime=True)

    compute_profile = CalmVariable.WithOptions.Predefined.string(
        ["DEFAULT_COMPUTE", "SMALL_COMPUTE", "LARGE_COMPUTE"],
        default="DEFAULT_COMPUTE",
        is_mandatory=True,
        runtime=True,
    )

    database_parameter = CalmVariable.Simple(
        "DEFAULT_POSTGRES_PARAMS", is_mandatory=True, runtime=True
    )

    db_name_prefix = CalmVariable.Simple(
        "oscar_django", is_mandatory=True, runtime=True
    )

    db_password = CalmVariable.Simple.Secret(
        DB_PASSWD, is_mandatory=True, runtime=True
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

    objects_ip = CalmVariable.Simple(
        "",
        regex=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
        is_mandatory=True,
        runtime=True,
    )

    sla_name = CalmVariable.Simple("GOLD", is_mandatory=True, runtime=True)

    software_profile = CalmVariable.Simple(
        "POSTGRES_10.4_OOB", is_mandatory=True, runtime=True
    )

    @action
    def Increase_Load():

        CalmTask.SetVariable.ssh(
            name="01IncreaseLoad",
            filename="scripts/locust/increase_load/01IncreaseLoad.sh",
            target=ref(Locust),
            variables=["load"],
        )

        CalmTask.Exec.ssh(
            name="02StopLoad",
            filename="scripts/locust/stop/StopLoad.sh",
            target=ref(Locust),
        )

        CalmTask.Exec.ssh(
            name="03StartLoad",
            filename="scripts/locust/start/GenerateLoad.sh",
            target=ref(Locust),
        )

    @action
    def Decrease_Load():

        CalmTask.SetVariable.ssh(
            name="01DecreaseLoad",
            filename="scripts/locust/decrease_load/01DecreaseLoad.sh",
            target=ref(Locust),
            variables=["load"],
        )

        CalmTask.Exec.ssh(
            name="02StopLoad",
            filename="scripts/locust/stop/StopLoad.sh",
            target=ref(Locust),
        )

        CalmTask.Exec.ssh(
            name="03StartLoad",
            filename="scripts/locust/start/GenerateLoad.sh",
            target=ref(Locust),
        )


class OscarDslBlueprint(Blueprint):
    """Oscar Application Blueprint"""

    credentials = [EraCreds, ObjectsCreds, CentOsCreds, PCCreds]
    services = [Postgres, Objects, Oscar, Locust]
    packages = [PostgresPackage, ObjectsPackage, OscarPackage, LocustPackage]
    substrates = [Era_PostgreSQL_DB, Object_Storage_Bucket, Oscar_AHV, Locust_AHV]
    profiles = [Default]


def main():
    print(OscarDslBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
