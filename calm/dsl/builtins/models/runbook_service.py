from .action import EntityType, Entity
from .validator import PropertyValidator

# RunbookService


class RunbookServiceType(EntityType):
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
    name = kwargs.get("name", None)
    bases = (Entity,)
    return RunbookServiceType(name, bases, kwargs)


RunbookService = runbook_service()


def _runbook_service_create(**kwargs):
    name = kwargs.get("name", kwargs.get("__name__", None))
    bases = (RunbookService,)
    return RunbookServiceType(name, bases, kwargs)
