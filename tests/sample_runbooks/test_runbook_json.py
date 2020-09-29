"""
Test for testing runbook generated json against known json
"""
import os
from calm.dsl.runbooks import runbook_json

from .decision_task import DslDecisionRunbook
from .existing_endpoint import DslExistingEndpoint
from .parallel import DslParallelRunbook
from .runbook_variables import DslRunbookWithVariables
from .simple_runbook import DslSimpleRunbook
from .while_loop import DslWhileLoopRunbook


def _test_runbook_json(Runbook, json_file):
    """
    Test the generated json for a runbook agains known output
    """

    print("JSON compilation test for {}".format(Runbook.action_name))
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, json_file)

    generated_json = runbook_json(Runbook)
    known_json = open(file_path).read()

    assert generated_json == known_json
    print("JSON compilation successful for {}".format(Runbook.action_name))


def test_runbooks():
    runbooks = {
        "test_decision_task.json": DslDecisionRunbook,
        "test_existing_endpoint.json": DslExistingEndpoint,
        "test_parallel.json": DslParallelRunbook,
        "test_runbook_variables.json": DslRunbookWithVariables,
        "test_simple_runbook.json": DslSimpleRunbook,
        "test_while_loop.json": DslWhileLoopRunbook,
    }

    for json_file, runbook in runbooks.items():
        _test_runbook_json(runbook, json_file)


if __name__ == "__main__":
    test_runbooks()
