import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.store import Cache
from calm.dsl.log import get_logging_handle
from .helper import common as common_helper

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

        # Get project from metadata or context
        project_cache_data = common_helper.get_cur_context_project()
        project_name = project_cache_data["name"]

        environments = cdict.get("environment_reference_list", [])
        if len(environments) > 1:
            LOG.error("Multiple environments are not allowed in a profile.")
            sys.exit(-1)
        
        environments = [ _e["uuid"] for _e in environments]
        env_uuid = environments[0] if len(environments) > 0 else None

        if env_uuid:
            # ensure that the referenced environment is associated to the project this BP belongs to.
            env_cache_data = Cache.get_entity_data_using_uuid(
                entity_type="environment", uuid=env_uuid
            )
            env_project = env_cache_data.get("project")
            env_name = env_cache_data.get("name")
            if env_project and project_name != env_project:
                LOG.error(
                    "Environment '{}' referenced by profile '{}' belongs to project '{}'. Use an environment from"
                    " project '{}'".format(
                        env_name, cdict.get("name", ""), env_project, project_name
                    )
                )
                sys.exit(-1)

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
