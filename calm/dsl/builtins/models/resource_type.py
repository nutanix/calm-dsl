import json
import sys

from calm.dsl.log import get_logging_handle
from calm.dsl.constants import RESOURCE_TYPE, ACTION

from .entity import EntityType, Entity
from .validator import PropertyValidator

LOG = get_logging_handle(__name__)


class ResourceTypeEntity(EntityType):
    __schema_name__ = "ResourceType"
    __openapi_type__ = "resource_type"

    def compile(cls):
        cdict = super().compile()
        cdict["type"] = RESOURCE_TYPE.TYPE.USER

        action_list = cdict["action_list"]
        for action in action_list:
            if action.type not in RESOURCE_TYPE.ACTION_TYPES:
                error = "ResourceType Action's type should be one of %s" % (
                    json.dumps(RESOURCE_TYPE.ACTION_TYPES)
                )
                LOG.error(error)
                sys.exit(error)

        icon_name = cdict.pop("icon_name", None)
        if icon_name:
            cdict["icon_name"] = icon_name
        icon_file = cdict.pop("icon_file", None)
        if icon_file:
            cdict["icon_file"] = icon_file

        resource_kind = cdict.pop("resource_kind", None)
        if resource_kind:
            cdict["tags"] = [resource_kind]
        return cdict

    @classmethod
    def pre_decompile(mcls, cdict, context, prefix=""):
        """Hook to modify cdict before decompile"""

        tags = cdict.pop("tags", [])
        if tags:
            cdict["resource_kind"] = tags[0]

        cdict["icon_name"] = cdict.pop("icon_reference", {}).get("name", "")
        return super(ResourceTypeEntity, mcls).pre_decompile(
            cdict, context, prefix=prefix
        )


class ResourceTypeValidator(PropertyValidator, openapi_type="resource_type"):
    __default__ = None
    __kind__ = ResourceTypeEntity


def _resource_type(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return ResourceTypeEntity(name, bases, kwargs)


ResourceType = _resource_type()
