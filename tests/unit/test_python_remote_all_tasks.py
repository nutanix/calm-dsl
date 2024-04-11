import os
import pytest

from calm.dsl.runbooks import *
from calm.dsl.runbooks import RunbookTask as CalmTask, CalmEndpoint as Endpoint

Cred = basic_cred(username="username", password="password", name="endpoint_cred")
IPEndpoint = Endpoint.Linux.ip(["10.10.10.10"], cred=Cred, name="IP_endpoint")


@runbook
def DslAllPythonRemoteTasks(endpoints=[], default=False):
    "Runbook example with All python_remote Type Tasks"

    with CalmTask.Decision.python(
        name="python_decision",
        filename=os.path.join("scripts", "escript_decision_true.py"),
        target=IPEndpoint,
    ) as d:
        if d.ok:
            CalmTask.Exec.python(
                name="python_exec",
                filename=os.path.join("scripts", "escript_exec.py"),
                target=IPEndpoint,
            )
            CalmTask.SetVariable.python(
                name="python_setvar",
                filename=os.path.join("scripts", "escript_setvariable.py"),
                variables=["var1"],
                target=IPEndpoint,
            )
        else:
            CalmTask.Exec.python(
                name="python_exec_print",
                script='''print "Decision else part"''',
                target=IPEndpoint,
            )


def _test_compare_compile_result(Runbook, json_file):
    """compares the runbook compilation and known output"""

    print("JSON compilation test for {}".format(Runbook.action_name))
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, json_file)

    generated_json = runbook_json(Runbook)
    known_json = open(file_path).read()
    assert generated_json == known_json
    print("JSON compilation successful for {}".format(Runbook.action_name))


@pytest.mark.runbook
@pytest.mark.escript
def test_all_python_remote_type_tasks():
    _test_compare_compile_result(
        DslAllPythonRemoteTasks, "./jsons/python_remote_all_tasks.json"
    )
