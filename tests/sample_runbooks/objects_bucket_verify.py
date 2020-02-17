"""
Calm Runbook for objects verify
"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask


@runbook
def DslObjectsVerify():
    "Verify objects"
    CalmTask.Exec.escript(
        script="print 'Successfully connected to Objects server'"
    )


def main():
    print(DslObjectsVerify.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
