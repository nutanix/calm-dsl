import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator

from .profile import profile
from .deployment import deployment
from .substrate import substrate
from .service import service
from .package import package
from .ref import ref
from .action import action as Action
from .blueprint import blueprint
from .variable import VariableType as Variable
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# Simple Blueprint


class VmBlueprintType(EntityType):
    __schema_name__ = "VmBlueprint"
    __openapi_type__ = "app_vm_blueprint"
    __has_dag_target__ = False

    def get_task_target(cls):
        return

    def compile(cls):

        # Create blueprint object

        # Extracting Vm Profiles
        vm_profiles = cls.profiles

        # create blueprint credentials
        bp_credentials = cls.credentials

        bp_name = getattr(cls, "name", None) or cls.__name__
        bp_description = getattr(cls, "description", None) or cls.__doc__

        is_single_vm_bp = True
        if len(vm_profiles) == 0:
            LOG.error("No vm profile provided for blueprint")
            sys.exit(-1)

        elif len(vm_profiles) > 1:
            is_single_vm_bp = False

        bp_services = []
        bp_packages = []
        bp_substrates = []
        bp_profiles = []

        # Extracting blueprint entities
        for vp in vm_profiles:
            vp_data = vp.get_bp_classes()
            bp_services.append(vp_data["service"])
            bp_packages.append(vp_data["package"])
            bp_substrates.append(vp_data["substrate"])
            bp_profiles.append(vp_data["profile"])

        bp_obj = blueprint(
            name=bp_name,
            packages=bp_packages,
            services=bp_services,
            substrates=bp_substrates,
            credentials=bp_credentials,
            profiles=bp_profiles,
        )

        return bp_obj.compile()


class VmBlueprintValidator(PropertyValidator, openapi_type="app_vm_blueprint"):
    __default__ = None
    __kind__ = VmBlueprintType


def vm_blueprint(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return VmBlueprintType(name, bases, kwargs)


VmBlueprint = vm_blueprint()
