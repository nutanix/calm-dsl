import sys
from copy import deepcopy

from distutils.version import LooseVersion as LV

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .utils import read_file
from calm.dsl.builtins import Ref
from calm.dsl.api.handle import get_api_client
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Version

LOG = get_logging_handle(__name__)


# Credential


class CredentialType(EntityType):
    __schema_name__ = "Credential"
    __openapi_type__ = "app_credential"

    def compile(cls):
        cdict = super().compile()
        cdict.pop("default", None)
        if cdict["type"] == "PASSWORD":
            cdict.pop("passphrase", None)
        return cdict


class CredentialValidator(PropertyValidator, openapi_type="app_credential"):
    __default__ = None
    __kind__ = CredentialType


def _credential(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return CredentialType(name, bases, kwargs)


Credential = _credential()


def basic_cred(
    username,
    password="",
    name="default",
    default=False,
    type="PASSWORD",
    filename=None,
    editables=dict(),
):

    if filename:
        password = read_file(filename, depth=2)

    secret = {"attrs": {"is_secret_modified": True}, "value": password}

    kwargs = {}
    kwargs["type"] = type
    kwargs["username"] = username
    kwargs["secret"] = secret
    kwargs["name"] = name
    kwargs["default"] = default
    if editables:
        kwargs["editables"] = editables

    return _credential(**kwargs)


def secret_cred(
    username,
    name="default",
    secret="default",
    type="PASSWORD",
    default=False,
    editables=dict(),
):

    # This secret value will be replaced when user is creatring a blueprint
    secret = {"attrs": {"is_secret_modified": True}, "value": "", "secret": secret}

    kwargs = {}
    kwargs["type"] = type
    kwargs["username"] = username
    kwargs["secret"] = secret
    kwargs["name"] = name
    kwargs["default"] = default
    if editables:
        kwargs["editables"] = editables

    return _credential(**kwargs)


def dynamic_cred(
    username,
    account,
    resource_type=None,
    variable_dict={},
    name="default",
    default=False,
    type="PASSWORD",
    editables=dict(),
):
    client = get_api_client()
    secret = {"attrs": {"is_secret_modified": True}, "value": "@@{secret}@@"}

    # Below line is required as account ref returns uuid in account ref dict
    # which is not required for dynamic cred cases

    kwargs = {}
    kwargs["type"] = type
    kwargs["username"] = username
    kwargs["secret"] = secret
    kwargs["name"] = name
    kwargs["default"] = default
    kwargs["cred_class"] = "dynamic"
    kwargs["account"] = account

    if not resource_type:
        resource_type = Ref.Resource_Type(account.name)

    if variable_dict:
        resource_type_uuid = resource_type.compile()["uuid"]
        res, err = client.resource_types.read(id=resource_type_uuid)
        if err:
            LOG.error(err)
            sys.exit(-1)

        resource_type_payload = res.json()

        cred_attr_list = (
            resource_type_payload.get("spec", {})
            .get("resources", {})
            .get("schema_list", {})
        )

        if not cred_attr_list:
            LOG.error("No Cred-Variables found in account")
            sys.exit(-1)

        variable_list = list()
        for cred_attr in cred_attr_list:
            cred_attr_copy = deepcopy(cred_attr)
            var_name = cred_attr["name"]
            if var_name in variable_dict:
                cred_attr_copy["value"] = variable_dict.pop(var_name)

            cred_attr_copy.pop("uuid", None)
            variable_list.append(cred_attr_copy)

        if variable_dict:
            LOG.error("Variables '{}' not found in account cred-attrs")
            sys.exit("Unknown variables found in credential")

        kwargs["variable_list"] = variable_list
        kwargs["resource_type"] = resource_type

    if editables:
        kwargs["editables"] = editables

    return _credential(**kwargs)
