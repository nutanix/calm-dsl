from .entity import EntityType, Entity
from .validator import PropertyValidator

from .task import dag
from .action import runbook_create, _action_create, action


# Service


class ServiceType(EntityType):
    __schema_name__ = "Service"
    __openapi_type__ = "app_service"

    ALLOWED_SYSTEM_ACTIONS = {
        "__create__": "action_create",
        "__delete__": "action_delete",
        "__start__": "action_start",
        "__stop__": "action_stop",
        "__restart__": "action_restart",
        "__soft_delete__": "action_soft_delete",
    }

    def get_task_target(cls):
        return cls.get_ref()

    @classmethod
    def pre_decompile(mcls, cdict, context, prefix=""):
        cdict = super().pre_decompile(cdict, context, prefix=prefix)

        if "__name__" in cdict:
            cdict["__name__"] = "{}{}".format(prefix, cdict["__name__"])

        return cdict

    def compile(cls):

        cdict = super().compile()

        def make_empty_runbook(action_name):
            suffix = getattr(cls, "name", "") or cls.__name__
            user_dag = dag(
                name="DAG_Task_for_Service_{}_{}".format(suffix, action_name),
                target=cls.get_task_target(),
            )
            return runbook_create(
                name="Runbook_for_Service_{}_{}".format(suffix, action_name),
                main_task_local_reference=user_dag.get_ref(),
                tasks=[user_dag],
            )

        compulsory_actions = list(cls.ALLOWED_SYSTEM_ACTIONS.values())
        for action_obj in cdict["action_list"]:
            if action_obj.__name__ in compulsory_actions:
                compulsory_actions.remove(action_obj.__name__)

        for action_name in compulsory_actions:
            user_action = _action_create(
                **{
                    "name": action_name,
                    "description": "",
                    "critical": True,
                    "type": "system",
                    "runbook": make_empty_runbook(action_name),
                }
            )
            cdict["action_list"].append(user_action)

        return cdict


class ServiceValidator(PropertyValidator, openapi_type="app_service"):
    __default__ = None
    __kind__ = ServiceType


def service(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return ServiceType(name, bases, kwargs)


Service = service()


class BaseService(Service):
    @action
    def __create__():
        pass

    @action
    def __start__():
        pass

    @action
    def __stop__():
        pass

    @action
    def __delete__():
        pass

    @action
    def __restart__():
        pass

    @action
    def __soft_delete__():
        pass
