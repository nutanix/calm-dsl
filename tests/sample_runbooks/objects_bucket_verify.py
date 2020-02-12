"""
Calm Runbook for objects bucket verify
"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmVariable


@runbook
def DslBucketVerify():
    "Bucket verify in objects"
    BUCKET_NAME = CalmVariable.Simple.string("", runtime=True)  # noqa
    CalmTask.Exec.escript(
        filename="/Users/sarat.kumar/Scripts/hackathon2020/objects_verify_user_pass.py"
    )


def main():
    print(DslBucketVerify.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
