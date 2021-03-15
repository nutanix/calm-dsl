import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


# Deployment


class DeploymentType(EntityType):
    __schema_name__ = "Deployment"
    __openapi_type__ = "app_blueprint_deployment"

    def get_task_target(cls):
        return cls.get_ref()

    @classmethod
    def pre_decompile(mcls, cdict, context, prefix=""):
        cdict = super().pre_decompile(cdict, context, prefix=prefix)

        if "__name__" in cdict:
            cdict["__name__"] = "{}{}".format(prefix, cdict["__name__"])

        return cdict

    @classmethod
    def decompile(mcls, cdict, context=[], prefix=""):

        if cdict["type"] == "K8S_DEPLOYMENT":
            LOG.error("Decompilation support for pod deployments is not available.")
            sys.exit(-1)

        return super().decompile(cdict, context=context, prefix=prefix)


class DeploymentValidator(PropertyValidator, openapi_type="app_blueprint_deployment"):
    __default__ = None
    __kind__ = DeploymentType


def deployment(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return DeploymentType(name, bases, kwargs)


Deployment = deployment()
