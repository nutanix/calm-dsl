"""
Calm DSL VM Operations Example

"""

from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint, ref


@runbook
def DslVMOperationsRunbook():
    "Runbook Service example"

    Task.VMPowerOff(
        name="VM Power Off Task", target=ref(Endpoint.use_existing("VMEndpoint"))
    )
    Task.VMPowerOn(
        name="VM Power On Task", target=ref(Endpoint.use_existing("VMEndpoint"))
    )
    Task.VMRestart(
        name="VM Restart Task", target=ref(Endpoint.use_existing("VMEndpoint"))
    )


def main():
    print(runbook_json(DslVMOperationsRunbook))


if __name__ == "__main__":
    main()
