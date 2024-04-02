"""
AHV_K8S_Discourse Blueprint

"""

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import action
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmVariable
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint, PODDeployment
from calm.dsl.builtins import read_provider_spec, read_spec, read_local_file


SSH_USERNAME = read_local_file(".tests/username")
SSH_PASSWORD = read_local_file(".tests/password")
DISCOURSE_PASSWORD = read_local_file(".tests/discourse_password")

DefaultCred = basic_cred(SSH_USERNAME, SSH_PASSWORD, name="CENTOS", default=True)


class AHVPostgresService(Service):
    """Postgres Service"""

    pass


class AHVPostgresPackage(Package):
    """Postgres Package"""

    services = [ref(AHVPostgresService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="Install Postgres", filename="scripts/postgres_PackageInstallTask.sh"
        )


class AHVPostgresSubstrate(Substrate):
    """Postgres Substrate"""

    provider_spec = read_provider_spec("ahv_spec.yaml")


class AHVPostgresDeployment(Deployment):
    """Postgres Deployment"""

    packages = [ref(AHVPostgresPackage)]
    substrate = ref(AHVPostgresSubstrate)


class MailContainer(Service):
    pass


class MailDeployment(PODDeployment):
    """Mail Deployment"""

    containers = [MailContainer]
    deployment_spec = read_spec("mail_deployment.yaml")
    service_spec = read_spec("mail_service.yaml")


class RedisContainer(Service):
    pass


class RedisDeployment(PODDeployment):
    """Redis Deployment"""

    containers = [RedisContainer]
    deployment_spec = read_spec("redis_deployment.yaml")
    service_spec = read_spec("redis_service.yaml")


class DiscourseContainer(Service):

    dependencies = [ref(AHVPostgresService), ref(MailContainer), ref(RedisContainer)]

    @action
    def sample_action():
        CalmTask.Exec.escript.py3(name="Sample Task", script="print ('Hello!')")


class DiscourseDeployment(PODDeployment):
    """Discourse Deployment"""

    containers = [DiscourseContainer]
    deployment_spec = read_spec("discourse_deployment.yaml")
    service_spec = read_spec("discourse_service.yaml")


class DefaultProfile(Profile):
    """Sample application profile with variables"""

    DISCOURSE_DB_NAME = CalmVariable.Simple("discourse", label="database name")
    DISCOURSE_DB_PASSWORD = CalmVariable.Simple.Secret(
        DISCOURSE_PASSWORD, label="database password"
    )
    DISCOURSE_DB_USERNAME = CalmVariable.Simple("admin", label="database username")
    INSTANCE_PUBLIC_KEY = CalmVariable.Simple(
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDMGAS/K0Mb/uwFXwD+hkjguy7VMZk2hpuhwPl9FUZwVBrURf/i9QMJ5/paPEZixu8VlRx7Inu4iun7rQfrnfeIYInmBwspXHYiTK3oHJAgZnrAHVEf1p6YaxLINlT1NI5yOAGPRWW6of8rBDBH1ObwU2+wcSx/1H0uIs3aZNLufr+Rh628ACxAum2Gt8AVRj6ua2BPFyt5VTdclyysAmeh1AiixNgOZXOz6y/i4TbzpY78I3isuKpxsUeXX6jxEMQol406jHDUF6njEOPIQG2zVZ3QJlTG9OlN+NiyZG9WkZz0VG/6M8ixxIHHI2dNwUbBFv2HUu+8X9LTLFq2O7KjX9Hp7uZKBAySHA3eKaKHIp2bZuU1bT5PRPkggngX86xg+T+OMNnutbAiMnRJ8+FvD5So+5TIx4b9GgxAxure3x2yRPT9lOiQOB+CVpJPxR0Rn9bOI+wiPnD0kAGvK/fHT+pqL4PM+hTnJtp9rrCRzIQApBx1263jEcYffhW2epZQRO+he5CMawFJ5TBe08om2AaDJ8GQdrpF6YA3W8DzHbmL3DPVVHdmqPLn10o+LX4gv5SdIIDVGdjKOc1BCnLTRmM28d5+sLDt/M+kvcQgf0y0yDjMVjGECZkt39hbm4ELMHzZtzYLmHNhBZxRqHeJ7qFTuv1kx88OW3Xc5mbBNQ== centos@nutanix.com",
        label="public key",
    )

    deployments = [
        AHVPostgresDeployment,
        DiscourseDeployment,
        RedisDeployment,
        MailDeployment,
    ]

    @action
    def ScaleIn():
        COUNT = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)  # noqa
        CalmTask.Scaling.scale_in(
            "@@{COUNT}@@", target=ref(DiscourseDeployment), name="Scale In"
        )

    @action
    def ScaleOut():
        COUNT = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)  # noqa
        CalmTask.Scaling.scale_out(
            "@@{COUNT}@@", target=ref(DiscourseDeployment), name="Scale Out"
        )


class AHVDiscourseDslBlueprint(Blueprint):
    """AHV Discourse Blueprint"""

    credentials = [DefaultCred]
    services = [AHVPostgresService, MailContainer, RedisContainer, DiscourseContainer]
    packages = [AHVPostgresPackage]
    substrates = [AHVPostgresSubstrate]
    profiles = [DefaultProfile]


def main():
    print(AHVDiscourseDslBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
