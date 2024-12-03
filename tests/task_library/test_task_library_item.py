"""
Create task library item
"""

import json
from distutils.version import LooseVersion as LV
from calm.dsl.store.version import Version
from calm.dsl.builtins import CalmTask

Install_IIS = CalmTask.Exec.powershell(
    name="Install IIS", filename="scripts/Install_IIS.ps1"
)


def test_json():
    """Test the generated json
    against known output"""
    import os

    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "test_task_library.json")

    generated_json = Install_IIS.json_dumps(pprint=True)

    known_json = open(file_path).read()

    known_json = json.loads(known_json)
    generated_json = json.loads(generated_json)

    CALM_VERSION = Version.get_version("Calm")
    if LV(CALM_VERSION) < LV("3.9.0"):
        if "status_map_list" in known_json:
            known_json.pop("status_map_list")

    assert sorted(known_json.items()) == sorted(generated_json.items())


def main():
    print(Install_IIS.json_dumps(pprint=True), end="")


if __name__ == "__main__":
    main()
