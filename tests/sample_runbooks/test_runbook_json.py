"""
Test for testing runbook generated json against known json
"""
import os
import pytest

from distutils.version import LooseVersion as LV
from calm.dsl.store import Version
from calm.dsl.runbooks import runbook_json

from .decision_task import DslDecisionRunbook
from .existing_endpoint import DslExistingEndpoint
from .parallel import DslParallelRunbook
from .runbook_variables import DslRunbookWithVariables
from .simple_runbook import DslSimpleRunbook
from .while_loop import DslWhileLoopRunbook

# calm_version
CALM_VERSION = Version.get_version("Calm")


@pytest.mark.parametrize(
    "json_file,Runbook",
    [
        ("test_decision_task.json", DslDecisionRunbook),
        ("test_existing_endpoint.json", DslExistingEndpoint),
        ("test_parallel.json", DslParallelRunbook),
        ("test_runbook_variables.json", DslRunbookWithVariables),
        ("test_simple_runbook.json", DslSimpleRunbook),
        ("test_while_loop.json", DslWhileLoopRunbook),
    ],
)
def test_runbook_json(Runbook, json_file):
    """
    Test the generated json for a runbook agains known output
    """

    _test_compare_compile_result(Runbook, json_file)


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.5.0"), reason="Inherit Task Feat is for v3.5.0"
)
def test_runbook_json_inherit_task():
    """
    Test the generated json for a runbook having inherit task against known output
    """

    from .inherit_target_runbook import DslInheritTargetRunbook

    Runbook = DslInheritTargetRunbook
    json_file = "test_inherit_target_runbook.json"

    _test_compare_compile_result(Runbook, json_file)


def _test_compare_compile_result(Runbook, json_file):
    """compares the runbook compilation and known output"""

    print("JSON compilation test for {}".format(Runbook.action_name))
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, json_file)

    generated_json = runbook_json(Runbook)
    known_json = open(file_path).read()

    assert generated_json == known_json
    print("JSON compilation successful for {}".format(Runbook.action_name))
