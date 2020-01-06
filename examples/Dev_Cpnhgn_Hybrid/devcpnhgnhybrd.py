"""
Calm DSL .DEV Copenhagen Hybrid Cloud Blueprint

author: michael@nutanix.com
date:   2019-09-27
"""

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import action, parallel
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmVariable
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint, PODDeployment
from calm.dsl.builtins import provider_spec, read_provider_spec, read_spec, read_local_file


ERA_KEY = read_local_file("era_key")
CENTOS_KEY = read_local_file("centos_key")
KARBON_KEY = read_local_file("karbon_key")
DB_PASSWD = read_local_file("db_passwd")


EraCreds = basic_cred("admin", ERA_KEY, name="era_creds")
CentOsCreds = basic_cred("centos", CENTOS_KEY, name="centos_creds", type="KEY", default=True)
KarbonCreds = basic_cred("admin", KARBON_KEY, name="karbon")


class Postgres(Service):

    pass


class WebServer1(Service):
    """WebServer1 AHV Service"""

    dependencies = [ref(Postgres)]

    @action
    def __create__():

        CalmTask.Exec.ssh(
            name="1CloneRepo",
            filename="scripts/webserver/create/CloneRepo.sh",
            cred=CentOsCreds,
        )
        CalmTask.Exec.ssh(
            name="2ConfigureSite",
            filename="scripts/webserver/create/ConfigureSite.sh",
            cred=CentOsCreds,
        )
        CalmTask.Exec.ssh(
            name="3DatabaseSetup",
            filename="scripts/webserver/create/DatabaseSetupAHV.sh",
            cred=CentOsCreds,
        )

    @action
    def __start__():

        CalmTask.Exec.ssh(
            name="1StartWebServer",
            filename="scripts/webserver/start/StartWebServer.sh",
            cred=CentOsCreds,
        )

    @action
    def __stop__():

        CalmTask.Exec.ssh(
            name="1StopWebServer",
            filename="scripts/webserver/stop/StopWebServer.sh",
            cred=CentOsCreds,
        )


class WebServer2(Service):
    """WebServer2 AWS Service"""

    dependencies = [ref(Postgres)]

    @action
    def __create__():

        CalmTask.Exec.ssh(
            name="1CloneRepo",
            filename="scripts/webserver/create/CloneRepo.sh",
            cred=CentOsCreds,
        )
        CalmTask.Exec.ssh(
            name="2ConfigureSite",
            filename="scripts/webserver/create/ConfigureSite.sh",
            cred=CentOsCreds,
        )
        CalmTask.Exec.ssh(
            name="3DatabaseSetup",
            filename="scripts/webserver/create/DatabaseSetupAWS.sh",
            cred=CentOsCreds,
        )

    @action
    def __start__():

        CalmTask.Exec.ssh(
            name="1StartWebServer",
            filename="scripts/webserver/start/StartWebServer.sh",
            cred=CentOsCreds,
        )

    @action
    def __stop__():

        CalmTask.Exec.ssh(
            name="1StopWebServer",
            filename="scripts/webserver/stop/StopWebServer.sh",
            cred=CentOsCreds,
        )


class WebServerK8s(Service):
    """WebServer Kubernetes Service"""

    dependencies = [ref(Postgres)]


class HaProxy(Service):
    """HaProxy Service"""

    dependencies = [ref(WebServer1), ref(WebServer2), ref(WebServerK8s)]


class PostgresPackage(Package):

    services = [ref(Postgres)]


class WebServer1Package(Package):

    services = [ref(WebServer1)]

    @action
    def __install__():

        CalmTask.Exec.ssh(
            name="1InstallSoftware",
            filename="scripts/webserver/package_install/InstallSoftware.sh",
            cred=CentOsCreds,
        )


class WebServer2Package(Package):

    services = [ref(WebServer2)]

    @action
    def __install__():

        CalmTask.Exec.ssh(
            name="1InstallSoftware",
            filename="scripts/webserver/package_install/InstallSoftware.sh",
            cred=CentOsCreds,
        )


class HaProxyPackage(Package):

    services = [ref(HaProxy)]

    @action
    def __install__():

        CalmTask.Exec.ssh(
            name="1ConfigureHaProxy",
            filename="scripts/haproxy/package_install/ConfigureHaProxy.sh",
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
        "credential": ref(CentOsCreds),
    }

    @action
    def __pre_create__():

        CalmTask.SetVariable.escript(
            name="1GetClusterID",
            filename="scripts/postgres/precreate/1GetClusterID.py",
            variables=["CLUSTER_ID", "TIME"],
        )
        CalmTask.SetVariable.escript(
            name="2GetProfileIDs",
            filename="scripts/postgres/precreate/2GetProfileIDs.py",
            variables=[
                "SOFTWARE_PROF_ID",
                "COMPUTE_PROF_ID",
                "NETWORK_PROF_ID",
                "DB_PARAM_ID",
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


class WebServer1_AHV(Substrate):
    """WebServer1 AHV Substrate"""

    provider_spec = read_provider_spec("ahv_spec.yaml")
    provider_spec.spec["name"] = "wb1-ahv-@@{calm_time}@@"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "0",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(CentOsCreds),
    }


class WebServer2_AWS(Substrate):
    """WebServer2 AWS Substrate"""

    provider_type = "AWS_VM"
    provider_spec = read_provider_spec("aws_spec.yaml")
    provider_spec.spec["name"] = "wb2-aws-@@{calm_time}@@"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(CentOsCreds),
    }


class HaProxy_AHV(Substrate):
    """HaProxy AHV Substrate"""

    provider_spec = read_provider_spec("ahv_spec.yaml")
    provider_spec.spec["name"] = "ha-@@{calm_time}@@"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "10",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(CentOsCreds),
    }


class PostgresDeployment(Deployment):
    """Era Postgres Deployment"""

    packages = [ref(PostgresPackage)]
    substrate = ref(Era_PostgreSQL_DB)


class WebServer1Deployment(Deployment):
    """WebServer1 AHV Deployment"""

    packages = [ref(WebServer1Package)]
    substrate = ref(WebServer1_AHV)


class WebServer2Deployment(Deployment):
    """WebServer2 AWS Deployment"""

    packages = [ref(WebServer2Package)]
    substrate = ref(WebServer2_AWS)


class WebServerK8sDeployment(PODDeployment):
    """WebServer Kubernetes Deployment"""

    containers = [WebServerK8s]
    deployment_spec = read_spec("webserver_deployment.yaml")
    service_spec = read_spec("webserver_service.yaml")

    dependencies = [ref(PostgresDeployment)]


class HaProxyDeployment(Deployment):

    packages = [ref(HaProxyPackage)]
    substrate = ref(HaProxy_AHV)


class Default(Profile):

    deployments = [
        PostgresDeployment,
        WebServer1Deployment,
        WebServer2Deployment,
        WebServerK8sDeployment,
        HaProxyDeployment,
    ]

    compute_profile = CalmVariable.WithOptions.Predefined.string(
        ["DEFAULT_OOB_COMPUTE", "SMALL_COMPUTE", "LARGE_COMPUTE"],
        default="DEFAULT_OOB_COMPUTE",
        is_mandatory=True,
        runtime=True,
    )
    database_parameter = CalmVariable.Simple(
        "DEFAULT_POSTGRES_PARAMS", is_mandatory=True, runtime=True
    )
    db_prefix = CalmVariable.Simple("psql", is_mandatory=True, runtime=True)
    db_password = CalmVariable.Simple(
        DB_PASSWD, is_hidden=True, is_mandatory=True, runtime=True
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
    kubemaster_ip = CalmVariable.Simple("", is_mandatory=True, runtime=True)

    @action
    def UpdateApp():
        """This action updates the app with the most recent code from git"""

        label = CalmVariable.Simple("latest", is_mandatory=True, runtime=True)

        with parallel():
            CalmTask.Exec.ssh(
                name="1RemoveWS1",
                filename="scripts/haproxy/updateapp/RemoveWS1.sh",
                target=ref(HaProxy),
            )
            CalmTask.Exec.escript(
                name="1UpdateContainers",
                filename="scripts/webserver/updateapp/UpdateContainers.py",
                target=ref(WebServerK8s),
            )

        CalmTask.Exec.ssh(
            name="2StopWebServer",
            filename="scripts/webserver/stop/StopWebServer.sh",
            target=ref(WebServer1),
        )
        CalmTask.Exec.ssh(
            name="3UpdateFromGit",
            filename="scripts/webserver/updateapp/UpdateFromGit.sh",
            target=ref(WebServer1),
        )
        CalmTask.Exec.ssh(
            name="4ConfigureSite",
            filename="scripts/webserver/create/ConfigureSite.sh",
            target=ref(WebServer1),
        )
        CalmTask.Exec.ssh(
            name="5StartWebServer",
            filename="scripts/webserver/start/StartWebServer.sh",
            target=ref(WebServer1),
        )
        CalmTask.Exec.ssh(
            name="6AddWS1",
            filename="scripts/haproxy/updateapp/AddWS1.sh",
            target=ref(HaProxy),
        )
        CalmTask.Exec.ssh(
            name="7Delay",
            filename="scripts/haproxy/updateapp/Delay.sh",
            target=ref(HaProxy),
        )
        CalmTask.Exec.ssh(
            name="8RemoveWS2",
            filename="scripts/haproxy/updateapp/RemoveWS2.sh",
            target=ref(HaProxy),
        )
        CalmTask.Exec.ssh(
            name="9StopWebServer",
            filename="scripts/webserver/stop/StopWebServer.sh",
            target=ref(WebServer2),
        )
        CalmTask.Exec.ssh(
            name="10UpdateFromGit",
            filename="scripts/webserver/updateapp/UpdateFromGit.sh",
            target=ref(WebServer2),
        )
        CalmTask.Exec.ssh(
            name="11ConfigureSite",
            filename="scripts/webserver/create/ConfigureSite.sh",
            target=ref(WebServer2),
        )
        CalmTask.Exec.ssh(
            name="12StartWebServer",
            filename="scripts/webserver/start/StartWebServer.sh",
            target=ref(WebServer2),
        )
        CalmTask.Exec.ssh(
            name="13AddWS2",
            filename="scripts/haproxy/updateapp/AddWS2.sh",
            target=ref(HaProxy),
        )


class DevCpnhgnHybridDSL(Blueprint):
    """* [Application Link](http://@@{HaProxy.address}@@/)"""

    credentials = [EraCreds, CentOsCreds, KarbonCreds]
    services = [Postgres, WebServer1, WebServer2, WebServerK8s, HaProxy]
    packages = [PostgresPackage, WebServer1Package, WebServer2Package, HaProxyPackage]
    substrates = [Era_PostgreSQL_DB, WebServer1_AHV, WebServer2_AWS, HaProxy_AHV]
    profiles = [Default]


def main():
    print(DevCpnhgnHybridDSL.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
