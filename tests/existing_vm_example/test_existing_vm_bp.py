"""
Exsiting machine example.
Uses DND_Harry_CentosVM (10.51.152.238)

"""

import json

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import action, parallel
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmVariable
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import provider_spec, read_local_file

CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")
TEST_PC_IP = read_local_file(".tests/test_pc_ip")
DNS_SERVER = read_local_file(".tests/dns_server")

DefaultCred = basic_cred(
    CRED_USERNAME, CRED_PASSWORD, name="default cred", default=True
)


# def test_ping_code():
#     """Check if we can reach the VM"""
#     from calm.dsl.tools import ping

#     assert ping(TEST_PC_IP) is True


# def test_ping_code_negative():
#     """Check if we fail to reach the VM"""
#     from calm.dsl.tools import ping

#     assert ping("1.2.3.4") is False


class MySQLService(Service):

    ENV = CalmVariable.Simple("DEV")
    var1 = CalmVariable.Simple("0")
    var2 = CalmVariable.Simple("0")


class MySQLPackage(Package):

    foo = CalmVariable.Simple("bar", runtime=True)
    services = [ref(MySQLService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Task1", script="echo @@{foo}@@", cred=ref(DefaultCred))


class PHPService(Service):

    dependencies = [ref(MySQLService)]

    @action
    def test_action():

        action_var1 = CalmVariable.Simple("val1")  # noqa
        action_var2 = CalmVariable.Simple("val2")  # noqa
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
    provider_spec = provider_spec({"address": TEST_PC_IP})
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

    nameserver = CalmVariable(DNS_SERVER, label="Local DNS resolver")
    deployments = [LampDeployment]
    var1 = CalmVariable.Simple(
        "var1_val",
        label="var1_label",
        regex="^[a-zA-Z0-9_]+$",
        validate_regex=True,
        runtime=True,
        description="var1 description",
    )
    var2 = CalmVariable.Simple.Secret(
        "var2_val",
        label="var2_label",
        regex="^[a-zA-Z0-9_]+$",
        validate_regex=True,
        is_hidden=True,
        is_mandatory=True,
        description="var2 description",
    )
    var3 = CalmVariable.Simple.int(
        "42",
        label="var3_label",
        validate_regex=True,
        runtime=True,
        is_hidden=True,
        is_mandatory=True,
        description="var3 description",
    )
    var4 = CalmVariable.Simple.date(
        "30/02/2019",
        label="var4_label",
        validate_regex=True,
        runtime=True,
        description="var4 description",
    )
    var5 = CalmVariable.Simple.time(
        "22:35:00",
        label="var5_label",
        validate_regex=True,
        runtime=True,
        description="var5 description",
    )
    var6 = CalmVariable.Simple.datetime(
        "30/02/2019 - 22:35:00",
        label="var6_label",
        validate_regex=True,
        runtime=True,
        description="var6 description",
    )
    var7 = CalmVariable.Simple.multiline(
        "x\ny", label="var7_label", runtime=True, description="var7 description"
    )
    var8 = CalmVariable.Simple.Secret.int(
        "42", label="var8_label", validate_regex=True, description="var8 description"
    )
    var9 = CalmVariable.Simple.Secret.date(
        "30/02/2019",
        label="var9_label",
        validate_regex=True,
        description="var9 description",
    )
    var10 = CalmVariable.Simple.Secret.time(
        "22:35:00",
        label="var10_label",
        validate_regex=True,
        description="var10 description",
    )
    var11 = CalmVariable.Simple.Secret.datetime(
        "30/02/2019 - 22:35:00",
        label="var11_label",
        validate_regex=True,
        description="var11 description",
    )
    var12 = CalmVariable.Simple.Secret.multiline(
        "x\ny", label="var12_label", description="var12 description"
    )
    var13 = CalmVariable.WithOptions(
        ["var13_val1", "var13_val2"],
        default="var13_val1",
        label="var13_label",
        regex="^[a-zA-Z0-9_]+$",
        validate_regex=True,
        runtime=True,
        description="var13 description",
    )
    var14 = CalmVariable.WithOptions.Predefined.int(
        ["0", "1"],
        label="var14_label",
        regex="^[0-9]+$",
        validate_regex=True,
        runtime=True,
        description="var14 description",
    )
    var15 = CalmVariable.WithOptions.Predefined.date(
        ["30/02/2019", "31/06/2019"],
        default="30/02/2019",
        label="var15_label",
        validate_regex=True,
        runtime=True,
        description="var15 description",
    )
    var16 = CalmVariable.WithOptions.Predefined.time(
        ["22:35:00", "10:35:00"],
        default="22:35:00",
        label="var16_label",
        validate_regex=True,
        runtime=True,
        description="var16 description",
    )
    var17 = CalmVariable.WithOptions.Predefined.datetime(
        ["30/02/2019 - 22:35:00", "31/06/2019 - 10:35:00"],
        default="30/02/2019 - 22:35:00",
        label="var17_label",
        validate_regex=True,
        runtime=True,
        description="var17 description",
    )
    var18 = CalmVariable.WithOptions.Predefined.multiline(
        ["x\ny", "a\nb"],
        default="x\ny",
        label="var18_label",
        validate_regex=True,
        runtime=True,
        description="var18 description",
    )
    var19 = CalmVariable.WithOptions.Predefined.Array(
        ["var19_val1", "var19_val2"],
        defaults=["var19_val1", "var19_val2"],
        label="var19_label",
        regex="^[a-zA-Z0-9_]+$",
        validate_regex=True,
        runtime=True,
        description="var19 description",
    )
    var20 = CalmVariable.WithOptions.Predefined.Array.int(
        ["0", "1"],
        label="var20_label",
        regex="^[0-9]+$",
        validate_regex=True,
        runtime=True,
        description="var20 description",
    )
    var21 = CalmVariable.WithOptions.Predefined.Array.date(
        ["30/02/2019", "31/06/2019"],
        defaults=["30/02/2019"],
        label="var21_label",
        validate_regex=True,
        runtime=True,
        description="var21 description",
    )
    var22 = CalmVariable.WithOptions.Predefined.Array.time(
        ["22:35:00", "10:35:00"],
        defaults=["22:35:00", "10:35:00"],
        label="var22_label",
        validate_regex=True,
        runtime=True,
        description="var22 description",
    )
    var23 = CalmVariable.WithOptions.Predefined.Array.datetime(
        ["30/02/2019 - 22:35:00", "31/06/2019 - 10:35:00"],
        defaults=["30/02/2019 - 22:35:00", "31/06/2019 - 10:35:00"],
        label="var23_label",
        validate_regex=True,
        runtime=True,
        description="var23 description",
    )
    var24 = CalmVariable.WithOptions.Predefined.Array.multiline(
        ["x\ny", "a\nb"],
        defaults=["x\ny", "a\nb"],
        label="var24_label",
        validate_regex=True,
        runtime=True,
        description="var24 description",
    )
    var25 = CalmVariable.WithOptions.FromTask(
        CalmTask.HTTP.get(
            "https://jsonplaceholder.typicode.com/posts/1",
            # Headers in HTTP variables are bugged:
            # https://jira.nutanix.com/browse/CALM-13724
            # headers={"Content-Type": "application/json"},
            content_type="application/json",
            verify=True,
            status_mapping={200: True},
            response_paths={"var25": "$.title"},
        ),
        label="var25_label",
        description="var25 description",
    )
    var26 = CalmVariable.WithOptions.FromTask.int(
        CalmTask.Exec.escript(script="print '0'"),
        label="var26_label",
        validate_regex=True,
        description="var26 description",
    )
    var27 = CalmVariable.WithOptions.FromTask.date(
        CalmTask.Exec.escript(script="print '30/02/2019'"),
        label="var27_label",
        validate_regex=True,
        description="var27 description",
    )
    var28 = CalmVariable.WithOptions.FromTask.time(
        CalmTask.Exec.escript(script="print '22:35:00'"),
        label="var28_label",
        validate_regex=True,
        description="var28 description",
    )
    var29 = CalmVariable.WithOptions.FromTask.datetime(
        CalmTask.Exec.escript(script="print '30/02/2019 - 22:35:00'"),
        label="var29_label",
        validate_regex=True,
        description="var29 description",
    )
    var30 = CalmVariable.WithOptions.FromTask.multiline(
        CalmTask.Exec.escript(script="print 'x\ny'"),
        label="var30_label",
        description="var30 description",
    )
    var31 = CalmVariable.WithOptions.FromTask.Array(
        CalmTask.HTTP.get(
            "https://jsonplaceholder.typicode.com/posts/1",
            # Headers in HTTP variables are bugged:
            # https://jira.nutanix.com/browse/CALM-13724
            # headers={"Content-Type": "application/json"},
            content_type="application/json",
            verify=True,
            status_mapping={200: True},
            response_paths={"var31": "$.title"},
        ),
        label="var31_label",
        description="var31 description",
    )
    var32 = CalmVariable.WithOptions.FromTask.Array.int(
        CalmTask.Exec.escript(script="print '0,1'"),
        label="var32_label",
        validate_regex=True,
        description="var32 description",
    )
    var33 = CalmVariable.WithOptions.FromTask.Array.date(
        CalmTask.Exec.escript(script="print '30/02/2019,31/06/2019'"),
        label="var33_label",
        validate_regex=True,
        description="var33 description",
    )
    var34 = CalmVariable.WithOptions.FromTask.Array.time(
        CalmTask.Exec.escript(script="print '22:35:00,10:35:00'"),
        label="var28_label",
        validate_regex=True,
        description="var34 description",
    )
    var35 = CalmVariable.WithOptions.FromTask.Array.datetime(
        CalmTask.Exec.escript(
            script="print '30/02/2019 - 22:35:00,31/06/2019 - 10:35:00'"
        ),
        label="var35_label",
        validate_regex=True,
        description="var35 description",
    )
    var36 = CalmVariable.WithOptions.FromTask.Array.multiline(
        CalmTask.Exec.escript(script="print 'var36=x\ny,a\nb'"),
        label="var36_label",
        description="var36 description",
    )

    @action
    def test_profile_action():
        var1 = CalmVariable.Simple(  # noqa
            "var1_val",
            label="var1_label",
            regex="^[a-zA-Z0-9_]+$",
            validate_regex=True,
            runtime=True,
        )
        var2 = CalmVariable.Simple.Secret(  # noqa
            "var2_val",
            label="var2_label",
            regex="^[a-zA-Z0-9_]+$",
            validate_regex=True,
            is_hidden=True,
            is_mandatory=True,
        )
        CalmTask.Exec.ssh(
            name="Task5", filename="scripts/sample_script.sh", target=ref(MySQLService)
        )
        PHPService.test_action(name="Task6")
        CalmTask.HTTP.get(
            "https://jsonplaceholder.typicode.com/posts/1",
            credential=DefaultCred,
            headers={"Content-Type": "application/json"},
            secret_headers={"secret_header": "secret"},
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
        with parallel():
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
                filename="scripts/sample_script.sh",
                name="Test Setvar SSH",
                variables=["var2"],
                target=ref(MySQLService),
            )
        CalmTask.Scaling.scale_out(1, target=ref(LampDeployment), name="Scale out Lamp")
        CalmTask.Delay(delay_seconds=60, target=ref(MySQLService), name="Delay")
        CalmTask.Scaling.scale_in(1, target=LampDeployment, name="Scale in Lamp")


class ExistingVMBlueprint(Blueprint):
    """Existing VM example"""

    credentials = [DefaultCred]
    services = [MySQLService, PHPService]
    packages = [MySQLPackage, PHPPackage]
    substrates = [ExistingVM]
    profiles = [DefaultProfile]


def test_json():
    """Test the generated json for a single VM
    against known output"""
    import os

    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "test_existing_vm_bp.json")

    generated_json = ExistingVMBlueprint.json_dumps(pprint=True)

    known_json = open(file_path).read()
    assert generated_json == known_json


def main():
    print(ExistingVMBlueprint.json_dumps(pprint=True), end="")


if __name__ == "__main__":
    main()
