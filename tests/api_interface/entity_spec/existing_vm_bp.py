"""
Exsiting machine example.
Uses DND_Harry_CentosVM (10.51.152.238)
"""

import json

from calm.dsl.builtins import ref, basic_cred, action
from calm.dsl.builtins import CalmTask, CalmVariable
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import provider_spec, read_local_file


CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")

DefaultCred = basic_cred(
    CRED_USERNAME, CRED_PASSWORD, name="default cred", default=True
)


def test_ping_code():
    """Check if we can reach the VM"""
    from calm.dsl.tools import ping

    assert ping("10.51.152.238") is True


def test_ping_code_negative():
    """Check if we fail to reach the VM"""
    from calm.dsl.tools import ping

    assert ping("1.2.3.4") is False


class MySQLService(Service):

    ENV = CalmVariable.Simple("DEV")
    var1 = CalmVariable.Simple("0")
    var2 = CalmVariable.Simple("0")


class MySQLPackage(Package):

    foo = CalmVariable.Simple("bar")
    services = [ref(MySQLService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Task1", script="echo @@{foo}@@", cred=ref(DefaultCred))


class PHPService(Service):

    dependencies = [ref(MySQLService)]

    @action
    def test_action():

        # TODO: Need to fix this lint
        blah = CalmVariable.Simple("2")  # noqa
        CalmTask.Exec.ssh(name="Task2", script='echo "Hello"; sleep 10')
        CalmTask.Exec.ssh(
            name="Task3", script='echo "Hello again"; sleep 10', cred=ref(DefaultCred)
        )


class PHPPackage(Package):

    foo = CalmVariable.Simple("baz")
    services = [ref(PHPService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Task4", script="echo @@{foo}@@")


class ExistingVM(Substrate):
    """CentOS VM"""

    provider_type = "EXISTING_VM"
    provider_spec = provider_spec({"address": "10.46.8.98"})
    readiness_probe = {
        "disabled": False,
        "delay_secs": "0",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }

    @action
    def __pre_create__():
        CalmTask.Exec.escript(name="Pre Create Task", script="print 'Hello!'")


class LampDeployment(Deployment):

    packages = [ref(MySQLPackage), ref(PHPPackage)]
    substrate = ref(ExistingVM)
    min_replicas = "1"
    max_replicas = "2"


class DefaultProfile(Profile):

    nameserver = CalmVariable.Simple("10.40.64.15", label="Local DNS resolver")
    deployments = [LampDeployment]

    @action
    def test_profile_action():
        CalmTask.Exec.ssh(
            name="Task5", filename="scripts/sample_script.sh", target=ref(MySQLService)
        )
        PHPService.test_action(name="Task6")
        CalmTask.HTTP.get(
            "https://jsonplaceholder.typicode.com/posts/1",
            headers={"Content-Type": "application/json"},
            content_type="application/json",
            verify=True,
            status_mapping={200: True},
            response_paths={"foo_title": "$.title"},
            name="Test HTTP Task Get",
            target=ref(MySQLService),
        )
        CalmTask.HTTP.post(
            "https://jsonplaceholder.typicode.com/posts",
            body=json.dumps({"id": 1, "title": "foo", "body": "bar", "userId": 1}),
            headers={"Content-Type": "application/json"},
            content_type="application/json",
            verify=True,
            status_mapping={200: True},
            response_paths={"foo_title": "$.title"},
            name="Test HTTP Task Post",
            target=ref(MySQLService),
        )
        CalmTask.HTTP.put(
            "https://jsonplaceholder.typicode.com/posts/1",
            body=json.dumps({"id": 1, "title": "foo", "body": "bar", "userId": 1}),
            headers={"Content-Type": "application/json"},
            content_type="application/json",
            verify=True,
            status_mapping={200: True},
            response_paths={"foo_title": "$.title"},
            name="Test HTTP Task Put",
            target=ref(MySQLService),
        )
        CalmTask.HTTP.delete(
            "https://jsonplaceholder.typicode.com/posts/1",
            headers={"Content-Type": "application/json"},
            content_type="application/json",
            verify=True,
            status_mapping={200: True},
            name="Test HTTP Task Delete",
            target=ref(MySQLService),
        )
        CalmTask.HTTP(
            "PUT",
            "https://jsonplaceholder.typicode.com/posts/1",
            body=json.dumps({"id": 1, "title": "foo", "body": "bar", "userId": 1}),
            headers={"Content-Type": "application/json"},
            content_type="application/json",
            verify=True,
            status_mapping={200: True},
            response_paths={"foo_title": "$.title"},
            name="Test HTTP Task",
            target=ref(MySQLService),
        )
        CalmTask.Exec.escript(
            "print 'Hello World!'", name="Test Escript", target=ref(MySQLService)
        )
        CalmTask.SetVariable.escript(
            script="print 'var1=test'",
            name="Test Setvar Escript",
            variables=["var1"],
            target=ref(MySQLService),
        )
        CalmTask.SetVariable.ssh(
            script="echo 'var2=test'",
            name="Test Setvar SSH",
            variables=["var2"],
            target=ref(MySQLService),
        )
        CalmTask.Scaling.scale_out(1, target=ref(LampDeployment), name="Scale out Lamp")
        CalmTask.Delay(delay_seconds=60, target=ref(MySQLService))
        CalmTask.Scaling.scale_in(1, target=LampDeployment, name="Scale in Lamp")


class ExistingVMBlueprint(Blueprint):
    """Existing VM example"""

    credentials = [DefaultCred]
    services = [MySQLService, PHPService]
    packages = [MySQLPackage, PHPPackage]
    substrates = [ExistingVM]
    profiles = [DefaultProfile]


def main():
    print(ExistingVMBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
