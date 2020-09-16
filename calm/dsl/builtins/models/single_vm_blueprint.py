import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator

from .profile import profile
from .deployment import deployment
from .provider_spec import provider_spec as get_provider_spec
from .substrate import substrate
from .service import service
from .package import package
from .ref import ref
from .action import action as Action
from .blueprint import blueprint
from .variable import VariableType
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# Simple Blueprint


class SingleVmBlueprintType(EntityType):
    __schema_name__ = "SingleVmBlueprint"
    __openapi_type__ = "app_single_vm_blueprint"
    __has_dag_target__ = False

    def make_bp_obj(cls):

        bp_name = getattr(cls, "name", None) or cls.__name__

        # create blueprint credentials
        bp_credentials = cls.credentials

        # create blueprint service
        bp_service = service(name=bp_name + "Service")

        # create blueprint package
        bp_pkg = package(name=bp_name + "Package", services=[ref(bp_service)])

        # create blueprint substrate
        bp_sub = substrate(
            name=bp_name + "Substrate",
            provider_type=cls.provider_type,
            provider_spec=cls.provider_spec,
            readiness_probe=cls.readiness_probe,
            os_type=cls.os_type,
        )

        # create blueprint deployment
        bp_dep = deployment(
            name=bp_name + "Deployment",
            min_replicas=cls.min_replicas,
            max_replicas=cls.max_replicas,
            packages=[ref(bp_pkg)],
            substrate=ref(bp_sub),
        )

        # create blueprint profile
        bp_profile = profile(name=bp_name + "Profile", deployments=[bp_dep])

        # Separate class action under packages, substrates and profile
        for k, v in cls.__dict__.items():
            if isinstance(v, (Action)):
                if k in ["__install__", "__uninstall__"]:
                    setattr(bp_pkg, k, v)

                elif k in ["__pre_create__", "__post_delete__"]:
                    setattr(bp_sub, k, v)

                else:
                    v.task_target = ref(bp_service)
                    setattr(bp_profile, k, v)

            elif isinstance(v, VariableType):
                setattr(bp_profile, k, v)

        bp_obj = blueprint(
            name=cls.__name__,
            services=[bp_service],
            packages=[bp_pkg],
            substrates=[bp_sub],
            credentials=bp_credentials,
            profiles=[bp_profile],
        )

        return bp_obj


class SingleBlueprintValidator(
    PropertyValidator, openapi_type="app_single_vm_blueprint"
):
    __default__ = None
    __kind__ = SingleVmBlueprintType


def single_vm_blueprint(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return SingleVmBlueprintType(name, bases, kwargs)


SingleVmBlueprint = single_vm_blueprint()
