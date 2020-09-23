import uuid

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .credential import CredentialType


# Endpoint


class EndpointType(EntityType):
    __schema_name__ = "Endpoint"
    __openapi_type__ = "app_endpoint"

    def __call__(*args, **kwargs):
        pass


class EndpointValidator(PropertyValidator, openapi_type="app_endpoint"):
    __default__ = None
    __kind__ = EndpointType


def _endpoint(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return EndpointType(name, bases, kwargs)


Endpoint = _endpoint()


def _endpoint_create(**kwargs):
    name = kwargs.get("name", kwargs.get("__name__", None))
    if name is None:
        name = getattr(EndpointType, "__schema_name__") + "_" + str(uuid.uuid4())[:8]
        kwargs["name"] = name
    bases = (Endpoint,)
    return EndpointType(name, bases, kwargs)


def _http_endpoint(
    url, name=None, retries=0, retry_interval=10, timeout=120, verify=False, auth=None
):
    kwargs = {
        "name": name,
        "type": "HTTP",
        "attrs": {
            "urls": [url],
            "retry_count": retries + 1,
            "retry_interval": retry_interval,
            "connection_timeout": timeout,
            "tls_verify": verify,
        },
    }
    if auth:
        kwargs["attrs"]["authentication"] = auth
    else:
        kwargs["attrs"]["authentication"] = {"auth_type": "none"}
    return _endpoint_create(**kwargs)


def _exec_create(
    value_type,
    ip_list,
    name=None,
    ep_type="Linux",
    port=22,
    connection_protocol=None,
    cred=None,
):
    kwargs = {
        "name": name,
        "type": ep_type,
        "attrs": {"values": ip_list, "value_type": value_type, "port": port},
    }
    if connection_protocol:
        kwargs["attrs"]["connection_protocol"] = connection_protocol
    if cred is not None and isinstance(cred, CredentialType):
        kwargs["attrs"]["credential_definition_list"] = [cred]
        kwargs["attrs"]["login_credential_reference"] = cred.get_ref()
    return _endpoint_create(**kwargs)


def linux_endpoint_ip(value, name=None, port=22, os_type="Linux", cred=None):
    return _exec_create("IP", value, ep_type="Linux", name=name, port=port, cred=cred)


def windows_endpoint_ip(
    value, name=None, connection_protocol="HTTP", port=None, cred=None
):
    connection_protocol = connection_protocol.lower()
    if connection_protocol not in ["http", "https"]:
        raise TypeError(
            "Connection Protocol ({}) should be HTTP/HTTPS".format(connection_protocol)
        )

    if port is None:
        if connection_protocol == "http":
            port = 5985
        else:
            port = 5986
    return _exec_create(
        "IP",
        value,
        ep_type="Windows",
        connection_protocol=connection_protocol,
        name=name,
        port=port,
        cred=cred,
    )


def _basic_auth(username, password):
    secret = {"attrs": {"is_secret_modified": True}, "value": password}
    auth = {}
    auth["type"] = "basic"
    auth["username"] = username
    auth["password"] = secret
    return auth


def existing_endpoint(name):
    kwargs = {"name": name, "attrs": {}}
    bases = (Endpoint,)
    return EndpointType(name, bases, kwargs)


class CalmEndpoint:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    use_existing = existing_endpoint

    class Linux:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        ip = linux_endpoint_ip

    class Windows:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        ip = windows_endpoint_ip

    class HTTP:
        def __new__(cls, *args, **kwargs):
            return _http_endpoint(*args, **kwargs)

    class Auth:
        def __new__(cls, *args, **kwargs):
            return _basic_auth(*args, **kwargs)
