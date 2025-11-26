"""
Test for testing runbook generated json against known json
"""
import os
import pytest
import json
import uuid
from distutils.version import LooseVersion as LV

from distutils.version import LooseVersion as LV
from calm.dsl.store import Version
from calm.dsl.runbooks import runbook_json
from calm.dsl.db.table_config import GlobalVariableCache

from .decision_task import DslDecisionRunbook
from .existing_endpoint import DslExistingEndpoint
from .parallel import DslParallelRunbook
from .runbook_variables import DslRunbookWithVariables
from .simple_runbook import DslSimpleRunbook
from .while_loop import DslWhileLoopRunbook
from .execution_name_runbook import DslExecutionRunbook

from tests.helper.global_variables_helper import remove_global_variables_from_spec
from tests.helper.execution_name_helper import remove_execution_name_from_spec

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


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("4.3.0"), reason="execution name introduced in for v4.3.0"
)
def test_runbook_json_execution_name():
    """
    Test the generated json for a runbook having execution_name
    """
    Runbook = DslExecutionRunbook
    json_file = "test_runbook_with_execution_name.json"

    _test_compare_compile_result(Runbook, json_file)


@pytest.mark.global_variables
@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("4.3.0"), reason="Global variable is for v4.3.0"
)
def test_runbook_json_global_variable():
    """
    Test the generated json for a runbook having global variable
    """

    gv_uuid = str(uuid.uuid4())
    GlobalVariableCache.add_one_by_entity_dict(
        {
            "status": {"name": "GlobalVar", "state": "ACTIVE", "resources": {}},
            "metadata": {
                "uuid": gv_uuid,
            },
        }
    )

    from .runbook_with_global_variables import DslRunbookWithGlobalVariables

    Runbook = DslRunbookWithGlobalVariables
    json_file = "test_runbook_with_gv.json"

    _test_compare_compile_result(Runbook, json_file)

    GlobalVariableCache.delete_one(gv_uuid)


def _test_compare_compile_result(Runbook, json_file):
    """compares the runbook compilation and known output"""
    print("JSON compilation test for {}".format(Runbook.action_name))
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, json_file)

    generated_json = runbook_json(Runbook)
    known_json = open(file_path).read()

    known_json = json.loads(known_json)
    generated_json = json.loads(generated_json)

    CALM_VERSION = Version.get_version("Calm")
    if LV(CALM_VERSION) < LV("3.9.0"):
        for task in known_json["runbook"]["task_definition_list"]:
            if "status_map_list" in task:
                task.pop("status_map_list")
    if LV(CALM_VERSION) < LV("4.3.0"):
        remove_global_variables_from_spec(known_json)
        remove_execution_name_from_spec(known_json)

    known_json["runbook"].pop("output_variables", None)
    known_json["runbook"].pop("output_variable_list", None)
    generated_json["runbook"].pop("output_variables", None)
    generated_json["runbook"].pop("output_variable_list", None)

    if generated_json.get("global_variable_reference_list", []):
        for item in generated_json["global_variable_reference_list"]:
            item.pop("uuid", None)

    assert sorted(known_json.items()) == sorted(generated_json.items())
    print("JSON compilation successful for {}".format(Runbook.action_name))
