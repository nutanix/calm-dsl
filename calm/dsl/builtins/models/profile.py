import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .metadata_payload import get_metadata_obj
from calm.dsl.config import get_context
from calm.dsl.store import Cache
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

        # Get project from metadata or context
        metadata_obj = get_metadata_obj()
        project_ref = metadata_obj.get("project_reference", {})
        context = get_context()
        project_config = context.get_project_config()
        project_name = project_ref.get("name", project_config["name"])

        env_uuid = cdict.get("environment", {}).get("uuid")
        env_name = cdict.get("environment", {}).get("name", env_uuid)

        if env_uuid:
            # ensure that the referenced environment is associated to the project this BP belongs to.
            env_cache_data = Cache.get_entity_data_using_uuid(
                entity_type="environment", uuid=env_uuid
            )
            env_project = env_cache_data.get("project")
            if env_project and project_name != env_project:
                LOG.error(
                    "Environment '{}' referenced by profile '{}' belongs to project '{}'. Use an environment from"
                    " project '{}'".format(
                        env_name, cdict.get("name", ""), env_project, project_name
                    )
                )
                sys.exit(-1)

            cdict["environment_reference_list"] = [env_uuid]

        # pop out unnecessary attibutes
        cdict.pop("environment", None)

        return cdict


class ProfileValidator(PropertyValidator, openapi_type="app_profile"):
    __default__ = None
    __kind__ = ProfileType


def profile(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return ProfileType(name, bases, kwargs)


Profile = profile()
