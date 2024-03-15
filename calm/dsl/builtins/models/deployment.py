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

    def get_service_ref(cls):
        """get service class reference from deployment"""

        package_ref = getattr(cls, "packages")
        package_cls = []
        for package in package_ref:
            package_cls.append(package.__self__)
        if package_cls:
            # Target for package is service, retrieving service ref for a package
            return package_cls[0].get_task_target()
        return None


class DeploymentValidator(PropertyValidator, openapi_type="app_blueprint_deployment"):
    __default__ = None
    __kind__ = DeploymentType


def deployment(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return DeploymentType(name, bases, kwargs)


Deployment = deployment()
