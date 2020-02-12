"""
Calm Runbook for objects bucket create
"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmVariable


@runbook
def DslBucketCreate():
    "Bucket create in objects"
    BUCKET_NAME = CalmVariable.Simple.string("", runtime=True)  # noqa
    CalmTask.SetVariable.escript(
        filename="scripts/objects_create_user_pass.py",
        variables=["UUID"]
    )
    CalmTask.Exec.escript(
        script="print '@@{UUID}@@'"
    )


def main():
    print(DslBucketCreate.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
