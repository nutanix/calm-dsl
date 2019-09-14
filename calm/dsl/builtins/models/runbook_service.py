from .action import ActionType, Action
from .validator import PropertyValidator

# RunbookService


class RunbookServiceType(ActionType):
    __schema_name__ = "RunbookService"
    __openapi_type__ = "runbook_service"


class RunbookServiceValidator(PropertyValidator, openapi_type="runbook_service"):
    __default__ = None
    __kind__ = RunbookServiceType


def runbook_service(**kwargs):
    name = getattr(RunbookServiceType, "__schema_name__")
    bases = (Action,)
    return RunbookServiceType(name, bases, kwargs)


RunbookService = runbook_service()
