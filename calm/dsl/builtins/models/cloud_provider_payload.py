import uuid

from .entity import Entity, EntityType
from .validator import PropertyValidator
from calm.dsl.builtins.models.cloud_provider import CloudProvider
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


class CloudProviderPayloadType(EntityType):
    """Metaclass for user provider"""

    __schema_name__ = "CloudProviderPayload"
    __openapi_type__ = "cloud_provider_payload"


class CloudProviderPayloadValidator(
    PropertyValidator, openapi_type="cloud_provider_payload"
):
    __default__ = None
    __kind__ = CloudProviderPayloadType


def _cloud_provider_payload(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return CloudProviderPayloadType(name, bases, kwargs)


CloudProviderPayload = _cloud_provider_payload()


def create_cloud_provider_payload(CloudProviderClass):
    err = {"error": "", "code": -1}

    if CloudProviderClass is None:
        err["error"] = "Given provider is empty."
        return None, err

    if not isinstance(CloudProviderClass, type(CloudProvider)):
        err["error"] = "Given provider is not of type User Provider"
        LOG.info("Given provider is not of type User Provider")
        return None, err

    spec = {
        "name": CloudProviderClass.__name__,
        "resources": CloudProviderClass,
        "description": CloudProviderClass.__doc__ or "",
    }
    metadata = {
        "kind": "provider",
        "name": CloudProviderClass.__name__,
        "uuid": str(uuid.uuid4()),
    }

    CloudProviderPayloadClass = _cloud_provider_payload()
    CloudProviderPayloadClass.metadata = metadata
    CloudProviderPayloadClass.spec = spec

    return CloudProviderPayloadClass
