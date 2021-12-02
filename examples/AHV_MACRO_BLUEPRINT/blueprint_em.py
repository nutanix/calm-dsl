"""
This blueprint uses macro in nic and disk
"""

import os  # no_qa
import json

from calm.dsl.builtins import *  # no_qa
from examples.AHV_MACRO_BLUEPRINT.sample_runbook import DslSetVariableTask


# Secret Variables
CRED_USERNAME = read_local_file("cred_username")
CRED_PASSWORD = read_local_file("cred_password")
DNS_SERVER = read_local_file(".tests/dns_server")
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
TEST_PC_IP = DSL_CONFIG["EXISTING_MACHINE"]["IP_1"]


class Service1(Service):
    """Sample Service"""

    # disk image uuid to be used in disk image
    Custom_disk_uuid = CalmVariable.Simple.string(
        "e7b96d85-f41b-40a1-bd23-310b7de14eb1"
    )

    # For profile, actions task_target_mapping is compulsory
    http_task_action2 = get_runbook_action(DslSetVariableTask)


class Package1(Package):
    """Sample package"""

    services = [ref(Service1)]


class ExistingVM(Substrate):
    """CentOS VM"""

    provider_type = "EXISTING_VM"
    provider_spec = provider_spec({"address": TEST_PC_IP})
    readiness_probe = {
        "disabled": False,
        "delay_secs": "0",
        "connection_type": "SSH",
        "connection_port": 22,
    }

    @action
    def __pre_create__():
        CalmTask.Exec.escript(name="Pre Create Task", script="print 'Hello!'")


class MacroBlueprintDeployment(Deployment):
    """Sample Deployment"""

    packages = [ref(Package1)]
    substrate = ref(ExistingVM)


class MacroBlueprintProfile(Profile):
    """Sample Profile"""

    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)
    deployments = [MacroBlueprintDeployment]

    # For profile, actions task_target_mapping is compulsory
    http_task_action = get_runbook_action(
        DslSetVariableTask,
        task_target_mapping={
            "Task1": ref(Service1),
            "Task2": ref(Service1),
            "Task3": ref(Service1),
        },
    )

    @action
    def test_profile_action():
        """Sample description for a profile action"""
        CalmTask.Exec.ssh(name="Task5", script='echo "Hello"', target=ref(Service1))
        Service1.http_task_action2()


class MacroBlueprintEM(Blueprint):
    """Blueprint using macro in disk and nics"""

    services = [Service1]
    packages = [Package1]
    substrates = [ExistingVM]
    profiles = [MacroBlueprintProfile]
    credentials = [basic_cred(CRED_USERNAME, CRED_PASSWORD, default=True)]
