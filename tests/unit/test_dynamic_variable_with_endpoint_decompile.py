import os
import json
import shutil
from calm.dsl.builtins import VariableType
from calm.dsl.decompile.file_handler import init_bp_dir
from calm.dsl.decompile.variable import render_variable_template


def test_dynamic_variable_with_endpoint_decompile():
    _, _, _, scripts_dir = init_bp_dir("./tests/test_dynamic_variable_with_endpoint")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "./jsons/dynamic_variable_with_endpoint.json")
    var_dict = json.loads(open(file_path).read())
    endpoints = []
    ep_list = []
    cls = VariableType.decompile(var_dict)
    assert "target_endpoint=ref(windows_endpoint)" in render_variable_template(
        cls, "runbook", endpoints=endpoints, ep_list=ep_list
    ), "expected endpoint windows_endpoint to be decompiled in task"
    assert "windows_endpoint" in ep_list, "endpoint name should be added in ep_list"
    assert (
        'windows_endpoint=Endpoint.use_existing("windows_endpoint")' in endpoints
    ), "rendered enpoint should be added in endpoints"
    shutil.rmtree(scripts_dir)
