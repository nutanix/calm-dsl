import uuid

from .action import ActionType, Action
from .validator import PropertyValidator

# RunbookService


class RunbookServiceType(ActionType):
    __schema_name__ = "RunbookService"
    __openapi_type__ = "runbook_service"

    def compile(cls):
        cdict = super().compile()
        if (cdict.get("default_target_reference", None) or None) is None:
            cdict.pop("default_target_reference", None)
        return cdict


class RunbookServiceValidator(PropertyValidator, openapi_type="runbook_service"):
    __default__ = None
    __kind__ = RunbookServiceType


def runbook_service(**kwargs):
    name = getattr(RunbookServiceType, "__schema_name__")
    bases = (Action,)
    return RunbookServiceType(name, bases, kwargs)


RunbookService = runbook_service()


def _runbook_service_create(**kwargs):
    name = str(uuid.uuid4())[:8] + "_" + getattr(RunbookServiceType, "__schema_name__")
    name = kwargs.pop("name", kwargs.get("__name__", name))
    bases = (RunbookService,)
    return RunbookServiceType(name, bases, kwargs)
