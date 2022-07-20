"""
Calm Runbook Sample for set variable task
"""
import os
import pytest
import json
from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.builtins.models.utils import read_local_file
from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint, basic_cred
from calm.dsl.store import Version
from distutils.version import LooseVersion as LV

from tests.cli.runtime_helpers.ahv.editable_params import DSL_CONFIG

# calm_version
CALM_VERSION = Version.get_version("Calm")
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))


@runbook
def DslSetVariableTaskUsingTunnel(endpoints=[], default=False):
    "Runbook example with Set Variable Tasks"

    Task.SetVariable.escript(
        name="tunnel_set_var",
        filename="scripts/escript_file",
        variables=["var1"],
        tunnel=Ref.Tunnel(name="NewNetworkGroupTunnel2"),
    )
    Task.Exec.escript(
        name="tunnel_exec",
        filename="scripts/escript_file",
        tunnel=Ref.Tunnel(name="NewNetworkGroupTunnel2"),
    )
    Task.Exec.escript(name="check set variable", filename="scripts/escript_check")


def _test_compare_compile_result(Runbook, json_file):
    """compares the runbook compilation and known output"""

    print("JSON compilation test for {}".format(Runbook.action_name))
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, json_file)

    generated_json = runbook_json(Runbook)
    known_json = open(file_path).read()

    assert generated_json == known_json
    print("JSON compilation successful for {}".format(Runbook.action_name))


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.5.0") or not DSL_CONFIG.get("IS_VPC_ENABLED", False),
    reason="Tunnel reference in Escript is for v3.5.0+",
)
def test_escript_with_tunnel_runbook_json():
    _test_compare_compile_result(
        DslSetVariableTaskUsingTunnel, "escript_with_tunnel_runbook.json"
    )


def main():
    print(runbook_json(DslSetVariableTaskUsingTunnel))


if __name__ == "__main__":
    main()
