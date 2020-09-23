from .entity import EntityType, Entity, EntityTypeBase
from .validator import PropertyValidator

from .task import dag
from .action import runbook_create, _action_create
from .runbook import RunbookType
from calm.dsl.log import get_logging_handle


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
            # No actions are allowed other than __install__ and __uninstall__
            cdict.pop("action_list", None)

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

    @classmethod
    def decompile(mcls, cdict, context=[]):

        cls = super().decompile(cdict, context=context)
        options = cls.options
        delattr(cls, "options")

        option_data = mcls.__validator_dict__["options"][0].decompile(options)

        package_type = getattr(cls, "type")
        if package_type == "CUSTOM" or package_type == "DEB":
            install_runbook = option_data["install_runbook"]
            uninstall_runbook = option_data["uninstall_runbook"]

            install_tasks = install_runbook["task_definition_list"]
            if len(install_tasks) > 1:
                cls.__install__ = _action_create(
                    **{
                        "name": "action_install",
                        "critical": True,
                        "type": "system",
                        "runbook": RunbookType.decompile(install_runbook),
                    }
                )

            uninstall_tasks = uninstall_runbook["task_definition_list"]
            if len(uninstall_tasks) > 1:
                cls.__uninstall__ = _action_create(
                    **{
                        "name": "action_uninstall",
                        "critical": True,
                        "type": "system",
                        "runbook": RunbookType.decompile(uninstall_runbook),
                    }
                )

        elif package_type == "SUBSTRATE_IMAGE":
            cdict = {
                "name": cls.__name__,
                "description": cls.__doc__,
                "options": option_data,
            }
            types = EntityTypeBase.get_entity_types()
            VmDiskPackageType = types.get("VmDiskPackage", None)
            if not VmDiskPackageType:
                raise ModuleNotFoundError("VmDiskPackage Module not found.")

            cls = VmDiskPackageType.decompile(cdict)
        return cls

    def get_task_target(cls):

        # Target for package actions is the service, keeping this consistent between UI and DSL.
        # Refer: https://jira.nutanix.com/browse/CALM-9182
        services = getattr(cls, "services", [])
        if services:
            return services[0]
        raise ValueError("package do not have any service referenced")


class PackageValidator(PropertyValidator, openapi_type="app_package"):
    __default__ = None
    __kind__ = PackageType


def package(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return PackageType(name, bases, kwargs)


Package = package()
