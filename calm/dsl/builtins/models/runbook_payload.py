from .entity import EntityType, Entity
from .validator import PropertyValidator
from .runbook import runbook


# Runbook Payload


class RunbookPayloadType(EntityType):
    __schema_name__ = "RunbookPayload"
    __openapi_type__ = "runbook_payload"


class RunbookPayloadValidator(PropertyValidator, openapi_type="runbook_payload"):
    __default__ = None
    __kind__ = RunbookPayloadType


def _runbook_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return RunbookPayloadType(name, bases, kwargs)


RunbookPayload = _runbook_payload()


def create_runbook_payload(UserRunbook):

    err = {"error": "", "code": -1}

    if UserRunbook is None:
        err["error"] = "Given runbook is empty."
        return None, err

    if not isinstance(UserRunbook, runbook):
        err["error"] = "Given runbook is not of type Runbook"
        return None, err

    spec = {
        "name": UserRunbook.action_name,
        "description": UserRunbook.action_description or "",
        "resources": UserRunbook.runbook,
    }

    metadata = {"spec_version": 1, "kind": "runbook", "name": UserRunbook.action_name}

    UserRunbookPayload = _runbook_payload()
    UserRunbookPayload.metadata = metadata
    UserRunbookPayload.spec = spec

    return UserRunbookPayload, None
