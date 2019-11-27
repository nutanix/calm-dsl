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
    name = kwargs.get("name") or getattr(EndpointType, "__schema_name__")
    bases = (Entity,)
    return EndpointType(name, bases, kwargs)


Endpoint = _endpoint()


def _endpoint_create(**kwargs):
    name = kwargs.get("name", kwargs.pop("__name__", None))
    if name is None:
        name = getattr(EndpointType, "__schema_name__") + "_" + str(uuid.uuid4())[:8]
        kwargs["name"] = name
    bases = (Endpoint,)
    return EndpointType(name, bases, kwargs)


def _http_endpoint(
        url, name=None, retries=0, retry_interval=10,
        timeout=120, verify=False, auth=None
):
    kwargs = {
        "name": name,
        "type": "HTTP",
        "attrs": {
            "url": url,
            "retry_count": retries + 1,
            "retry_interval": retry_interval,
            "connection_timeout": timeout,
            "tls_verify": verify,
        }
    }
    if auth:
        kwargs["attrs"]["authentication"] = auth
    else:
        kwargs["attrs"]["authentication"] = {"auth_type": "none"}
    return _endpoint_create(**kwargs)


def _exec_create(
        value_type, value, name=None, connection_type="SSH",
        port=22, os_type="Linux", cred=None
):
    kwargs = {
        "name": name,
        "type": "EXEC",
        "attrs": {
            "value": value,
            "value_type": value_type,
            "os_type": os_type,
            "port": port,
            "connection_type": connection_type,
        }
    }
    if cred is not None and isinstance(cred, CredentialType):
        kwargs["attrs"]["credential_definition_list"] = [cred]
        kwargs["attrs"]["login_credential_reference"] = cred.get_ref()
    return _endpoint_create(**kwargs)


def exec_endpoint_ip(
    value, name=None, connection_type="SSH", port=22, os_type="Linux", cred=None
):
    return _exec_create(
        "ip",
        value,
        name=name,
        connection_type=connection_type,
        port=port,
        os_type=os_type,
        cred=cred
    )


def exec_endpoint_vm(
    value, name=None, connection_type="SSH", port=22, os_type="Linux", cred=None
):
    return _exec_create(
        "vm",
        value,
        name=name,
        connection_type=connection_type,
        port=port,
        os_type=os_type,
        cred=cred
    )


class CalmEndpoint:
    def __new__(cls, name):
        kwargs = {
            "name": name,
            "attrs": {}
        }
        bases = (Endpoint,)
        return EndpointType(name, bases, kwargs)

    class Exec:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        ip = exec_endpoint_ip
        vm = exec_endpoint_vm

    class HTTP:
        def __new__(cls, *args, **kwargs):
            return _http_endpoint(*args, **kwargs)


class Auth:
    def __new__(cls, name):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    def Basic(username, password):
        secret = {"attrs": {"is_secret_modified": True}, "value": password}
        auth = {}
        auth["type"] = "basic"
        auth["username"] = username
        auth["password"] = secret
        return auth

    def BasicCred(cred):
        if not isinstance(cred, CredentialType):
            raise TypeError("{} should of type CredentialType".format(cred))

        auth = {}
        auth["type"] = "basic_with_cred"
        auth["credential_local_reference"] = cred.get_ref()
        return auth
