import enum
import uuid
import sys
from distutils.version import LooseVersion as LV

from .entity import EntityType, Entity, EntityTypeBase
from .validator import DictValidator, PropertyValidator
from .credential import CredentialType
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE
from calm.dsl.store import Version
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)

# Endpoint


class EndpointType(EntityType):
    __schema_name__ = "Endpoint"
    __openapi_type__ = "app_endpoint"

    def compile(cls):
        cdict = super().compile()
        if (cdict.get("provider_type", "")) == "":
            cdict.pop("provider_type", "")
        if (cdict.get("value_type", "")) == "":
            cdict.pop("value_type", "")

        CALM_VERSION = Version.get_version("Calm")
        if LV(CALM_VERSION) < LV("3.2.0"):
            value_type = cdict.pop("value_type")
            cdict["attrs"]["value_type"] = value_type

        else:
            value_type = cdict.get("value_type", "IP")
            if value_type == "VM":
                account = cdict["attrs"]["account_reference"]
                account_name = account["name"]
                account_data = Cache.get_entity_data(
                    entity_type=CACHE.ENTITY.ACCOUNT, name=account_name
                )
                if not account_data:
                    LOG.error("Account {} not found".format(account_name))
                    sys.exit(-1)

                provider_type = account_data["provider_type"]
                if provider_type not in ["nutanix_pc", "vmware"]:
                    LOG.error(
                        "Provider {} not supported for endpoints".format(provider_type)
                    )
                    sys.exit(-1)

                cdict["provider_type"] = provider_type.upper()

            tunnel = cdict.get("tunnel_reference", None)
            if tunnel is not None:
                if value_type not in ["IP", "HTTP"]:
                    LOG.error("Tunnel is supported only with IP and HTTP endpoints")
                    sys.exit(-1)
                cdict["tunnel_reference"] = tunnel.compile()
            else:
                cdict.pop("tunnel_reference")
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
    url,
    name=None,
    retries=0,
    retry_interval=10,
    timeout=120,
    verify=False,
    auth=None,
    tunnel=None,
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
    if tunnel is not None:
        kwargs["tunnel_reference"] = tunnel
    return _endpoint_create(**kwargs)


def _os_endpoint(
    value_type,
    value_list=[],
    vms=[],
    name=None,
    ep_type="Linux",
    port=22,
    connection_protocol=None,
    cred=None,
    subnet=None,
    filter=None,
    account=None,
    tunnel=None,
):
    kwargs = {
        "name": name,
        "type": ep_type,
        "value_type": value_type,
        "attrs": {"values": value_list, "port": port},
    }

    if value_type == "VM":
        if not account:
            LOG.error("Account is compulsory for vm endpoints")
            sys.exit(-1)

        # If filter string is given, filter type will be set to dynamic
        filter_type = "dynamic" if filter else "static"

        kwargs["attrs"]["vm_references"] = vms
        kwargs["attrs"]["subnet"] = subnet
        kwargs["attrs"]["filter_type"] = filter_type
        kwargs["attrs"]["account_reference"] = account
        if filter_type == "dynamic":
            kwargs["attrs"]["filter"] = filter

    if connection_protocol:
        kwargs["attrs"]["connection_protocol"] = connection_protocol
    if cred is not None and isinstance(cred, CredentialType):
        kwargs["attrs"]["credential_definition_list"] = [cred]
        kwargs["attrs"]["login_credential_reference"] = cred.get_ref()
    if tunnel:
        kwargs["tunnel_reference"] = tunnel

    return _endpoint_create(**kwargs)


def linux_endpoint_ip(
    value, name=None, port=22, os_type="Linux", cred=None, tunnel=None
):
    return _os_endpoint(
        "IP", value, ep_type="Linux", name=name, port=port, cred=cred, tunnel=tunnel
    )


def windows_endpoint_ip(
    value, name=None, connection_protocol="HTTP", port=None, cred=None, tunnel=None
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
        tunnel=tunnel,
    )


def linux_endpoint_vm(
    vms=[],
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
        filter=filter,
        port=port,
        subnet=subnet,
        cred=cred,
        account=account,
    )


def windows_endpoint_vm(
    vms=[],
    name=None,
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
        connection_protocol=connection_protocol,
        name=name,
        port=port,
        cred=cred,
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
