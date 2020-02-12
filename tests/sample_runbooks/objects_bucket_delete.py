"""
Calm Runbook for objects bucket delete
"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmVariable


@runbook
def DslBucketDelete():
    "Bucket create in objects"
    BUCKET_NAME = CalmVariable.Simple.string("", runtime=True)  # noqa
    CalmTask.Exec.escript(
        filename="scripts/objects_delete_user_pass.py"
    )


def main():
    print(DslBucketDelete.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
