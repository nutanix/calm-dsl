import os
import json
import shutil
from calm.dsl.builtins.models.project import ProjectType
from calm.dsl.builtins import read_local_file
from calm.dsl.decompile.file_handler import init_project_dir, get_project_dir
from calm.dsl.decompile.projects import render_project_template
from black import format_str, FileMode

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
NTNX_LOCAL_AZ = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]


def test_project_decompile():
    _, _, _, scripts_dir = init_project_dir("./tests/test_project_decompile")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "./jsons/project.json")
    project_dict = json.loads(open(file_path).read())

    project_dict["status"]["resources"]["user_reference_list"][0]["name"] = DSL_CONFIG[
        "USERS"
    ][0]["NAME"]
    project_dict["status"]["resources"]["user_reference_list"][0]["uuid"] = DSL_CONFIG[
        "USERS"
    ][0]["UUID"]

    project_dict["status"]["resources"]["default_subnet_reference"][
        "uuid"
    ] = NTNX_LOCAL_AZ["SUBNETS"][0]["UUID"]
    project_dict["status"]["resources"]["subnet_reference_list"][0][
        "name"
    ] = NTNX_LOCAL_AZ["SUBNETS"][0]["NAME"]
    project_dict["status"]["resources"]["subnet_reference_list"][0][
        "uuid"
    ] = NTNX_LOCAL_AZ["SUBNETS"][0]["UUID"]

    project_dict["status"]["resources"]["account_reference_list"][0][
        "uuid"
    ] = NTNX_LOCAL_AZ["UUID"]
    project_dict["spec"]["resources"]["account_reference_list"][0][
        "uuid"
    ] = NTNX_LOCAL_AZ["UUID"]
    project_dict["metadata"]["uuid"] = DSL_CONFIG["PROJECTS"]["PROJECT1"]["UUID"]
    project_dict["metadata"]["project_reference"]["uuid"] = DSL_CONFIG["PROJECTS"][
        "PROJECT1"
    ]["UUID"]

    cls = ProjectType.decompile(project_dict)

    data = render_project_template(cls)

    assert cls.users[0]["name"] == DSL_CONFIG["USERS"][0]["NAME"]
    assert str(cls.providers[0].account_reference) == NTNX_LOCAL_AZ["NAME"]
    assert (
        str(cls.providers[0].subnet_reference_list[0])
        == NTNX_LOCAL_AZ["SUBNETS"][0]["NAME"]
    )

    shutil.rmtree(scripts_dir)
