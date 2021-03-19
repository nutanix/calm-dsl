import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)

# Profile


class ProfileType(EntityType):
    __schema_name__ = "Profile"
    __openapi_type__ = "app_profile"

    def get_task_target(cls):
        return

    @classmethod
    def pre_decompile(mcls, cdict, context, prefix=""):
        cdict = super().pre_decompile(cdict, context, prefix=prefix)

        if "__name__" in cdict:
            cdict["__name__"] = "{}{}".format(prefix, cdict["__name__"])

        return cdict

    def compile(cls):
        cdict = super().compile()
        # description attribute in profile gives bp launch error: https://jira.nutanix.com/browse/CALM-19380
        cdict.pop("description", None)

        environments = cdict.pop("environment_reference_list", [])
        if len(environments) > 1:
            LOG.error("Multiple environments are not allowed in a profile.")
            sys.exit(-1)

        # Compile env first
        environments = [_e.get_dict() for _e in environments]
        environments = [_e["uuid"] for _e in environments]

        if environments:
            cdict["environment_reference_list"] = environments

        return cdict


class ProfileValidator(PropertyValidator, openapi_type="app_profile"):
    __default__ = None
    __kind__ = ProfileType


def profile(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return ProfileType(name, bases, kwargs)


Profile = profile()
