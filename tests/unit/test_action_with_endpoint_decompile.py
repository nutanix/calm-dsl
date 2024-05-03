import os
import json
import shutil
from calm.dsl.builtins import ActionType
from calm.dsl.decompile.file_handler import init_bp_dir, get_bp_dir
from calm.dsl.decompile.action import render_action_template


def test_action_with_endpoint_decompile():
    _, _, _, scripts_dir = init_bp_dir("./tests/test_action_with_endpoint")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "./jsons/action_with_endpoint.json")
    bp_dict = json.loads(open(file_path).read())
    cls = ActionType.decompile(bp_dict)
    assert "target_endpoint=ref(ep2)" in render_action_template(
        cls
    ), "expected endpoint ep2 to be decompiled in task"
    shutil.rmtree(scripts_dir)
