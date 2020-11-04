"""
Create task library item
"""

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
    assert generated_json == known_json


def main():
    print(Install_IIS.json_dumps(pprint=True), end="")


if __name__ == "__main__":
    main()
