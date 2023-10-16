import os
import json
import shutil
from calm.dsl.runbooks import RunbookType
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.decompile.file_handler import init_runbook_dir


def test_runbook_var_with_basic_creds():
    _, _, script_dir = init_runbook_dir(
        "./tests/test_runbook_http_var_with_basic_auth/"
    )
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "jsons/runbook_http_var.json")
    rb_dict = json.loads(open(file_path).read())
    rb_cls = RunbookType.decompile(rb_dict["status"]["resources"]["runbook"])
    credentials_list = []
    rendered_credential_list = []
    variables = []
    for variable in rb_cls.variables:
        variables.append(
            render_variable_template(
                variable,
                "",
                credentials_list=credentials_list,
                rendered_credential_list=rendered_credential_list,
            )
        )
    assert len(credentials_list) == 1, "Basic auth in variable was not decompiled"
    shutil.rmtree(script_dir)


if __name__ == "__main__":
    test_runbook_var_with_basic_creds()
