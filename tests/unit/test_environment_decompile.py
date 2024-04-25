import os
import json
import shutil
from calm.dsl.builtins.models.environment import EnvironmentType
from calm.dsl.builtins import read_local_file
from calm.dsl.decompile.file_handler import init_environment_dir, get_environment_dir
from calm.dsl.decompile.environments import render_environment_template
from black import format_str, FileMode

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
NTNX_LOCAL_AZ = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]


def test_environment_decompile():
    _, _, _, scripts_dir = init_environment_dir("./tests/test_environment_decompile")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "./jsons/environment.json")
    environment_dict = json.loads(open(file_path).read())

    environment_dict["status"]["resources"]["infra_inclusion_list"][0][
        "account_reference"
    ]["uuid"] = NTNX_LOCAL_AZ["UUID"]
    environment_dict["status"]["resources"]["infra_inclusion_list"][0][
        "account_reference"
    ]["name"] = NTNX_LOCAL_AZ["NAME"]

    environment_dict["status"]["resources"]["infra_inclusion_list"][0][
        "subnet_references"
    ][0]["name"] = NTNX_LOCAL_AZ["SUBNETS"][0]["NAME"]

    environment_dict["status"]["resources"]["infra_inclusion_list"][0][
        "subnet_references"
    ][0]["uuid"] = NTNX_LOCAL_AZ["SUBNETS"][0]["UUID"]

    environment_dict["status"]["resources"]["infra_inclusion_list"][0][
        "default_subnet_reference"
    ]["uuid"] = NTNX_LOCAL_AZ["SUBNETS"][0]["UUID"]

    environment_dict["status"]["resources"]["infra_inclusion_list"][0][
        "cluster_references"
    ][0]["uuid"] = NTNX_LOCAL_AZ["SUBNETS"][0]["CLUSTER_UUID"]

    environment_dict["status"]["resources"]["infra_inclusion_list"][0][
        "cluster_references"
    ][0]["name"] = NTNX_LOCAL_AZ["SUBNETS"][0]["CLUSTER"]

    environment_dict["status"]["resources"]["substrate_definition_list"][0][
        "create_spec"
    ]["cluster_reference"]["uuid"] = NTNX_LOCAL_AZ["SUBNETS"][0]["CLUSTER_UUID"]

    environment_dict["status"]["resources"]["substrate_definition_list"][0][
        "create_spec"
    ]["cluster_reference"]["name"] = NTNX_LOCAL_AZ["SUBNETS"][0]["CLUSTER"]

    cls = EnvironmentType.decompile(environment_dict["status"]["resources"])

    assert str(cls.providers[0].account_reference) == NTNX_LOCAL_AZ["NAME"]
    assert str(cls.substrates) == "[Untitled]"
    assert (
        str(cls.providers[0].default_subnet_reference)
        == NTNX_LOCAL_AZ["SUBNETS"][0]["NAME"]
    )
    assert (
        str(cls.providers[0].cluster_reference_list[0])
        == NTNX_LOCAL_AZ["SUBNETS"][0]["CLUSTER"]
    )

    shutil.rmtree(scripts_dir)
