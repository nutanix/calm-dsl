import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator

from .ref import ref
from .action import action as Action
from .blueprint import blueprint
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# Simple Blueprint


class VmBlueprintType(EntityType):
    __schema_name__ = "VmBlueprint"
    __openapi_type__ = "app_vm_blueprint"
    __has_dag_target__ = False

    def get_task_target(cls):
        return

    def make_bp_obj(cls):
        """returns blueprint object"""

        # Extracting Vm Profiles
        vm_profiles = getattr(cls, "profiles", [])

        # create blueprint credentials
        bp_credentials = cls.credentials

        bp_name = getattr(cls, "name", None) or cls.__name__
        if not vm_profiles:
            LOG.error("No vm profile provided for blueprint")
            sys.exit(-1)

        bp_services = []
        bp_packages = []
        bp_substrates = []
        bp_profiles = []

        # Extracting blueprint entities

        # Extracting service, as it should be same across profiles
        vp_data = vm_profiles[0].get_bp_classes()
        bp_svc = vp_data["service"]
        bp_services = [bp_svc]

        for vp in vm_profiles:
            vp_data = vp.get_bp_classes()

            pkg = vp_data["package"]
            pkg.services = [ref(bp_svc)]

            subt = vp_data["substrate"]

            pfl = vp_data["profile"]

            # Set service as reference to profile actions
            for k, v in pfl.__dict__.items():
                if isinstance(v, Action):
                    v.task_target = ref(bp_svc)

            bp_packages.append(pkg)
            bp_substrates.append(subt)
            bp_profiles.append(pfl)

        bp_obj = blueprint(
            name=bp_name,
            packages=bp_packages,
            services=bp_services,
            substrates=bp_substrates,
            credentials=bp_credentials,
            profiles=bp_profiles,
        )

        return bp_obj


class VmBlueprintValidator(PropertyValidator, openapi_type="app_vm_blueprint"):
    __default__ = None
    __kind__ = VmBlueprintType


def vm_blueprint(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return VmBlueprintType(name, bases, kwargs)


VmBlueprint = vm_blueprint()
