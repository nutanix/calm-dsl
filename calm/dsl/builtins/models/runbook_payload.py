from .entity import EntityType, Entity
from .validator import PropertyValidator
from .runbook_service import RunbookServiceType


# Runbook Payload


class RunbookPayloadType(EntityType):
    __schema_name__ = "RunbookPayload"
    __openapi_type__ = "runbook_payload"


class RunbookPayloadValidator(
    PropertyValidator, openapi_type="runbook_payload"
):
    __default__ = None
    __kind__ = RunbookPayloadType


def _runbook_payload(**kwargs):
    name = getattr(RunbookPayloadType, "__schema_name__")
    bases = (Entity,)
    return RunbookPayloadType(name, bases, kwargs)


RunbookPayload = _runbook_payload()


def create_runbook_payload(UserRunbook):

    err = {"error": "", "code": -1}

    if UserRunbook is None:
        err["error"] = "Given runbook is empty."
        return None, err

    if not isinstance(UserRunbook, RunbookServiceType):
        err["error"] = "Given runbook is not of type Runbook"
        return None, err

    spec = {
        "name": UserRunbook.__name__,
        "description": UserRunbook.__doc__ or "",
        "resources": UserRunbook,
    }

    metadata = {"spec_version": 1, "kind": "action", "name": UserRunbook.__name__}

    UserRunbookPayload = _runbook_payload()
    UserRunbookPayload.metadata = metadata
    UserRunbookPayload.spec = spec

    return UserRunbookPayload, None
