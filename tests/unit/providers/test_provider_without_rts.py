import json
import os
import pytest

from calm.dsl.cli.providers import compile_provider
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def _prepare_json_for_comparsion(generated_json):
    """
    This helper functions pops all the fields where UUIDs are dynamically
    generated & inserted during 'compile' operation

    Args:
        generated_json (dict): Dictionary to do the edits on
    """
    resources = generated_json["spec"]["resources"]
    auth_schema_list = resources["auth_schema_list"]
    variable_list = resources["variable_list"]
    endpoint_schema_list = resources.get("endpoint_schema", {}).get("variable_list", [])
    acc_var_list = (
        resources.get("test_account", {}).get("data", {}).get("variable_list", [])
    )
    for var in auth_schema_list + variable_list + endpoint_schema_list + acc_var_list:
        var.pop("uuid", None)

    resources.get("test_account", {}).pop("uuid", None)

    action_list = resources.get("action_list")
    if action_list:
        action, runbook = action_list[0], action_list[0]["runbook"]
        action.pop("uuid", None)
        runbook.pop("uuid", None)
        runbook["main_task_local_reference"].pop("uuid", None)
        tasks = runbook["task_definition_list"]
        for task in tasks:
            task.pop("uuid", None)
            if task["type"] == "DAG":
                for t in task["child_tasks_local_reference_list"]:
                    t.pop("uuid", None)

    generated_json["metadata"].pop("uuid", None)


def _test_compare_compile_result(provider_file, expected_output_file):
    """
    Compares the runbook compilation and known output

    Args:
        provider_file (string): Path to the DSL file that needs to be compiled
        expected_output_file (string): Path to the JSON expected out of compile operation
    """

    LOG.info("JSON compilation test for {}".format(provider_file))

    dir_path = os.path.dirname(os.path.realpath(__file__))
    generated_json = compile_provider(os.path.join(dir_path, provider_file))
    _prepare_json_for_comparsion(generated_json)

    known_json = open(os.path.join(dir_path, expected_output_file)).read()
    known_json = json.loads(known_json)

    assert generated_json == known_json
    LOG.info("JSON compilation successful for {}".format(provider_file))


# TODO: After all the development is done, update the JSONs
@pytest.mark.provider
@pytest.mark.parametrize(
    "provider_file, expected_json_file",
    [
        (
            "./dsl_files/provider_with_just_auth_schema.py",
            "./expected_jsons/provider_with_just_auth_schema.json",
        ),
        (
            "./dsl_files/provider_with_custom_ep_schema.py",
            "./expected_jsons/provider_with_custom_ep_schema.json",
        ),
        (
            "./dsl_files/provider_with_none_ep_schema.py",
            "./expected_jsons/provider_with_none_ep_schema.json",
        ),
        (
            "./dsl_files/provider_with_ntnx_ep_schema.py",
            "./expected_jsons/provider_with_ntnx_ep_schema.json",
        ),
        (
            "./dsl_files/provider_with_verify_action.py",
            "./expected_jsons/provider_with_verify_action.json",
        ),
        (
            "./dsl_files/provider_with_test_account.py",
            "./expected_jsons/provider_with_test_account.json",
        ),
        (
            "./dsl_files/provider_with_variables.py",
            "./expected_jsons/provider_with_variables.json",
        ),
    ],
)
def test_provider_compile_without_rts(provider_file, expected_json_file):
    _test_compare_compile_result(provider_file, expected_json_file)
