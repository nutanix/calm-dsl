import enum
import uuid

from .entity import EntityType, Entity, EntityTypeBase
from .validator import DictValidator, PropertyValidator
from .credential import CredentialType


# Endpoint


class ENDPOINT_FILTER(enum.Enum):

    STATIC = 1
    DYNAMIC = 2


ENDPOINT_FILTER_MAP = {
    ENDPOINT_FILTER.STATIC: "static",
    ENDPOINT_FILTER.DYNAMIC: "dynamic",
}


class ENDPOINT_PROVIDER(enum.Enum):

    NUTANIX = 1
    VMWARE = 2


PROVIDER_TYPE_MAP = {
    ENDPOINT_PROVIDER.NUTANIX: "NUTANIX_PC",
    ENDPOINT_PROVIDER.VMWARE: "VMWARE",
}


class EndpointType(EntityType):
    __schema_name__ = "Endpoint"
    __openapi_type__ = "app_endpoint"

    def compile(cls):
        cdict = super().compile()
        if (cdict.get("provider_type", "")) == "":
            cdict.pop("provider_type", "")
        if (cdict.get("value_type", "")) == "":
            cdict.pop("value_type", "")
        return cdict

    def post_compile(cls, cdict):
        cdict = super().post_compile(cdict)

        # Setting the parent to attrs
        attrs = cdict.get("attrs", {})

        for _, v in attrs.items():
            if isinstance(v, list):
                for ve in v:
                    if issubclass(type(ve), EntityTypeBase):
                        ve.__parent__ = cls
            elif issubclass(type(v), EntityTypeBase):
                v.__parent__ = cls

        return cdict

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
        "value_type": "IP",
        "attrs": {
            "urls": [url] if isinstance(url, str) else url,
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


def _os_endpoint(
    value_type,
    value_list=[],
    vms=[],
    name=None,
    ep_type="Linux",
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
    port=22,
    connection_protocol=None,
    cred=None,
    filter_type=ENDPOINT_FILTER.STATIC,
    subnet=None,
    filter=None,
    account=None,
):
    kwargs = {
        "name": name,
        "type": ep_type,
        "value_type": value_type,
        "attrs": {"values": value_list, "port": port},
    }

    if value_type == "VM":
        kwargs["attrs"]["vm_references"] = vms
        kwargs["provider_type"] = PROVIDER_TYPE_MAP.get(provider_type, "NUTANIX_PC")
        kwargs["attrs"]["subnet"] = subnet
        kwargs["attrs"]["filter_type"] = ENDPOINT_FILTER_MAP.get(filter_type, "static")
        kwargs["attrs"]["account_reference"] = account
        if filter_type == ENDPOINT_FILTER.DYNAMIC:
            kwargs["attrs"]["filter"] = filter

    if connection_protocol:
        kwargs["attrs"]["connection_protocol"] = connection_protocol
    if cred is not None and isinstance(cred, CredentialType):
        kwargs["attrs"]["credential_definition_list"] = [cred]
        kwargs["attrs"]["login_credential_reference"] = cred.get_ref()
    return _endpoint_create(**kwargs)


def linux_endpoint_ip(value, name=None, port=22, os_type="Linux", cred=None):
    return _os_endpoint("IP", value, ep_type="Linux", name=name, port=port, cred=cred)


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
    return _os_endpoint(
        "IP",
        value,
        ep_type="Windows",
        connection_protocol=connection_protocol,
        name=name,
        port=port,
        cred=cred,
    )


def linux_endpoint_vm(
    vms=[],
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
    filter_type=ENDPOINT_FILTER.STATIC,
    filter=None,
    name=None,
    port=22,
    subnet="",
    cred=None,
    account=None,
):
    return _os_endpoint(
        "VM",
        [],
        vms=vms,
        name=name,
        ep_type="Linux",
        provider_type=provider_type,
        filter_type=filter_type,
        filter=filter,
        port=port,
        subnet=subnet,
        cred=cred,
        account=account,
    )


def windows_endpoint_vm(
    vms=[],
    name=None,
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
    filter_type=ENDPOINT_FILTER.STATIC,
    filter=None,
    connection_protocol="HTTP",
    port=None,
    cred=None,
    subnet="",
    account=None,
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
    return _os_endpoint(
        "VM",
        [],
        vms=vms,
        ep_type="Windows",
        provider_type=provider_type,
        connection_protocol=connection_protocol,
        name=name,
        port=port,
        cred=cred,
        filter_type=filter_type,
        filter=filter,
        subnet=subnet,
        account=account,
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
        vm = linux_endpoint_vm

    class Windows:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        ip = windows_endpoint_ip
        vm = windows_endpoint_vm

    class HTTP:
        def __new__(cls, *args, **kwargs):
            return _http_endpoint(*args, **kwargs)

    class Auth:
        def __new__(cls, *args, **kwargs):
            return _basic_auth(*args, **kwargs)
