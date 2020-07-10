from .entity import EntityType, Entity
from .validator import PropertyValidator
from .endpoint import EndpointType


# Endpoint Payload


class EndpointPayloadType(EntityType):
    __schema_name__ = "EndpointPayload"
    __openapi_type__ = "endpoint_payload"


class EndpointPayloadValidator(PropertyValidator, openapi_type="endpoint_payload"):
    __default__ = None
    __kind__ = EndpointPayloadType


def _endpoint_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return EndpointPayloadType(name, bases, kwargs)


EndpointPayload = _endpoint_payload()


def create_endpoint_payload(UserEndpoint):

    err = {"error": "", "code": -1}

    if UserEndpoint is None:
        err["error"] = "Given endpoint is empty."
        return None, err

    if not isinstance(UserEndpoint, EndpointType):
        err["error"] = "Given endpoint is not of type Endpoint"
        return None, err

    spec = {
        "name": UserEndpoint.__name__,
        "description": UserEndpoint.__doc__ or "",
        "resources": UserEndpoint,
    }

    metadata = {"spec_version": 1, "kind": "endpoint", "name": UserEndpoint.__name__}

    UserEndpointPayload = _endpoint_payload()
    UserEndpointPayload.metadata = metadata
    UserEndpointPayload.spec = spec

    return UserEndpointPayload, None
