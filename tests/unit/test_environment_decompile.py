import os
import json
import shutil
from calm.dsl.builtins.models.environment import EnvironmentType
from calm.dsl.decompile.file_handler import init_environment_dir, get_environment_dir
from calm.dsl.decompile.environments import render_environment_template
from black import format_str, FileMode


def test_environment_decompile():
    _, _, _, scripts_dir = init_environment_dir("./tests/test_environment_decompile")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "./jsons/environment.json")
    environment_dict = json.loads(open(file_path).read())
    cls = EnvironmentType.decompile(environment_dict["status"]["resources"])
    data = render_environment_template(cls)
    data = format_str(data, mode=FileMode())
    assert "substrates = [Untitled]" in data, "expected substrate to be decompiled"
    assert (
        'account=Ref.Account("NTNX_LOCAL_AZ"),' in data
    ), "expected provider account to be decompiled"
    shutil.rmtree(scripts_dir)
