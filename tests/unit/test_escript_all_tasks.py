import uuid
import os
import pytest

from calm.dsl.runbooks import *
from calm.dsl.runbooks import (
    RunbookTask as CalmTask,
)
from calm.dsl.builtins import CalmTask as CalmVarTask, Metadata


@runbook
def DslAllEscriptTasks(endpoints=[], default=False):
    "Runbook example with All Escript Type Tasks"

    with CalmTask.Decision.escript(
        name="escript_decision",
        filename=os.path.join("scripts", "escript_decision_true.py"),
    ) as d:
        if d.ok:
            CalmTask.Exec.escript(
                name="escript_exec", filename=os.path.join("scripts", "escript_exec.py")
            )
            CalmTask.SetVariable.escript(
                name="escript_setvar",
                filename=os.path.join("scripts", "escript_setvariable.py"),
                variables=["var1"],
            )
        else:
            CalmTask.Exec.escript(
                name="escript_exec_print", script='''print "Decision else part"'''
            )

    with CalmTask.Decision.escript.py2(
        name="escript2_decision",
        filename=os.path.join("scripts", "escript_decision_false.py"),
    ) as d:
        if d.ok:
            CalmTask.Exec.escript.py2(
                name="escript3_exec_print", script='''print "Decision if part"'''
            )
        else:
            CalmTask.Exec.escript.py2(
                name="escript2_exec",
                filename=os.path.join("scripts", "escript_exec.py"),
            )
            CalmTask.SetVariable.escript.py2(
                name="escript2_setvar",
                filename=os.path.join("scripts", "escript_setvariable.py"),
                variables=["var1"],
            )

    with CalmTask.Decision.escript.py3(
        name="escript3_decision",
        filename=os.path.join("scripts", "escript_decision_true.py"),
    ) as d:
        if d.ok:
            CalmTask.Exec.escript.py3(
                name="escript3_exec",
                filename=os.path.join("scripts", "escript_exec.py"),
            )
            CalmTask.SetVariable.escript.py3(
                name="escript3_setvar",
                filename=os.path.join("scripts", "escript_setvariable.py"),
                variables=["var1"],
            )
        else:
            CalmTask.Exec.escript.py3(
                name="escript3_exec_print", script="""print("Decision else part")"""
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
def test_all_escript_type_tasks():
    _test_compare_compile_result(DslAllEscriptTasks, "./jsons/escript_all_tasks.json")
