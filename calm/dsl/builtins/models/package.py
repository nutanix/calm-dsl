from .entity import EntityType, Entity
from .validator import PropertyValidator

from .task import dag
from .action import runbook_create
from calm.dsl.tools import get_logging_handle


LOG = get_logging_handle(__name__)
# Package


class PackageType(EntityType):
    __schema_name__ = "Package"
    __openapi_type__ = "app_package"

    ALLOWED_SYSTEM_ACTIONS = {
        "__install__": "action_install",
        "__uninstall__": "action_uninstall",
    }

    def compile(cls):

        cdict = {}

        # As downloadable images have no type attribute
        # So just return it's compiled dict
        if getattr(cls, "__kind__") == "app_vm_disk_package":
            return super().compile()

        if getattr(cls, "type") == "K8S_IMAGE":
            cdict = super().compile()
            cdict["options"] = {}

        elif getattr(cls, "type") == "CUSTOM":

            def make_empty_runbook(action_name):
                user_dag = dag(
                    name="DAG_Task_for_Package_{}_{}".format(str(cls), action_name),
                    target=cls.get_task_target(),
                )
                return runbook_create(
                    name="Runbook_for_Package_{}_{}".format(str(cls), action_name),
                    main_task_local_reference=user_dag.get_ref(),
                    tasks=[user_dag],
                )

            install_runbook = (
                getattr(getattr(cls, "__install__", None), "runbook", None) or None
            )

            # delattr(cls, "__install__")
            if not install_runbook:
                install_runbook = make_empty_runbook("action_install")

            uninstall_runbook = (
                getattr(getattr(cls, "__uninstall__", None), "runbook", None) or None
            )

            # delattr(cls, "__uninstall__")
            if not uninstall_runbook:
                uninstall_runbook = make_empty_runbook("action_uninstall")

            cdict = super().compile()

            # Remove image_spec field created during compile step
            cdict.pop("image_spec", None)
            cdict["options"] = {
                "install_runbook": install_runbook,
                "uninstall_runbook": uninstall_runbook,
            }

        elif getattr(cls, "type") == "SUBSTRATE_IMAGE":
            cdict = super().compile()
            if cdict.get("options"):
                cdict["options"].pop("install_runbook", None)
                cdict["options"].pop("uninstall_runbook", None)
            cdict.pop("image_spec", None)
            return cdict

        else:
            ptype = getattr(cls, "type")
            LOG.debug(
                "Supported Package Types: ['SUBSTRATE_IMAGE', 'CUSTOM', 'K8S_IMAGE']"
            )
            raise Exception("Un-supported package type {}".format(ptype))

        return cdict

    def get_task_target(cls):

        # Target for package actions is the service, keeping this consistent between UI and DSL.
        # Refer: https://jira.nutanix.com/browse/CALM-9182
        services = getattr(cls, "services", [])
        if services:
            return services[0]


class PackageValidator(PropertyValidator, openapi_type="app_package"):
    __default__ = None
    __kind__ = PackageType


def package(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return PackageType(name, bases, kwargs)


Package = package()
