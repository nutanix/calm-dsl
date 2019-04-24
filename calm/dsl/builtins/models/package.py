from .entity import EntityType, Entity
from .validator import PropertyValidator

from .task import dag
from .action import _runbook_create

# Package


class PackageType(EntityType):
    __schema_name__ = "Package"
    __openapi_type__ = "app_package"

    def compile(cls):

        if not getattr(cls, "type") == "CUSTOM":
            cdict = super().compile()
            return cdict

        def make_empty_runbook():
            user_dag = dag()
            return _runbook_create(
                main_task_local_reference=user_dag.get_ref(), tasks=[user_dag]
            )

        install_runbook = (
            getattr(getattr(cls, "__install__", None), "runbook", None) or None
        )
        if install_runbook:
            delattr(cls, "__install__")
        else:
            install_runbook = make_empty_runbook()
        uninstall_runbook = (
            getattr(getattr(cls, "__uninstall__", None), "runbook", None) or None
        )
        if uninstall_runbook:
            delattr(cls, "__uninstall__")
        else:
            uninstall_runbook = make_empty_runbook()

        cdict = super().compile()

        cdict["options"]["install_runbook"] = install_runbook
        cdict["options"]["uninstall_runbook"] = uninstall_runbook

        # Delete additional dsl keys
        # TODO - pop items based on schema flag
        del cdict["install_tasks"]

        return cdict


class PackageValidator(PropertyValidator, openapi_type="app_package"):
    __default__ = None
    __kind__ = PackageType


def package(**kwargs):
    name = getattr(PackageType, "__schema_name__")
    bases = (Entity,)
    return PackageType(name, bases, kwargs)


Package = package()
