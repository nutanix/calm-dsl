import uuid

from .task import meta
from .entity import EntityType, Entity
from .validator import PropertyValidator


class RunbookType(EntityType):
    __schema_name__ = "Runbook"
    __openapi_type__ = "app_runbook"

    def __call__(*args, **kwargs):
        pass


class RunbookValidator(PropertyValidator, openapi_type="app_runbook"):
    __default__ = None
    __kind__ = RunbookType


def _runbook(**kwargs):
    name = getattr(RunbookType, "__schema_name__")
    bases = (Entity,)
    return RunbookType(name, bases, kwargs)


Runbook = _runbook()


def runbook_create(**kwargs):

    # This follows UI naming convention for runbooks
    name = str(uuid.uuid4())[:8] + "_" + getattr(RunbookType, "__schema_name__")
    name = kwargs.get("name", kwargs.get("__name__", name))
    bases = (Runbook,)
    return RunbookType(name, bases, kwargs)


def generate_runbook(**kwargs):

    tasks = kwargs.get("tasks")

    category = kwargs.pop("category", None)
    substrate_ips = kwargs.pop("substrate_ips", None)
    if category is not None and substrate_ips is not None:
        raise ValueError(
            "Only one of category or substrate_ips is allowed at runbook level "
            + kwargs.get("name", "")
        )
    if category is not None:
        kwargs["target_type"] = "category"
        kwargs["target_value"] = category
    if substrate_ips is not None:
        kwargs["target_type"] = "substrate_ips"
        kwargs["target_value"] = substrate_ips

    meta_task = meta(
        name=str(uuid.uuid4())[:8] + "_meta",
        child_tasks=tasks,
        edges=[],
    )
    runbook = runbook_create(**kwargs)
    runbook.main_task_local_reference = meta_task.get_ref()
    runbook.tasks = [meta_task] + tasks
    return runbook
