from .entity import EntityType, Entity
from .validator import PropertyValidator

from .profile import profile
from .deployment import deployment
from .substrate import substrate
from .service import service
from .package import package
from .ref import ref
from .action import action as Action
from .variable import VariableType as Variable
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# Simple Blueprint


class VmProfileType(EntityType):
    __schema_name__ = "VmProfile"
    __openapi_type__ = "app_vm_profile"
    __has_dag_target__ = False

    def get_task_target(cls):
        return

    def get_bp_classes(cls):

        profile_name = getattr(cls, "name", None) or cls.__name__

        bp_service = service(name=profile_name + "Service")

        # create blueprint package
        bp_pkg = package(name=profile_name + "Package", services=[ref(bp_service)])

        # create blueprint substrate
        bp_sub = substrate(
            name=profile_name + "Substrate",
            provider_type=cls.provider_type,
            provider_spec=cls.provider_spec,
            readiness_probe=cls.readiness_probe,
            os_type=cls.os_type,
        )

        # create blueprint deployment
        bp_dep = deployment(
            name=profile_name + "Deployment",
            min_replicas=cls.min_replicas,
            max_replicas=cls.max_replicas,
            packages=[ref(bp_pkg)],
            substrate=ref(bp_sub),
        )

        # create blueprint profile
        pfl_kwargs = {"name": profile_name, "deployments": [bp_dep]}

        environments = getattr(cls, "environments", None)
        if environments:
            pfl_kwargs["environments"] = environments

        bp_profile = profile(**pfl_kwargs)

        # Traverse over mro dict of class
        cls_data = cls.get_default_attrs()
        for klass in reversed(cls.mro()):
            cls_data = {**cls_data, **klass.__dict__}

        # Separate class action under packages, substrates and profile
        for k, v in cls_data.items():
            if isinstance(v, Action):
                if k in ["__install__", "__uninstall__"]:
                    setattr(bp_pkg, k, v)

                elif k in ["__pre_create__", "__post_delete__"]:
                    setattr(bp_sub, k, v)

                else:
                    setattr(bp_profile, k, v)

            elif isinstance(v, Variable):
                setattr(bp_profile, k, v)

        return {
            "service": bp_service,
            "package": bp_pkg,
            "substrate": bp_sub,
            "profile": bp_profile,
        }


class VmProfileValidator(PropertyValidator, openapi_type="app_vm_profile"):
    __default__ = None
    __kind__ = VmProfileType


def vm_profile(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return VmProfileType(name, bases, kwargs)


VmProfile = vm_profile()
