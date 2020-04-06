"""
Simple deployment interface for
AHV_K8S_Discourse Blueprint

"""

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import SimpleDeployment, SimpleBlueprint
from calm.dsl.builtins import read_provider_spec, read_spec, read_local_file
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import CalmVariable as Var
from calm.dsl.builtins import action


SSH_USERNAME = read_local_file("username")
SSH_PASSWORD = read_local_file("password")
DISCOURSE_PASSWORD = read_local_file("discourse_password")

DefaultCred = basic_cred(SSH_USERNAME, SSH_PASSWORD, name="CENTOS", default=True)


class AHVPostgres(SimpleDeployment):
    """ AHV Postgres Deployment """

    provider_spec = read_provider_spec("ahv_spec.yaml")

    @action
    def __install__():
        Task.Exec.ssh(
            name="Install Postgres", filename="scripts/postgres_PackageInstallTask.sh"
        )


class MailDeployment(SimpleDeployment):
    """Mail Deployment"""

    deployment_spec = read_spec("mail_deployment.yaml")
    service_spec = read_spec("mail_service.yaml")


class RedisDeployment(SimpleDeployment):
    """Redis Deployment"""

    deployment_spec = read_spec("redis_deployment.yaml")
    service_spec = read_spec("redis_service.yaml")


class DiscourseDeployment(SimpleDeployment):
    """Discourse Deployment"""

    deployment_spec = read_spec("discourse_deployment.yaml")
    service_spec = read_spec("discourse_service.yaml")

    dependencies = [ref(AHVPostgres), ref(MailDeployment), ref(RedisDeployment)]

    @action
    def sample_action(container_name="discourse"):
        Task.Exec.escript(name="Sample Task", script="print 'Hello!'")


class DiscourseSimpleBlueprint(SimpleBlueprint):
    """Simple Discourse Blueprint"""

    DISCOURSE_DB_NAME = Var.Simple("discourse", label="database name")
    DISCOURSE_DB_PASSWORD = Var.Simple.Secret(
        DISCOURSE_PASSWORD, label="database password"
    )
    DISCOURSE_DB_USERNAME = Var.Simple("admin", label="database username")
    INSTANCE_PUBLIC_KEY = Var.Simple(
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDMGAS/K0Mb/uwFXwD+hkjguy7VMZk2hpuhwPl9FUZwVBrURf/i9QMJ5/paPEZixu8VlRx7Inu4iun7rQfrnfeIYInmBwspXHYiTK3oHJAgZnrAHVEf1p6YaxLINlT1NI5yOAGPRWW6of8rBDBH1ObwU2+wcSx/1H0uIs3aZNLufr+Rh628ACxAum2Gt8AVRj6ua2BPFyt5VTdclyysAmeh1AiixNgOZXOz6y/i4TbzpY78I3isuKpxsUeXX6jxEMQol406jHDUF6njEOPIQG2zVZ3QJlTG9OlN+NiyZG9WkZz0VG/6M8ixxIHHI2dNwUbBFv2HUu+8X9LTLFq2O7KjX9Hp7uZKBAySHA3eKaKHIp2bZuU1bT5PRPkggngX86xg+T+OMNnutbAiMnRJ8+FvD5So+5TIx4b9GgxAxure3x2yRPT9lOiQOB+CVpJPxR0Rn9bOI+wiPnD0kAGvK/fHT+pqL4PM+hTnJtp9rrCRzIQApBx1263jEcYffhW2epZQRO+he5CMawFJ5TBe08om2AaDJ8GQdrpF6YA3W8DzHbmL3DPVVHdmqPLn10o+LX4gv5SdIIDVGdjKOc1BCnLTRmM28d5+sLDt/M+kvcQgf0y0yDjMVjGECZkt39hbm4ELMHzZtzYLmHNhBZxRqHeJ7qFTuv1kx88OW3Xc5mbBNQ== centos@nutanix.com",
        label="public key",
    )

    @action
    def ScaleIn():
        COUNT = Var.Simple.int("1", is_mandatory=True, runtime=True)  # noqa
        Task.Scaling.scale_in(
            "@@{COUNT}@@", target=ref(DiscourseDeployment), name="Scale In"
        )

    @action
    def ScaleOut():
        COUNT = Var.Simple.int("1", is_mandatory=True, runtime=True)  # noqa
        Task.Scaling.scale_in(
            "@@{COUNT}@@", target=ref(DiscourseDeployment), name="Scale In"
        )

    credentials = [DefaultCred]
    deployments = [AHVPostgres, RedisDeployment, MailDeployment, DiscourseDeployment]


def test_json():

    import json

    bp_dict = DiscourseDeployment.make_bp_dict()
    generated_json = json.dumps(bp_dict, indent=4)
    print(generated_json)


if __name__ == "__main__":
    test_json()
